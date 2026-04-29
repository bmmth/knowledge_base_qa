import os
import json
import hashlib
from typing import List, Dict, Any
from dataclasses import dataclass

try:
    from langchain_community.document_loaders import TextLoader, PDFLoader, Docx2txtLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.chains import ConversationalRetrievalChain
    from langchain_community.chat_models import ChatOpenAI
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

@dataclass
class Document:
    content: str
    metadata: Dict[str, Any]
    doc_id: str

class RAGEngine:
    def __init__(self, persist_directory: str = "vector_store"):
        self.persist_directory = persist_directory
        self.documents: List[Document] = []
        self.vectorstore = None
        self.chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )

        if LANGCHAIN_AVAILABLE:
            self.embeddings = OpenAIEmbeddings()
            self._init_vectorstore()
        else:
            self.embeddings = None

    def _init_vectorstore(self):
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            except Exception:
                self.vectorstore = None

    def _get_file_loader(self, filepath: str):
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.txt':
            return TextLoader(filepath, encoding='utf-8')
        elif ext == '.pdf':
            return PDFLoader(filepath)
        elif ext in ['.docx', '.doc']:
            return Docx2txtLoader(filepath)
        else:
            return TextLoader(filepath, encoding='utf-8')

    def _calculate_doc_id(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def _load_and_split_document(self, filepath: str) -> List[Document]:
        try:
            loader = self._get_file_loader(filepath)
            raw_docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
            )

            chunks = text_splitter.split_documents(raw_docs)

            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    content=chunk.page_content,
                    metadata={
                        "source": chunk.metadata.get("source", filepath),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    doc_id=self._calculate_doc_id(chunk.page_content)
                )
                documents.append(doc)

            return documents
        except Exception as e:
            print(f"Error loading document {filepath}: {e}")
            return []

    def _create_simple_vectorstore(self, documents: List[Document]):
        if not documents:
            return

        texts = [doc.content for doc in documents]
        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vectorstore.persist()

    def _build_chain(self):
        if not self.vectorstore:
            return

        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )

        self.chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.3, model_name="gpt-3.5-turbo"),
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": None}
        )

    def add_document(self, filepath: str) -> bool:
        if not LANGCHAIN_AVAILABLE:
            print("LangChain not available, using simple mode")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                doc = Document(
                    content=content[:5000],
                    metadata={"source": filepath},
                    doc_id=self._calculate_doc_id(content)
                )
                self.documents.append(doc)
            return True

        new_docs = self._load_and_split_document(filepath)

        if not new_docs:
            return False

        self.documents.extend(new_docs)

        if self.vectorstore is None:
            self._create_simple_vectorstore(new_docs)
        else:
            texts = [doc.content for doc in new_docs]
            self.vectorstore.add_texts(texts)
            self.vectorstore.persist()

        self._build_chain()
        return True

    def query(self, question: str) -> Dict[str, Any]:
        if not question.strip():
            return {"answer": "请输入问题", "sources": []}

        if not LANGCHAIN_AVAILABLE or self.chain is None:
            return self._simple_query(question)

        try:
            result = self.chain({"question": question})
            answer = result["answer"]

            source_docs = []
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    source_docs.append({
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "source": doc.metadata.get("source", "未知来源")
                    })

            return {
                "answer": answer,
                "sources": source_docs
            }
        except Exception as e:
            return self._simple_query(question)

    def _simple_query(self, question: str) -> Dict[str, Any]:
        if not self.documents:
            return {
                "answer": "知识库为空，请先上传文档",
                "sources": []
            }

        question_lower = question.lower()
        best_match = None
        best_score = 0

        for doc in self.documents:
            content_lower = doc.content.lower()

            words = question_lower.split()
            match_count = sum(1 for word in words if word in content_lower)

            if match_count > best_score:
                best_score = match_count
                best_match = doc

        if best_match:
            return {
                "answer": f"根据文档「{os.path.basename(best_match.metadata.get('source', '未知'))}」，相关信息如下：\n\n{best_match.content[:1000]}",
                "sources": [{
                    "content": best_match.content[:200] + "..." if len(best_match.content) > 200 else best_match.content,
                    "source": best_match.metadata.get("source", "未知来源")
                }]
            }

        return {
            "answer": "抱歉，知识库中没有找到与您问题相关的内容",
            "sources": []
        }

    def get_document_list(self) -> List[Dict[str, Any]]:
        sources = {}
        for doc in self.documents:
            source = doc.metadata.get("source", "未知")
            if source not in sources:
                sources[source] = {
                    "name": os.path.basename(source),
                    "path": source,
                    "chunks": 0
                }
            sources[source]["chunks"] += 1

        return list(sources.values())

    def rebuild_index(self) -> bool:
        try:
            self.documents = []
            self.memory.clear()

            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)

            self.vectorstore = None
            self.chain = None

            kb_path = "knowledge_base"
            if os.path.exists(kb_path):
                for filename in os.listdir(kb_path):
                    filepath = os.path.join(kb_path, filename)
                    if os.path.isfile(filepath):
                        self.add_document(filepath)

            return True
        except Exception as e:
            print(f"Error rebuilding index: {e}")
            return False
