let allSessions = [];
let currentPage = 1;
const sessionsPerPage = 5;

async function loadSessions(page = 1) {
    if (!window.currentUser) {
        const container = document.getElementById('sessions-container');
        if (container) container.innerHTML = '<p class="no-sessions">Please sign in to view your study sessions</p>';
        if (typeof updateProgressChart === 'function') updateProgressChart([], 5);
        return;
    }
    
    try {
        const response = await fetch('/get_sessions');
        if (response.status === 401) throw new Error('Authentication required');
        
        const data = await response.json();
        
        if (data.status === 'success') {
            allSessions = data.sessions;
            const container = document.getElementById('sessions-container');
            
            if (container) {
                if (allSessions.length === 0) {
                    container.innerHTML = '<p class="no-sessions">No study sessions yet.</p>';
                } else {
                    renderPaginatedSessions();
                }
            }
            
            if (window.location.pathname === '/analytics' && typeof applyAnalyticsFilters === 'function') {
                applyAnalyticsFilters();
            }
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
        const container = document.getElementById('sessions-container');
        if (container) container.innerHTML = '<p class="no-sessions">Error loading sessions</p>';
    }
}

function renderPaginatedSessions() {
    const container = document.getElementById('sessions-container');
    const pagination = document.getElementById('pagination-controls');
    
    if (!container || !pagination) return;
    
    const sorted = [...allSessions].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    const start = (currentPage - 1) * sessionsPerPage;
    const paginated = sorted.slice(start, start + sessionsPerPage);
    
    renderSessions(paginated);
    renderPaginationControls();
}

function renderSessions(sessions) {
    const container = document.getElementById('sessions-container');
    if (!container) return;
    
    if (!sessions.length) {
        container.innerHTML = '<p>No sessions found.</p>';
        return;
    }
    
    const list = document.createElement('ul');
    list.className = 'sessions-list';
    
    sessions.forEach(session => {
        const minutes = (session.session_duration || 0) / 60;
        const durationDisplay = minutes < 1 ? '<1 minute' : `${Math.round(minutes * 2) / 2} ${Math.round(minutes) === 1 ? 'minute' : 'minutes'}`;
        
        const score = session.score_percentage || 0;
        const scoreClass = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
        
        const item = document.createElement('li');
        item.className = 'session-item';
        item.innerHTML = `
            <div class="session-content">
                <div class="session-topic">${escapeHtml(session.title)}</div>
            </div>
            <div class="session-stats">
                <div class="session-stat">⏱️ ${durationDisplay}</div>
                <div class="session-stat">📊 ${session.total_questions} questions</div>
                <div class="session-stat ${scoreClass}">🎯 ${score}%</div>
            </div>
            <div class="session-actions">
                <button class="view-session-btn" data-id="${session.id}">View</button>
                <button class="delete-session-btn" data-id="${session.id}">Delete</button>
            </div>
        `;
        list.appendChild(item);
    });
    
    container.innerHTML = '';
    container.appendChild(list);
    
    // Attach delete handlers
    document.querySelectorAll('.delete-session-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(btn.dataset.id);
        });
    });
}

function renderPaginationControls() {
    const container = document.getElementById('pagination-controls');
    if (!container) return;
    
    const totalPages = Math.ceil(allSessions.length / sessionsPerPage);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <button class="pagination-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>← Previous</button>
        <span class="pagination-info">Page ${currentPage} of ${totalPages}</span>
        <button class="pagination-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>
    `;
}

function changePage(page) {
    const totalPages = Math.ceil(allSessions.length / sessionsPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderPaginatedSessions();
}

async function deleteSession(sessionId) {
    if (!confirm('Delete this session? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`/delete_session/${sessionId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.status === 'success') {
            loadSessions(currentPage);
            showTempMessage('Session deleted', 'success');
        } else {
            alert('Error deleting session');
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Error deleting session');
    }
}

async function openSessionModal(sessionId) {
    const modal = document.getElementById('session-detail-modal');
    if (!modal) return;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    try {
        const response = await fetch(`/get_flashcards/${sessionId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            populateSessionModal(sessionId, data.flashcards);
        } else {
            throw new Error('Failed to load session');
        }
    } catch (error) {
        console.error('Error loading session:', error);
        document.getElementById('session-questions-container').innerHTML = '<div class="error-message">Error loading session</div>';
    }
}

function populateSessionModal(sessionId, flashcards) {
    const session = allSessions.find(s => s.id == sessionId);
    const total = flashcards.length;
    const correct = flashcards.filter(c => c.is_correct).length;
    const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
    
    document.getElementById('session-modal-title').textContent = session?.title || `Session ${sessionId}`;
    document.getElementById('session-modal-date').textContent = session?.created_at ? `Created: ${formatUTCDate(session.created_at)}` : 'Created: Unknown';
    document.getElementById('session-modal-score').textContent = `Score: ${percent}% (${correct}/${total})`;
    
    const container = document.getElementById('session-questions-container');
    container.innerHTML = flashcards.map((card, idx) => `
        <div class="session-question">
            <div class="session-question-text">${idx + 1}. ${escapeHtml(card.question)}</div>
            <div class="session-options">
                ${card.options.map((opt, optIdx) => {
                    const isUser = optIdx === card.user_answer;
                    const isCorrect = optIdx === card.correct_answer;
                    let classes = 'session-option';
                    if (isUser) classes += isUser === isCorrect ? ' correct' : ' incorrect';
                    if (isCorrect && !isUser) classes += ' correct';
                    let indicator = '';
                    if (isUser) indicator = isUser === isCorrect ? ' ✓ Your answer' : ' ✗ Your answer';
                    if (isCorrect && !isUser) indicator = ' ✓ Correct answer';
                    return `<div class="${classes}">${String.fromCharCode(65 + optIdx)}) ${escapeHtml(opt)}${indicator}</div>`;
                }).join('')}
            </div>
        </div>
    `).join('');
    
    const deleteBtn = document.getElementById('modal-delete-session-btn');
    if (deleteBtn) deleteBtn.setAttribute('data-session-id', sessionId);
}

function closeSessionModal() {
    const modal = document.getElementById('session-detail-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

async function deleteSessionFromModal(sessionId) {
    const deleteBtn = document.getElementById('modal-delete-session-btn');
    const originalText = deleteBtn.textContent;
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
        const response = await fetch(`/delete_session/${sessionId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.status === 'success') {
            closeSessionModal();
            loadSessions(currentPage);
            showTempMessage('Session deleted', 'success');
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Error deleting session');
        deleteBtn.textContent = originalText;
        deleteBtn.disabled = false;
    }
}