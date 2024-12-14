const chatWindow = document.getElementById('chat-window');
const chatInput = document.querySelector('.chat-input');
const searchBtn = document.querySelector('.search-btn');

let currentMessageElement = null;
let currentThreadId = null;

function createLoadingAnimation() {
    const loadingBubble = document.createElement('div');
    loadingBubble.classList.add('chat-bubble', 'ai-bubble', 'loading-bubble');
    
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
    // Remove loading animation if it exists and this is the first content
    const loadingBubble = document.querySelector('.loading-bubble');
    if (loadingBubble) {
        loadingBubble.remove();
    }

    if (!currentMessageElement) {
        currentMessageElement = createAssistantMessage();
    }
    
    // Parse the content as markdown and append it
    const parsedContent = marked.parse(content);
    // Create a temporary div to hold the new content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = parsedContent;
    
    // Get the text content and append it to the current paragraph
    let currentParagraph = currentMessageElement.querySelector('p:last-child');
    if (!currentParagraph) {
        currentParagraph = document.createElement('p');
        currentMessageElement.appendChild(currentParagraph);
    }
    currentParagraph.textContent += tempDiv.textContent;
    
    // Highlight any code blocks
    currentMessageElement.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    
    chatWindow.scrollTop = chatWindow.scrollHeight;
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
        const fileLink = document.createElement('a');
        fileLink.classList.add('file-name');
        fileLink.href = '#';
        fileLink.textContent = file.file_name;
        fileLink.onclick = (e) => {
            e.preventDefault();
            if (file.quote) {
                const quoteDiv = document.createElement('div');
                quoteDiv.classList.add('file-citation');
                quoteDiv.textContent = file.quote;
                fileItem.appendChild(quoteDiv);
                fileLink.onclick = null;
            }
        };
        fileItem.appendChild(fileLink);
        fileList.appendChild(fileItem);
    });
    
    fileInfoDiv.appendChild(fileList);
    currentMessageElement.appendChild(fileInfoDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showError(message) {
    // Remove loading animation if it exists
    const loadingBubble = document.querySelector('.loading-bubble');
    if (loadingBubble) {
        loadingBubble.remove();
    }

    const errorBubble = document.createElement('div');
    errorBubble.classList.add('chat-bubble', 'ai-bubble', 'error');
    errorBubble.textContent = message || "Sorry, there was an error processing your request. Please try again.";
    chatWindow.appendChild(errorBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
    if (!message.trim()) return;
    
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
    
    // Clear input and prepare for new message
    chatInput.value = '';
    currentMessageElement = null;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                thread_id: currentThreadId 
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            
            // Keep the last line in the buffer if it's incomplete
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'content') {
                            appendContent(data.content);
                        } else if (data.type === 'file_search') {
                            appendFileSearchInfo(data.files);
                        } else if (data.type === 'error') {
                            showError(data.message);
                        } else if (data.type === 'done') {
                            // Store thread ID for conversation continuity
                            if (data.thread_id) {
                                currentThreadId = data.thread_id;
                            }
                            // Remove loading animation if it still exists
                            const remainingLoadingBubble = document.querySelector('.loading-bubble');
                            if (remainingLoadingBubble) {
                                remainingLoadingBubble.remove();
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

        // Process any remaining data in the buffer
        if (buffer.startsWith('data: ')) {
            try {
                const data = JSON.parse(buffer.slice(6));
                if (data.type === 'content') {
                    appendContent(data.content);
                } else if (data.type === 'file_search') {
                    appendFileSearchInfo(data.files);
                } else if (data.type === 'error') {
                    showError(data.message);
                } else if (data.type === 'done' && data.thread_id) {
                    currentThreadId = data.thread_id;
                }
            } catch (e) {
                console.error('Error parsing SSE data:', e);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to connect to the server. Please try again.');
    }
}

// Reset thread ID when page is refreshed
window.addEventListener('load', () => {
    currentThreadId = null;
});

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