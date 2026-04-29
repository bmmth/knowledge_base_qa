from flask import Flask, render_template, request, jsonify
from rag_core import RAGEngine
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

rag_engine = RAGEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query', '')

        if not query:
            return jsonify({'error': '问题不能为空'}), 400

        result = rag_engine.query(query)

        return jsonify({
            'answer': result['answer'],
            'sources': result['sources'],
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    try:
        docs = rag_engine.get_document_list()
        return jsonify({'documents': docs, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/documents', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        if file:
            filename = file.filename
            filepath = os.path.join('knowledge_base', filename)
            file.save(filepath)

            rag_engine.add_document(filepath)

            return jsonify({
                'message': f'文档 {filename} 上传成功',
                'status': 'success'
            })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/rebuild', methods=['POST'])
def rebuild_index():
    try:
        rag_engine.rebuild_index()
        return jsonify({'message': '索引重建成功', 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
