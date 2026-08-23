async function uploadPDF() {
    const fileInput = document.getElementById('pdfFile');
    const statusDiv = document.getElementById('uploadStatus');
    console.log('click')
    if (!fileInput.files[0]) {
        alert('يرجى اختيار ملف PDF أولاً');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    statusDiv.style.color = '#38bdf8';
    statusDiv.innerText = '⏳ جاري تجهيز الملف ...';
    try {
        const res = await fetch('/api/v1/upload-pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (res.ok) {
            statusDiv.style.color = '#4ade80';
            statusDiv.innerText = '✅ ' + data.message;
        } else {
            statusDiv.style.color = '#f87171';
            statusDiv.innerText = '❌ ' + (data.detail || 'حدث خطأ أثناء الرفع');
        }
    } catch (err) {
        statusDiv.style.color = '#f87171';
        statusDiv.innerText = '❌ فشل الاتصال بالسيرفر';
    }
}
const input = document.getElementById('queryInput');

function sendQuery() {
    const chatBox = document.getElementById('chatBox');
    const prompt = input.value.trim();

    if (!prompt) return;

    chatBox.innerHTML = ''; // تنظيف الشاشة

    const eventSource = new EventSource(`/api/v1/chat/stream?prompt=${encodeURIComponent(prompt)}`);
    let answerContainer = null;

    eventSource.onmessage = (event) => {
        input.value = ''
        const data = JSON.parse(event.data);

        if (data.type === 'thought') {
            const thoughtDiv = document.createElement('div');
            thoughtDiv.className = 'thought-step';
            thoughtDiv.innerText = data.content;
            chatBox.appendChild(thoughtDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        } 
        else if (data.type === 'answer') {
            if (!answerContainer) {
                answerContainer = document.createElement('div');
                answerContainer.className = 'answer-text';
                chatBox.appendChild(answerContainer);
            }
            answerContainer.innerText += data.content;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        else if (data.type === 'error') {
            const errorDiv = document.createElement('div');
            errorDiv.style.color = '#f87171';
            errorDiv.innerText = '❌ ' + data.content;
            chatBox.appendChild(errorDiv);
            eventSource.close();
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
    };
}

window.addEventListener('keypress',(event)=>{
    if(event.key == 'Enter' && input.value.trim()){
        sendQuery()
    }
})