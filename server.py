from flask import Flask, request, send_file, send_from_directory, jsonify
import os
from yt_dlp import YoutubeDL
import uuid

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/video-info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format')  # "video" o "audio"

    if not url or not format_type:
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        temp_id = str(uuid.uuid4())  # Genera un ID único para la descarga
        ydl_opts = {
            'outtmpl': f'{temp_id}.%(ext)s',
            'format': 'best' if format_type == "video" else 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if format_type == "audio" else [],
            'quiet': True,  # Silenciar la salida de yt_dlp
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            if format_type == 'audio':
                file_name = file_name.replace('.webm', '.mp3').replace('.m4a', '.mp3')  # Ajusta extensiones si es necesario

        return send_file(file_name, as_attachment=True, download_name=info['title'] + os.path.splitext(file_name)[1])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Limpia archivos temporales
        for temp_file in os.listdir('.'):
            if temp_file.startswith(temp_id):
                os.remove(temp_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)