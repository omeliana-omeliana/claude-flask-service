from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import os
from docx import Document
import tempfile

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

@app.route('/', methods=['GET'])
def home():
    return "Claude article formatting service is running"

@app.route('/api/format', methods=['POST'])
def format_article():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    doc = Document(tmp_path)
    text = '\n'.join([p.text for p in doc.paragraphs])
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""You are a scientific article formatter.

Article content:
{text}

Tasks:
1. Identify the journal this should be formatted for (or suggest Nature as default)
2. Format it according to standard scientific journal guidelines
3. Fix structure: Title, Abstract, Introduction, Methods, Results, Discussion, References
4. Fix citations to proper format
5. Return ONLY the formatted article text."""
            }]
        )
        formatted = message.content[0].text
    except Exception as e:
        os.unlink(tmp_path)
        return jsonify({"error": str(e)}), 500

    os.unlink(tmp_path)
    return jsonify({'formatted_article': formatted})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)