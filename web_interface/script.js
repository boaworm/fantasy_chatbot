// Fantasy Chatbot Web Interface

// Get API base URL from query parameter or use default
const urlParams = new URLSearchParams(window.location.search);
let API_BASE = urlParams.get('api_url') || window.location.origin + '/api';
console.log('API_BASE:', API_BASE);
console.log('URL params:', urlParams.toString());

// DOM Elements
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const typingIndicator = document.getElementById('typing-indicator');
const universeSelect = document.getElementById('universe-select');
const startChatButton = document.getElementById('start-chat-button');
const newChatButton = document.getElementById('new-chat-button');
const selectionScreen = document.getElementById('universe-selection-screen');
const inputArea = document.querySelector('.input-area');
const paginationControls = document.getElementById('pagination-controls');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageIndicator = document.getElementById('page-indicator');

// Conversation state
let conversationId = null;
let isTyping = false;
let currentUniverse = null;
let availableUniverses = [];
let conversationHistory = [];
let currentPageIndex = 0;

// Initialize conversation setup
function initConversation() {
    conversationId = 'conv_' + Date.now();
    conversationHistory = [{
        role: 'bot',
        content: `Welcome to ${currentUniverse}! What would you like to ask?`
    }];
    currentPageIndex = 0;
    renderCurrentPage();
}

// Render the current page spread
function renderCurrentPage() {
    chatMessages.innerHTML = '';

    // Safety check
    if (conversationHistory.length === 0) return;

    // In our paginated flow, we show exactly ONE Q&A pair per "page flip" to ensure it fits the two-column spread.
    // The welcome message is stand-alone.
    const turn = conversationHistory[currentPageIndex];

    if (turn.role === 'bot' && currentPageIndex === 0) {
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    ${turn.content}
                </div>
            </div>
        `;
    } else {
        // Render user question
        const qDiv = document.createElement('div');
        qDiv.className = 'message user-message';
        qDiv.innerHTML = `<div class="message-content">${turn.question}</div>`;
        chatMessages.appendChild(qDiv);

        // Render bot answer
        const aDiv = document.createElement('div');
        aDiv.className = 'message bot-message';
        aDiv.innerHTML = `<div class="message-content">${turn.answer}</div>`;
        chatMessages.appendChild(aDiv);
    }

    // Update pagination controls
    pageIndicator.textContent = `Page ${currentPageIndex + 1} of ${conversationHistory.length}`;
    prevPageBtn.disabled = currentPageIndex === 0;
    nextPageBtn.disabled = currentPageIndex === conversationHistory.length - 1;
}

// Add message to chat array
function addTurn(question, answer) {
    conversationHistory.push({ question, answer });
    currentPageIndex = conversationHistory.length - 1;
    renderCurrentPage();
}

// Show typing indicator
function showTyping() {
    typingIndicator.style.display = 'block';
}

// Hide typing indicator
function hideTyping() {
    typingIndicator.style.display = 'none';
}

// Send message
async function sendMessage(message) {
    if (!message.trim() || isTyping) return;

    // Fast-transition to new page logic - immediately display user question while waiting for answer.
    conversationHistory.push({ question: message, answer: '...' });
    currentPageIndex = conversationHistory.length - 1;
    renderCurrentPage();

    messageInput.value = '';
    sendButton.disabled = true;

    // Initialize conversation if needed
    if (!conversationId) {
        initConversation();
    }

    // Show typing indicator
    showTyping();

    try {
        // Send to API
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                universe: currentUniverse,
                conversation_id: conversationId
            })
        });

        const data = await response.json();

        // Hide typing indicator
        hideTyping();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get response');
        }

        // Update the '...' with the real answer
        conversationHistory[currentPageIndex].answer = data.response;
        renderCurrentPage();

        // Update conversation ID if provided
        if (data.conversation_id) {
            conversationId = data.conversation_id;
        }

    } catch (error) {
        hideTyping();
        conversationHistory[currentPageIndex].answer = `Error: ${error.message}. Please try again.`;
        renderCurrentPage();
    }

    // Enable input
    sendButton.disabled = false;
    messageInput.focus();
}

// Event Listeners
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(messageInput.value);
});

// Enable/disable send button based on input
messageInput.addEventListener('input', () => {
    sendButton.disabled = !messageInput.value.trim();
});

// Start chat after universe selection
startChatButton.addEventListener('click', () => {
    if (currentUniverse) {
        selectionScreen.style.display = 'none';
        inputArea.style.display = 'block';
        paginationControls.style.display = 'flex';
        newChatButton.style.display = 'inline-block';
        document.body.classList.add('chat-active');
        initConversation();
        messageInput.focus();
    }
});

// Pagination Controls
prevPageBtn.addEventListener('click', () => {
    if (currentPageIndex > 0) {
        currentPageIndex--;
        renderCurrentPage();
    }
});

nextPageBtn.addEventListener('click', () => {
    if (currentPageIndex < conversationHistory.length - 1) {
        currentPageIndex++;
        renderCurrentPage();
    }
});

// New Chat button
newChatButton.addEventListener('click', () => {
    currentUniverse = null;
    conversationId = null;
    conversationHistory = [];
    currentPageIndex = 0;
    universeSelect.value = '';

    // Hide chat UI & Reset
    inputArea.style.display = 'none';
    paginationControls.style.display = 'none';
    newChatButton.style.display = 'none';
    document.body.classList.remove('chat-active');
    chatMessages.innerHTML = '';

    // Show Selection Screen
    selectionScreen.style.display = 'block';
    startChatButton.disabled = true;
});

// Focus input on load
messageInput.focus();

// Fetch universes from API
async function fetchUniverses() {
    console.log('Fetching universes from:', `${API_BASE}/universes`);
    try {
        const response = await fetch(`${API_BASE}/universes`);
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok && data.topics) {
            availableUniverses = data.topics;
            console.log('Available universes:', availableUniverses);
            populateUniverseDropdown(availableUniverses);
        } else {
            console.error('Failed to fetch universes:', data);
        }
    } catch (error) {
        console.error('Error fetching universes:', error);
    }
}

// Populate universe dropdown
function populateUniverseDropdown(universes) {
    // Clear existing options except the first one
    while (universeSelect.options.length > 1) {
        universeSelect.remove(1);
    }

    // Add each universe as an option
    universes.forEach(universe => {
        const option = document.createElement('option');
        option.value = universe;
        option.textContent = universe;
        universeSelect.appendChild(option);
    });

    // Enable the select element
    universeSelect.disabled = false;

    // Update footer with universe list
    updateFooter(universes);
}

// Update footer with universe list
function updateFooter(universes) {
    const footerElement = document.getElementById('footer-universes');
    if (footerElement && universes.length > 0) {
        footerElement.textContent = `Available universes: ${universes.join(', ')}`;
    }
}

// Handle universe selection change
universeSelect.addEventListener('change', (e) => {
    currentUniverse = e.target.value;
    startChatButton.disabled = !currentUniverse;
    messageInput.placeholder = `Ask about ${currentUniverse || 'your selected universe'}...`;
});

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'degraded') {
            console.warn('LLM server may not be running. Please start LM Studio.');
        }
    } catch (error) {
        console.warn('Could not connect to API server. Make sure the server is running.');
    }
}

// Initialize
inputArea.style.display = 'none';

fetchUniverses();
checkHealth();