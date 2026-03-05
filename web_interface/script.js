// Fantasy Chatbot Web Interface

// Get API base URL from query parameter or use default
const urlParams = new URLSearchParams(window.location.search);
const API_BASE = urlParams.get('api_url') || 'http://localhost:8000/api';
console.log('API_BASE:', API_BASE);
console.log('URL params:', urlParams.toString());

// DOM Elements
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const typingIndicator = document.getElementById('typing-indicator');
const universeSelect = document.getElementById('universe-select');
const apiUrlInput = document.getElementById('api-url-input');
const saveApiUrlButton = document.getElementById('save-api-url');

// Conversation state
let conversationId = null;
let isTyping = false;
let currentUniverse = null;
let availableUniverses = [];

// Initialize conversation
function initConversation() {
    conversationId = 'conv_' + Date.now();
}

// Add message to chat
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTyping() {
    typingIndicator.style.display = 'block';
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide typing indicator
function hideTyping() {
    typingIndicator.style.display = 'none';
}

// Send message
async function sendMessage(message) {
    if (!message.trim() || isTyping) return;

    // Add user message
    addMessage(message, true);
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

        // Add bot response
        addMessage(data.response, false);

        // Update conversation ID if provided
        if (data.conversation_id) {
            conversationId = data.conversation_id;
        }

    } catch (error) {
        hideTyping();
        addMessage(`Error: ${error.message}. Please try again.`, false);
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

// Save API URL button
saveApiUrlButton.addEventListener('click', () => {
    const newApiUrl = apiUrlInput.value.trim();
    if (newApiUrl) {
        // Update API_BASE
        API_BASE = newApiUrl + '/api';
        // Update URL without reloading
        const url = new URL(window.location);
        url.searchParams.set('api_url', API_BASE);
        window.history.pushState({}, '', url);
        // Re-fetch universes
        fetchUniverses();
    }
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
// Set the API URL input field value
apiUrlInput.value = API_BASE.replace('/api', '');
// Reconstruct API_BASE without /api suffix for the input
API_BASE = API_BASE.replace('/api', '');

fetchUniverses();
checkHealth();