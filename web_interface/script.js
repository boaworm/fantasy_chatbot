// Fantasy Chatbot Web Interface

const API_BASE = 'http://localhost:8000/api';

// DOM Elements
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessages = document.getElementById('chat-messages');
const typingIndicator = document.getElementById('typing-indicator');
const universeSelect = document.getElementById('universe-select');

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

// Focus input on load
messageInput.focus();

// Fetch universes from API
async function fetchUniverses() {
    try {
        const response = await fetch(`${API_BASE}/universes`);
        const data = await response.json();

        if (response.ok && data.topics) {
            availableUniverses = data.topics;
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

// Enable/disable send button based on input
messageInput.addEventListener('input', () => {
    sendButton.disabled = !messageInput.value.trim();
});

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
fetchUniverses();
checkHealth();