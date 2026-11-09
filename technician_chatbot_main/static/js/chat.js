// Chat interface functionality
class TechnicianChatbot {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.statusMessage = document.getElementById('statusMessage');
        this.responseTime = document.getElementById('responseTime');
        this.currentChatLogId = null;
        
        this.initializeEventListeners();
        this.updateStatus('Ready', 'success');
    }
    
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key in message input
        this.messageInput.addEventListener('keypress', (e) => this.handleKeyPress(e));
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResize());
        
        // Focus on input when page loads
        this.messageInput.focus();
    }
    
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message) {
            this.showError('Please enter a message');
            return;
        }
        
        if (message.length > 1000) {
            this.showError('Message too long (max 1000 characters)');
            return;
        }
        
        // Disable input and show loading state
        this.setLoading(true);
        this.addUserMessage(message);
        this.messageInput.value = '';
        this.autoResize();
        
        // Show typing indicator
        const typingId = this.addTypingIndicator();
        
        const startTime = Date.now();
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const responseTime = (Date.now() - startTime) / 1000;
            this.updateResponseTime(responseTime);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (data.error) {
                this.addBotMessage(data.error, 'error');
                this.updateStatus('Error occurred', 'error');
            } else {
                this.addBotMessage(data.response, data.source, data);
                this.currentChatLogId = data.chat_log_id;
                this.updateStatus('Response received', 'success');
                
                // Show feedback option for successful responses
                if (data.chat_log_id) {
                    setTimeout(() => this.showFeedbackOption(data.chat_log_id), 2000);
                }
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator(typingId);
            this.addBotMessage(
                'Sorry, I encountered an error. Please try again or contact support if the problem persists.',
                'error'
            );
            this.updateStatus('Connection error', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex justify-end mb-4';
        messageDiv.innerHTML = `
            <div class="max-w-xs lg:max-w-md bg-blue-500 text-white rounded-lg px-4 py-2">
                <p class="text-sm">${this.escapeHtml(message)}</p>
                <div class="text-xs text-blue-100 mt-1 text-right">
                    ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addBotMessage(message, source = 'bot', metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3 mb-4 fade-in';
        
        const sourceIcon = this.getSourceIcon(source);
        const sourceColor = this.getSourceColor(source);
        const formattedMessage = this.formatBotMessage(message);
        
        messageDiv.innerHTML = `
            <div class="w-8 h-8 ${sourceColor} rounded-full flex items-center justify-center text-white text-sm">
                ${sourceIcon}
            </div>
            <div class="flex-1">
                <div class="bg-gray-100 rounded-lg p-4">
                    <div class="prose prose-sm max-w-none">
                        ${formattedMessage}
                    </div>
                    <div class="flex items-center justify-between mt-3 text-xs text-gray-500">
                        <div class="flex items-center space-x-3">
                            <span title="Response Source">
                                <i class="fas fa-tag mr-1"></i>${this.formatSource(source)}
                            </span>
                            ${metadata.confidence ? `
                                <span title="Confidence Score">
                                    <i class="fas fa-tachometer-alt mr-1"></i>${Math.round(metadata.confidence * 100)}%
                                </span>
                            ` : ''}
                            ${metadata.intent ? `
                                <span title="Detected Intent">
                                    <i class="fas fa-brain mr-1"></i>${metadata.intent}
                                </span>
                            ` : ''}
                        </div>
                        <span>${new Date().toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addTypingIndicator() {
        const typingId = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = typingId;
        typingDiv.className = 'flex items-start space-x-3 mb-4';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center text-white text-sm">
                🔧
            </div>
            <div class="flex-1">
                <div class="bg-gray-100 rounded-lg p-4">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot" style="animation-delay: 0.2s;"></div>
                        <div class="typing-dot" style="animation-delay: 0.4s;"></div>
                    </div>
                    <div class="text-xs text-gray-500 mt-2">Assistant is thinking...</div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        
        return typingId;
    }
    
    removeTypingIndicator(typingId) {
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    formatBotMessage(message) {
        // Convert line breaks to HTML
        let formatted = message.replace(/\n/g, '<br>');
        
        // Format lists
        formatted = formatted.replace(/^\*\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Wrap consecutive list items in ul tags
        formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul class="list-disc list-inside space-y-1 my-2">$1</ul>');
        
        // Format bold text
        formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Format code blocks
        formatted = formatted.replace(/``````/gs, '<pre class="bg-gray-200 rounded p-2 text-sm overflow-x-auto my-2"><code>$1</code></pre>');
        
        // Format inline code
        formatted = formatted.replace(/`(.+?)`/g, '<code class="bg-gray-200 px-1 rounded text-sm">$1</code>');
        
        // Format headers (simple approach)
        formatted = formatted.replace(/^### (.+)$/gm, '<h4 class="font-semibold text-gray-800 mt-3 mb-1">$1</h4>');
        formatted = formatted.replace(/^## (.+)$/gm, '<h3 class="font-semibold text-gray-800 text-lg mt-4 mb-2">$1</h3>');
        formatted = formatted.replace(/^# (.+)$/gm, '<h2 class="font-bold text-gray-900 text-xl mt-4 mb-2">$1</h2>');
        
        return formatted;
    }
    
    getSourceIcon(source) {
        switch (source) {
            case 'rule_based':
            case 'rule_based_fallback':
            case 'rule_based_default':
                return '📋';
            case 'llm':
                return '🤖';
            case 'error':
                return '❌';
            default:
                return '🔧';
        }
    }
    
    getSourceColor(source) {
        switch (source) {
            case 'rule_based':
            case 'rule_based_fallback':
            case 'rule_based_default':
                return 'bg-green-500';
            case 'llm':
                return 'bg-blue-500';
            case 'error':
                return 'bg-red-500';
            default:
                return 'bg-gray-500';
        }
    }
    
    formatSource(source) {
        switch (source) {
            case 'rule_based':
                return 'Rule Based';
            case 'rule_based_fallback':
                return 'Rule Based (Fallback)';
            case 'rule_based_default':
                return 'Rule Based (Default)';
            case 'llm':
                return 'AI Assistant';
            case 'error':
                return 'Error';
            default:
                return 'System';
        }
    }
    
    showFeedbackOption(chatLogId) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'flex justify-center mb-4';
        feedbackDiv.innerHTML = `
            <button onclick="openFeedbackModal('${chatLogId}')" 
                    class="text-sm text-blue-600 hover:text-blue-800 underline">
                <i class="fas fa-star mr-1"></i>Rate this response
            </button>
        `;
        
        this.chatMessages.appendChild(feedbackDiv);
        this.scrollToBottom();
    }
    
    clearChat() {
        // Keep only the initial greeting message
        const messages = this.chatMessages.children;
        for (let i = messages.length - 1; i >= 1; i--) {
            messages[i].remove();
        }
        
        this.updateStatus('Chat cleared', 'info');
        this.messageInput.focus();
    }
    
    sendExample(exampleText) {
        this.messageInput.value = exampleText;
        this.messageInput.focus();
        this.autoResize();
        this.sendMessage();
    }
    
    setLoading(loading) {
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;
        
        if (loading) {
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Sending...';
            this.updateStatus('Sending message...', 'processing');
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane mr-1"></i>Send';
        }
    }
    
    updateStatus(message, type) {
        if (!this.statusMessage) return;
        
        this.statusMessage.textContent = message;
        
        // Remove existing status classes
        this.statusMessage.className = this.statusMessage.className
            .replace(/text-(green|red|yellow|blue)-\d+/g, '');
        
        // Add new status class
        switch (type) {
            case 'success':
                this.statusMessage.classList.add('text-green-300');
                break;
            case 'error':
                this.statusMessage.classList.add('text-red-300');
                break;
            case 'processing':
                this.statusMessage.classList.add('text-yellow-300');
                break;
            default:
                this.statusMessage.classList.add('text-blue-200');
        }
        
        // Auto-clear status after 3 seconds
        setTimeout(() => {
            if (this.statusMessage.textContent === message) {
                this.statusMessage.textContent = '';
            }
        }, 3000);
    }
    
    updateResponseTime(seconds) {
        if (!this.responseTime) return;
        
        if (seconds < 1) {
            this.responseTime.textContent = `${Math.round(seconds * 1000)}ms`;
        } else {
            this.responseTime.textContent = `${seconds.toFixed(2)}s`;
        }
        
        // Auto-clear after 5 seconds
        setTimeout(() => {
            this.responseTime.textContent = '';
        }, 5000);
    }
    
    showError(message) {
        // Create temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded-md shadow-lg z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-red-600 hover:text-red-800">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Feedback functionality
class FeedbackManager {
    constructor() {
        this.currentChatLogId = null;
        this.selectedRating = 0;
        this.initializeFeedbackModal();
    }
    
    initializeFeedbackModal() {
        // Initialize star rating
        const stars = document.querySelectorAll('.star');
        stars.forEach((star, index) => {
            star.addEventListener('click', () => this.setRating(index + 1));
            star.addEventListener('mouseenter', () => this.highlightStars(index + 1));
            star.addEventListener('mouseleave', () => this.highlightStars(this.selectedRating));
        });
    }
    
    openModal(chatLogId) {
        this.currentChatLogId = chatLogId;
        this.selectedRating = 0;
        this.highlightStars(0);
        document.getElementById('feedbackComment').value = '';
        document.getElementById('feedbackModal').classList.remove('hidden');
    }
    
    closeModal() {
        document.getElementById('feedbackModal').classList.add('hidden');
        this.currentChatLogId = null;
        this.selectedRating = 0;
    }
    
    setRating(rating) {
        this.selectedRating = rating;
        this.highlightStars(rating);
    }
    
    highlightStars(count) {
        const stars = document.querySelectorAll('.star');
        stars.forEach((star, index) => {
            if (index < count) {
                star.classList.add('active');
                star.querySelector('i').className = 'fas fa-star';
            } else {
                star.classList.remove('active');
                star.querySelector('i').className = 'far fa-star';
            }
        });
    }
    
    async submitFeedback() {
        if (this.selectedRating === 0) {
            alert('Please select a rating');
            return;
        }
        
        if (!this.currentChatLogId) {
            alert('No chat log ID available');
            return;
        }
        
        const comment = document.getElementById('feedbackComment').value.trim();
        
        try {
            const response = await fetch('/api/chat/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    chat_log_id: this.currentChatLogId,
                    rating: this.selectedRating,
                    comment: comment
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccessMessage('Thank you for your feedback!');
                this.closeModal();
            } else {
                throw new Error(data.error || 'Failed to save feedback');
            }
            
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Failed to submit feedback. Please try again.');
        }
    }
    
    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-300 text-green-800 px-4 py-3 rounded-md shadow-lg z-50';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(successDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (successDiv.parentElement) {
                successDiv.remove();
            }
        }, 3000);
    }
}

// Initialize chat system when page loads
let chatbot, feedbackManager;

document.addEventListener('DOMContentLoaded', function() {
    chatbot = new TechnicianChatbot();
    feedbackManager = new FeedbackManager();
    
    console.log('Technician Support Chatbot initialized');
});

// Global functions for HTML onclick events
function sendMessage() {
    if (chatbot) {
        chatbot.sendMessage();
    }
}

function sendExample(exampleText) {
    if (chatbot) {
        chatbot.sendExample(exampleText);
    }
}

function clearChat() {
    if (chatbot) {
        chatbot.clearChat();
    }
}

function handleKeyPress(event) {
    if (chatbot) {
        chatbot.handleKeyPress(event);
    }
}

function openFeedbackModal(chatLogId) {
    if (feedbackManager) {
        feedbackManager.openModal(chatLogId);
    }
}

function closeFeedbackModal() {
    if (feedbackManager) {
        feedbackManager.closeModal();
    }
}

function submitFeedback() {
    if (feedbackManager) {
        feedbackManager.submitFeedback();
    }
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter to send message
    if (event.ctrlKey && event.key === 'Enter') {
        sendMessage();
    }
    
    // Escape to clear chat
    if (event.key === 'Escape') {
        clearChat();
    }
});

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TechnicianChatbot, FeedbackManager };
}
