import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from openai import OpenAI
from pydub import AudioSegment

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEXT_FOLDER'] = 'texts'
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEXT_FOLDER'], exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Templates
TEMPLATES = {
    "Basic Transcription": "Transcreva o áudio para texto em português.",
    "Pathology Macroscopy": (
        "Transcreva o texto com a seguinte formatação e tome atenção que será falado por um utilizador galego a tentar falar portugês: "
        "1. Coloque o número do exame e o nome do paciente no topo, separados por parágrafo. Quando se diz traço é - "
        "2. Organize o restante das informações em tópicos resumidos e separados por pontos. "
        "3. Não é necessário transcrever pontuação, como ponto, vírgula, etc. "
        "4. As medidas, quando ditas em centímetros ou milímetros, devem ser transcritas na versão reduzida (por exemplo, cm ou mm, respectivamente). "
        "5. Preste atenção a palavras-chave como serosa, gânglios, linfáticos, linfático, amarelo, lobulado, acastanhado, que dista, constrituído, colectomia, ulceroinfiltrativa, frasco referenciado como, fragmentos, fragmento, esbranquiçados. "
        "6. Ao transcrever palavras com acentos, remova os acentos e transcreva a palavra de acordo com a ortografia padrão da língua portuguesa."
    )
}

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def transcribe_audio(file_path, template):
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=template,
                language="pt"
            )
        return transcript.text
    except Exception as e:
        logging.error(f"Error transcribing audio file {file_path}: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        audio_files = os.listdir(app.config['UPLOAD_FOLDER'])
        text_files = os.listdir(app.config['TEXT_FOLDER'])
        return render_template('index.html', audio_files=audio_files, text_files=text_files, templates=TEMPLATES)
    except Exception as e:
        logging.error(f"Error rendering index page: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            logging.info(f"File {filename} uploaded successfully")
            return jsonify({"message": f"File {filename} uploaded successfully"}), 200
        except Exception as e:
            logging.error(f"Error uploading file {file.filename}: {str(e)}")
            return jsonify({"error": "Error uploading file"}), 500
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/transcribe', methods=['POST'])
def transcribe():
    template_key = request.json.get('template', 'Basic Transcription')
    template = TEMPLATES.get(template_key, TEMPLATES['Basic Transcription'])
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            text = transcribe_audio(file_path, template)
            text_filename = os.path.splitext(filename)[0] + '.txt'
            text_path = os.path.join(app.config['TEXT_FOLDER'], text_filename)
            with open(text_path, 'w') as f:
                f.write(text)
        logging.info("Transcription completed successfully")
        return jsonify({"message": "Transcription complete"}), 200
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return jsonify({"error": "Error during transcription"}), 500

@app.route('/combine', methods=['POST'])
def combine_texts():
    try:
        combined_text = ""
        for filename in os.listdir(app.config['TEXT_FOLDER']):
            file_path = os.path.join(app.config['TEXT_FOLDER'], filename)
            with open(file_path, 'r') as f:
                combined_text += f.read() + "\n\n"
        combined_file_path = os.path.join(app.config['TEXT_FOLDER'], 'combined.txt')
        with open(combined_file_path, 'w') as f:
            f.write(combined_text)
        logging.info("Texts combined successfully")
        return jsonify({"message": "Texts combined successfully"}), 200
    except Exception as e:
        logging.error(f"Error combining texts: {str(e)}")
        return jsonify({"error": "Error combining texts"}), 500

@app.route('/delete-multiple/<folder>', methods=['POST'])
def delete_multiple_files(folder):
    files = request.json.get('files', [])
    folder_path = app.config['UPLOAD_FOLDER'] if folder == 'audio' else app.config['TEXT_FOLDER']
    deleted_files = []
    try:
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(filename)
        logging.info(f"Deleted {len(deleted_files)} files: {', '.join(deleted_files)}")
        return jsonify({"message": f"Deleted {len(deleted_files)} files: {', '.join(deleted_files)}"}), 200
    except Exception as e:
        logging.error(f"Error deleting files: {str(e)}")
        return jsonify({"error": "Error deleting files"}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['TEXT_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error downloading file {filename}: {str(e)}")
        return jsonify({"error": "Error downloading file"}), 500

@app.route('/get_templates', methods=['GET'])
def get_templates():
    return jsonify(TEMPLATES)

@app.route('/add_template', methods=['POST'])
def add_template():
    name = request.json.get('name')
    content = request.json.get('content')
    if name and content:
        TEMPLATES[name] = content
        logging.info(f"Template '{name}' added successfully")
        return jsonify({"message": "Template added successfully"}), 200
    return jsonify({"error": "Invalid template data"}), 400

@app.route('/update_template', methods=['POST'])
def update_template():
    name = request.json.get('name')
    content = request.json.get('content')
    if name in TEMPLATES and content:
        TEMPLATES[name] = content
        logging.info(f"Template '{name}' updated successfully")
        return jsonify({"message": "Template updated successfully"}), 200
    return jsonify({"error": "Template not found or invalid data"}), 400

@app.route('/delete_template', methods=['POST'])
def delete_template():
    name = request.json.get('name')
    if name in TEMPLATES and name != "Basic Transcription":
        del TEMPLATES[name]
        logging.info(f"Template '{name}' deleted successfully")
        return jsonify({"message": "Template deleted successfully"}), 200
    return jsonify({"error": "Template not found or cannot be deleted"}), 400

@app.route('/get_template_content', methods=['POST'])
def get_template_content():
    name = request.json.get('name')
    if name in TEMPLATES:
        return jsonify({"content": TEMPLATES[name]}), 200
    return jsonify({"error": "Template not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)