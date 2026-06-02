// Main application initialization
document.addEventListener('DOMContentLoaded', async function() {
    console.log('ReviseAI initialized');
    
    // Initialize UI components
    initMobileNavigation();
    initCollapsibleSidebar();
    
    // Check authentication
    const isAuthenticated = await checkAuthStatus();
    
    if (isAuthenticated) {
        enableAppInterface();
        updateTierInfo();
        loadSessions(1);
        
        // Initialize charts on analytics page
        if (window.location.pathname === '/analytics') {
            initAllCharts();
            setTimeout(() => applyAnalyticsFilters(), 500);
        }
    } else {
        disableAppInterface();
        showAuthModal();
    }
    
    // Set up event listeners
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) generateBtn.addEventListener('click', generateFlashcards);
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) saveBtn.addEventListener('click', saveFlashcards);
    
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);
    
    const authSubmit = document.getElementById('auth-submit');
    if (authSubmit) {
        authSubmit.addEventListener('click', () => {
            const email = document.getElementById('auth-email').value.trim();
            if (email && email.includes('@')) handleLogin(email);
            else alert('Please enter a valid email');
        });
    }
    
    const authEmail = document.getElementById('auth-email');
    if (authEmail) {
        authEmail.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') authSubmit.click();
        });
    }
    
    // Modal option handlers
    const continueBtn = document.getElementById('continue-same-notes');
    const startFreshBtn = document.getElementById('start-fresh');
    const stayBtn = document.getElementById('view-progress');
    const modalClose = document.getElementById('modal-close-btn');
    
    if (continueBtn) continueBtn.addEventListener('click', () => resetUIForNewSession(false));
    if (startFreshBtn) startFreshBtn.addEventListener('click', () => resetUIForNewSession(true));
    if (stayBtn) stayBtn.addEventListener('click', hideSuccessModal);
    if (modalClose) modalClose.addEventListener('click', closeSessionModal);
    
    // Session detail modal delete button
    const modalDelete = document.getElementById('modal-delete-session-btn');
    if (modalDelete) {
        modalDelete.addEventListener('click', () => {
            const sessionId = modalDelete.getAttribute('data-session-id');
            if (sessionId && confirm('Delete this session? This cannot be undone.')) {
                deleteSessionFromModal(sessionId);
            }
        });
    }
    
    // Chart range selectors
    const rangeSelect = document.getElementById('sessions-range');
    const timeSelect = document.getElementById('time-period');
    if (rangeSelect && timeSelect && window.location.pathname === '/analytics') {
        rangeSelect.addEventListener('change', applyAnalyticsFilters);
        timeSelect.addEventListener('change', applyAnalyticsFilters);
    }
    
    // Resize handler for card heights
    window.addEventListener('resize', debounce(setUniformCardHeights, 200));
    
    // Window resize handler for topbar visibility
    window.addEventListener('resize', function() {
        const topbar = document.getElementById('auth-topbar');
        if (topbar && currentUser) {
            topbar.style.display = window.innerWidth >= 1024 ? 'block' : 'none';
        }
    });
});