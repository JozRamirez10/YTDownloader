from flask import Flask, request, send_file, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
from yt_dlp import YoutubeDL
import uuid
import re

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/video-info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    url = limpiar_url(url)
    
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
    url = limpiar_url(url)
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
            'progress_hooks': [lambda d: progress_hook(d, temp_id)],
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

def progress_hook(d, temp_id):
    if d['status'] == 'downloading':
        percent_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0.0').strip())
        try:
            percent = float(percent_str.replace('%', '').strip())
        except ValueError:
            percent = 0.0
        socketio.emit('progress', {'id': temp_id, 'progress': percent})
    elif d['status'] == 'finished':
        socketio.emit('progress', {'id': temp_id, 'progress': 100.0})

def emit_error(temp_id, error_message):
    socketio.emit('error', {'id': temp_id, 'message': error_message})

def limpiar_url(url):
    posicion_list = url.find("&list")
    # Si se encuentra '&list', corta la URL hasta antes de ese punto
    if posicion_list != -1:
        url = url[:posicion_list]
    return url

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
