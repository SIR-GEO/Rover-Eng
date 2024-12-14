const chatWindow = document.getElementById('chat-window');
const chatInput = document.querySelector('.chat-input');
const searchBtn = document.querySelector('.search-btn');

// WebSocket setup
let socket = null;
let currentMessageContent = '';
let currentMessageElement = null;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    socket.onclose = function() {
        console.log('WebSocket connection closed');
        setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'stream_start') {
        const existingLoading = document.querySelector('.loading-bubble');
        if (existingLoading) {
            existingLoading.remove();
        }
        currentMessageContent = '';
        currentMessageElement = createAssistantMessage();
    } else if (data.type === 'stream_content') {
        appendContent(data.content);
    } else if (data.type === 'file_search_info') {
        appendFileSearchInfo(data.files);
    } else if (data.type === 'stream_end') {
        finishMessage();
    } else if (data.type === 'error') {
        showError(data.message);
    }
}

function createAssistantMessage() {
    const assistantBubble = document.createElement('div');
    assistantBubble.classList.add('chat-bubble', 'ai-bubble');
    
    const aiLabel = document.createElement('span');
    aiLabel.classList.add('chat-label');
    aiLabel.textContent = "Classic Rover Engineer:";
    assistantBubble.appendChild(aiLabel);
    
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    assistantBubble.appendChild(messageContent);
    
    chatWindow.appendChild(assistantBubble);
    return messageContent;
}

function appendContent(content) {
    if (!currentMessageElement) return;
    
    currentMessageContent += content;
    // Parse the accumulated content as markdown
    currentMessageElement.innerHTML = marked.parse(currentMessageContent);
    
    // Highlight any code blocks
    currentMessageElement.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function finishMessage() {
    if (!currentMessageElement) return;
    
    // Final markdown parsing and highlighting
    currentMessageElement.innerHTML = marked.parse(currentMessageContent);
    currentMessageElement.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
    chatWindow.scrollTop = chatWindow.scrollHeight;
    currentMessageElement = null;
    currentMessageContent = '';
}

function createLoadingAnimation() {
    const loadingBubble = document.createElement('div');
    loadingBubble.classList.add('chat-bubble', 'loading-bubble');
    
    const loadingDots = document.createElement('div');
    loadingDots.classList.add('loading-dots');
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        loadingDots.appendChild(dot);
    }
    
    loadingBubble.appendChild(loadingDots);
    return loadingBubble;
}

function showError(message) {
    const errorBubble = document.createElement('div');
    errorBubble.classList.add('chat-bubble', 'ai-bubble', 'error');
    errorBubble.textContent = message || "Sorry, there was an error processing your request. Please try again.";
    chatWindow.appendChild(errorBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function sendMessage(message) {
    if (!message.trim()) return;
    
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        showError("Connection lost. Reconnecting...");
        connectWebSocket();
        return;
    }
    
    // Display user message
    chatWindow.style.display = 'block';
    const userBubble = document.createElement('div');
    userBubble.classList.add('chat-bubble', 'user-bubble');
    
    const userLabel = document.createElement('span');
    userLabel.classList.add('user-label');
    userLabel.textContent = "You:";
    userBubble.appendChild(userLabel);
    
    const userText = document.createElement('div');
    userText.classList.add('message-content');
    userText.textContent = message;
    userBubble.appendChild(userText);
    chatWindow.appendChild(userBubble);
    
    // Add loading animation
    const loadingBubble = createLoadingAnimation();
    chatWindow.appendChild(loadingBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // Clear input
    chatInput.value = '';
    
    // Send message through WebSocket
    socket.send(message);
}

function appendFileSearchInfo(files) {
    if (!files || files.length === 0) return;
    
    const fileInfoDiv = document.createElement('div');
    fileInfoDiv.classList.add('file-search-info');
    
    const fileInfoHeader = document.createElement('div');
    fileInfoHeader.classList.add('file-search-header');
    fileInfoHeader.innerHTML = '<i class="fas fa-search"></i> Files referenced:';
    fileInfoDiv.appendChild(fileInfoHeader);
    
    const fileList = document.createElement('ul');
    fileList.classList.add('file-list');
    
    files.forEach(file => {
        const fileItem = document.createElement('li');
        fileItem.innerHTML = `<span class="file-name">${file.file_name}</span>`;
        if (file.file_citation) {
            fileItem.innerHTML += `<span class="file-citation">${file.file_citation}</span>`;
        }
        fileList.appendChild(fileItem);
    });
    
    fileInfoDiv.appendChild(fileList);
    
    if (currentMessageElement) {
        currentMessageElement.appendChild(fileInfoDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}

// Event Listeners
searchBtn.addEventListener('click', () => {
    sendMessage(chatInput.value);
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(chatInput.value);
    }
});

chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = chatInput.scrollHeight + 'px';
});

// Initialize WebSocket connection
connectWebSocket(); 