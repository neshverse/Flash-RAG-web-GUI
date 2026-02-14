// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentPage = 'chat';
let chatHistory = [];
let isProcessing = false;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const loadingOverlay = document.getElementById('loading-overlay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChat();
    initUpload();
    initSettings();
    loadStats();
    checkHealth();
});

// Navigation
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            switchPage(page);
            
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`${page}-page`).classList.add('active');
    currentPage = page;
}

// Chat Functionality
function initChat() {
    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
    });

    // Send on Enter (Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // Example buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.textContent.replace(/"/g, '');
            sendMessage();
        });
    });

    // New chat
    document.getElementById('new-chat-btn').addEventListener('click', () => {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">⚡</div>
                <h2>Welcome to Flash Financial RAG</h2>
                <p>Upload your sales data and ask questions like:</p>
                <div class="example-queries">
                    <button class="example-btn">"What were Q1 sales?"</button>
                    <button class="example-btn">"Compare Branch A vs B"</button>
                    <button class="example-btn">"Top 5 products by revenue"</button>
                </div>
            </div>
        `;
        chatHistory = [];
        reinitExampleButtons();
    });
}

function reinitExampleButtons() {
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.textContent.replace(/"/g, '');
            sendMessage();
        });
    });
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;

    // Clear welcome message if first message
    if (chatMessages.querySelector('.welcome-message')) {
        chatMessages.innerHTML = '';
    }

    // Add user message
    addMessage('user', message);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Show loading
    isProcessing = true;
    showLoading(true);
    updateStatus('Thinking...');

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: message,
                top_k: parseInt(document.getElementById('top-k')?.value || 5),
                temperature: parseFloat(document.getElementById('temperature')?.value || 0.7)
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            addMessage('assistant', data.response, data.sources);
            updateStats(data.processing_time);
        } else {
            addMessage('assistant', `Error: ${data.detail || 'Something went wrong'}`);
        }
    } catch (error) {
        addMessage('assistant', `Connection error: ${error.message}. Is the backend running?`);
    } finally {
        isProcessing = false;
        showLoading(false);
        updateStatus('Ready');
    }
}

function addMessage(role, content, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '⚡';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(content);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = `<i class="fas fa-database"></i> Based on ${sources.length} sources`;
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
    // Simple markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// Upload Functionality
function initUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });
}

async function handleFile(file) {
    const progressDiv = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload/csv`, {
            method: 'POST',
            body: formData
        });

        progressFill.style.width = '100%';

        const data = await response.json();

        if (response.ok) {
            progressText.textContent = `✅ Uploaded! ${data.rows_processed} rows processed`;
            addUploadToHistory(file.name, data.rows_processed);
            loadStats();
        } else {
            progressText.textContent = `❌ Error: ${data.detail}`;
        }
    } catch (error) {
        progressText.textContent = `❌ Error: ${error.message}`;
    }

    setTimeout(() => {
        progressDiv.style.display = 'none';
    }, 3000);
}

function addUploadToHistory(filename, rows) {
    const list = document.getElementById('upload-list');
    const item = document.createElement('div');
    item.className = 'upload-item';
    item.innerHTML = `
        <i class="fas fa-file-csv"></i>
        <span>${filename}</span>
        <span class="rows">${rows} rows</span>
    `;
    list.insertBefore(item, list.firstChild);
}

// Settings
function initSettings() {
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    
    if (tempSlider) {
        tempSlider.addEventListener('input', () => {
            tempValue.textContent = tempSlider.value;
        });
    }
}

// Stats & Health
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.vector_store) {
            document.getElementById('doc-count').textContent = data.vector_store.total_documents;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        const statusEl = document.getElementById('model-status');
        if (data.model_loaded) {
            statusEl.style.color = 'var(--success)';
            statusEl.textContent = '●';
        } else {
            statusEl.style.color = 'var(--error)';
            statusEl.textContent = '●';
        }
    } catch (error) {
        document.getElementById('model-status').style.color = 'var(--error)';
    }
}

function updateStats(responseTime) {
    // Update average response time
    const avgEl = document.getElementById('avg-response-time');
    const currentAvg = parseInt(avgEl.textContent) || 0;
    const newAvg = currentAvg ? Math.round((currentAvg + responseTime * 1000) / 2) : Math.round(responseTime * 1000);
    avgEl.textContent = newAvg + 'ms';
    
    // Update total queries
    const totalEl = document.getElementById('total-queries');
    totalEl.textContent = parseInt(totalEl.textContent) + 1;
}

function updateStatus(text) {
    const statusEl = document.getElementById('status-text');
    if (statusEl) statusEl.textContent = text;
}

