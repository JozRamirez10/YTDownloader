const socket = io();
const fetchInfoBtn = document.getElementById('fetchInfoBtn');
const downloadBtn = document.getElementById('downloadBtn');
const youtubeUrl = document.getElementById('youtubeUrl');
const statusMessage = document.getElementById('statusMessage');
const videoInfo = document.getElementById('videoInfo');
const videoTitle = document.getElementById('videoTitle');
const videoThumbnail = document.getElementById('videoThumbnail');
const progressBarContainer = document.getElementById('progressBarContainer');
const progressBar = document.getElementById('progressBar');

fetchInfoBtn.addEventListener('click', async () => {
    
    downloadBtn.classList.add("d-none");
    videoInfo.classList.add("d-none");

    const url = youtubeUrl.value.trim();
    if (!url) {
        statusMessage.textContent = 'Por favor, ingrese una URL válida.';
        statusMessage.className = 'text-danger';
        return;
    }

    statusMessage.textContent = 'Obteniendo información del video...';
    statusMessage.className = 'text-info';

    try {
        const response = await fetch('/video-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        if (!response.ok) throw new Error('Error al obtener la información del video.');

        const data = await response.json();
        videoTitle.textContent = data.title;
        videoThumbnail.src = data.thumbnail;
        videoInfo.classList.remove('d-none');
        downloadBtn.classList.remove('d-none');
        statusMessage.textContent = '';
    } catch (err) {
        console.error(err);
        statusMessage.textContent = 'Error al obtener la información del video.';
        statusMessage.className = 'text-danger';
    }
});

downloadBtn.addEventListener('click', async () => {
    const url = youtubeUrl.value.trim();
    const format = document.getElementById('format').value;

    if (!url) {
        statusMessage.textContent = 'Por favor, ingrese una URL válida.';
        statusMessage.className = 'text-danger';
        return;
    }

    progressBar.style.width = 0 + '%';
    if(progressBar.classList.contains("bg-success"))
        progressBar.classList.remove("bg-success");

    statusMessage.textContent = 'Procesando archivo...';
    statusMessage.className = 'text-info';
    progressBarContainer.classList.remove('d-none');

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format }),
        });

        if (!response.ok) throw new Error('Error al descargar el archivo.');

        // Nombre original del archivo
        const contentDisposition = response.headers.get('Content-Disposition');
        const fileNameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
        const fileName = fileNameMatch ? fileNameMatch[1] : 'download';

        // Descarga del servidor al cliente
        const reader = response.body.getReader();
        const contentLength = +response.headers.get('Content-Length');
        let receivedLength = 0;

        if(progressBar.classList.contains("progress-bar-striped"))
            progressBar.classList.remove("progress-bar-striped");

        if(progressBar.classList.contains("progress-bar-animated"))
            progressBar.classList.remove("progress-bar-animated");

        // Progreso de descarga
        statusMessage.textContent = 'Descargando...';
        progressBar.classList.add("bg-success");
        let chunks = [];
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
            receivedLength += value.length;

            const progress = Math.round((receivedLength / contentLength) * 100);
            progressBar.style.width = progress + '%';
            progressBar.textContent = progress + '%';
        }

        // Descarga del archivo
        const blob = new Blob(chunks);
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = fileName;
        a.click();

        statusMessage.textContent = 'Descarga completada.';
        statusMessage.className = 'text-success';
        youtubeUrl.value = '';
        progressBarContainer.classList.add('d-none');
    } catch (err) {
        console.error(err);
        statusMessage.textContent = 'Error al procesar la descarga.';
        statusMessage.className = 'text-danger';
        progressBarContainer.classList.add('d-none');
    }
});

socket.on('progress', (data) => {
    if (data.progress) {
        progressBar.style.width = data.progress + '%';
        progressBar.textContent = data.progress + '%';
    }
    if(data.progress == 100 && document.getElementById('format').value == "audio"){
        statusMessage.textContent = "Procesando archivo de audio, por favor espere...";
        progressBar.classList.add("progress-bar-striped");
        progressBar.classList.add("progress-bar-animated");
    }
        
});

socket.on('error', (data) => {
    statusMessage.textContent = `Error: ${data.message}`;
});
