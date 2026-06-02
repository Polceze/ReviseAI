// UI Component Functions
function showSuccessModal() {
    const modal = document.getElementById('success-modal');
    if (modal) modal.style.display = 'flex';
}

function hideSuccessModal() {
    const modal = document.getElementById('success-modal');
    if (modal) modal.style.display = 'none';
}

function resetUIForNewSession(clearNotes = true) {
    flashcardsData = [];
    const container = document.getElementById('flashcards-container');
    if (container) {
        container.innerHTML = '<div class="flashcard-placeholder"><p>Your studycards will appear here after generating them from your notes.</p></div>';
    }
    
    if (clearNotes) {
        const notes = document.getElementById('study-notes');
        if (notes) notes.value = '';
    }
    
    const scoreEl = document.getElementById('score-container');
    if (scoreEl) scoreEl.textContent = 'Score: 0/0 (0%)';
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Save study session';
    }
    hasSavedCurrentSet = false;
    
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate studycards';
    }
    
    hideSuccessModal();
}

function initMobileNavigation() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const overlay = document.getElementById('mobile-menu-overlay');
    const closeBtn = document.getElementById('mobile-close-btn');
    
    if (!toggle || !overlay) return;
    
    toggle.addEventListener('click', () => overlay.classList.add('active'));
    closeBtn?.addEventListener('click', () => overlay.classList.remove('active'));
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
    });
}

function initCollapsibleSidebar() {
    const sidebar = document.getElementById('desktop-sidebar');
    if (!sidebar) return;
    
    let isExpanded = false;
    let touchExpanded = false;
    
    function expand() {
        if (window.innerWidth >= 1024 && window.innerWidth < 1200) {
            sidebar.classList.add('expanded');
            isExpanded = true;
        }
    }
    
    function collapse() {
        if (window.innerWidth >= 1024 && window.innerWidth < 1200) {
            sidebar.classList.remove('expanded');
            isExpanded = false;
        }
    }
    
    sidebar.addEventListener('click', (e) => {
        if (window.innerWidth >= 1024 && window.innerWidth < 1200) {
            if (!isExpanded) {
                e.preventDefault();
                expand();
                touchExpanded = true;
            } else if (e.target.closest('.sidebar-link') && touchExpanded) {
                setTimeout(collapse, 300);
                touchExpanded = false;
            }
        }
    });
    
    document.addEventListener('click', (e) => {
        if (isExpanded && !sidebar.contains(e.target) && window.innerWidth >= 1024 && window.innerWidth < 1200) {
            collapse();
            touchExpanded = false;
        }
    });
    
    // Initialize based on screen size
    if (window.innerWidth >= 1200) {
        sidebar.classList.add('expanded');
        isExpanded = true;
    }
}

function syncMobileUserData() {
    const desktopEmail = document.getElementById('topbar-email');
    const mobileEmail = document.getElementById('mobile-user-email');
    if (desktopEmail && mobileEmail) {
        mobileEmail.textContent = desktopEmail.textContent;
    }
    
    const tierEl = document.getElementById('user-tier');
    const mobileTier = document.getElementById('mobile-tier-label');
    if (tierEl && mobileTier) {
        mobileTier.textContent = tierEl.textContent;
    }
}