function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Reset button
document.getElementById('reset-btn')?.addEventListener('click', async () => {
    if (!confirm('Clear all data? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/reset`, { method: 'POST' });
        if (response.ok) {
            alert('Database reset successfully');
            loadStats();
        }
    } catch (error) {
        alert('Failed to reset: ' + error.message);
    }
});

// Updated display function for strict mode
function displayStrictResponse(data) {
    const confidenceColors = {
        'high': '#10b981',
        'medium': '#f59e0b', 
        'low': '#ef4444',
        'none': '#ef4444'
    };
    
    const confidenceIcons = {
        'high': '✓',
        'medium': '⚠',
        'low': '✗',
        'none': '✗'
    };
    
    let html = '<div class="strict-response">';
    
    // Confidence badge
    html += `
        <div class="confidence-badge" style="background: ${confidenceColors[data.confidence]}20; color: ${confidenceColors[data.confidence]}; border: 1px solid ${confidenceColors[data.confidence]}">
            <span class="confidence-icon">${confidenceIcons[data.confidence]}</span>
            <span>${data.confidence.toUpperCase()} CONFIDENCE</span>
        </div>
    `;
    
    // Warning if present
    if (data.warning) {
        html += `
            <div class="warning-banner">
                <i class="fas fa-exclamation-triangle"></i>
                ${data.warning}
            </div>
        `;
    }
    
    // Answer box
    const isInsufficient = !data.found_in_evidence || data.answer.includes('INSUFFICIENT');
    
    html += `<div class="answer-container ${isInsufficient ? 'insufficient' : ''}">`;
    
    if (isInsufficient) {
        html += `
            <div class="insufficient-data">
                <i class="fas fa-database"></i>
                <h4>Data Not Found</h4>
                <p>${data.answer.replace('INSUFFICIENT_DATA:', '')}</p>
                <small>The system could not find this information in your uploaded data.</small>
            </div>
        `;
    } else {
        html += `<div class="answer-text">${formatAnswer(data.answer)}</div>`;
        
        // Raw values table
        if (Object.keys(data.raw_values).length > 0) {
            html += `
                <div class="raw-values">
                    <h5>Extracted Values</h5>
                    <table>
                        ${Object.entries(data.raw_values).map(([k, v]) => `
                            <tr><td>${k}</td><td><strong>${v}</strong></td></tr>
                        `).join('')}
                    </table>
                </div>
            `;
        }
        
        // Citations
        if (data.citations && data.citations.length > 0) {
            html += `
                <div class="citations-section">
                    <h5><i class="fas fa-link"></i> Sources (${data.citations.length})</h5>
                    <div class="citation-list">
                        ${data.source_data.map((src, i) => `
                            <div class="citation-item">
                                <span class="cite-num">[${data.citations[i]}]</span>
                                <div class="cite-content">
                                    ${Object.entries(src).map(([k, v]) => `
                                        <span class="cite-field"><strong>${k}:</strong> ${v}</span>
                                    `).join(' ')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Verification stats
        if (data.verification) {
            html += `
                <div class="verification-stats">
                    <span>Claims: ${data.verification.verified} verified</span>
                    ${data.verification.unverified > 0 ? `<span class="unverified">${data.verification.unverified} unverified</span>` : ''}
                </div>
            `;
        }
    }
    
    html += '</div>'; // Close answer-container
    
    // Metadata footer
    html += `
        <div class="response-meta">
            <span><i class="fas fa-clock"></i> ${(data.processing_time * 1000).toFixed(0)}ms</span>
            <span><i class="fas fa-database"></i> ${data.retrieval_stats.candidates} candidates</span>
            <span class="method-badge">${data.method}</span>
        </div>
    `;
    
    html += '</div>'; // Close strict-response
    
    return html;
}

function formatAnswer(text) {
    // Highlight citations
    return text
        .replace(/\[(\d+)\]/g, '<span class="citation-ref">[$1]</span>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// Updated send message function
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;

    // Clear welcome
    if (chatMessages.querySelector('.welcome-message')) {
        chatMessages.innerHTML = '';
    }

    // Add user message
    addMessage('user', message);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    isProcessing = true;
    showLoading(true);
    updateStatus('Searching database...');

    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: message,
                strict_mode: true,  // Always strict
                top_k: 5,
                temperature: 0.0
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            // Use strict display
            const html = displayStrictResponse(data);
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant strict';
            messageDiv.innerHTML = `
                <div class="message-avatar">⚡</div>
                <div class="message-content">${html}</div>
            `;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            addMessage('assistant', `Error: ${data.detail}`);
        }
    } catch (error) {
        addMessage('assistant', `Connection error: ${error.message}`);
    } finally {
        isProcessing = false;
        showLoading(false);
        updateStatus('Ready');
    }
}