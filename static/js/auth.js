// Authentication state
let currentUser = null;

async function checkAuthStatus() {
    try {
        const response = await fetch('/auth/status');
        const data = await response.json();
        if (data.authenticated && data.user) {
            currentUser = data.user;
            return true;
        }
        return false;
    } catch (error) {
        console.error('Auth check failed:', error);
        return false;
    }
}

async function handleLogin(email) {
    const submitBtn = document.getElementById('auth-submit');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Signing in...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            currentUser = data.user;
            localStorage.setItem('userEmail', data.user.email);
            localStorage.setItem('userId', data.user.id);
            hideAuthModal();
            enableAppInterface();
            updateTierInfo();
            if (typeof loadSessions === 'function') loadSessions(1);
            return true;
        } else {
            alert('Login failed: ' + data.message);
            return false;
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
        return false;
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

async function handleLogout() {
    try {
        await fetch('/auth/logout');
        currentUser = null;
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userId');
        disableAppInterface();
        showAuthModal();
        if (typeof clearChatArea === 'function') clearChatArea();
        if (typeof loadSessions === 'function') loadSessions(1);
    } catch (error) {
        console.error('Logout error:', error);
    }
}

function showAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
    const savedEmail = localStorage.getItem('userEmail');
    if (savedEmail) {
        const emailInput = document.getElementById('auth-email');
        if (emailInput) emailInput.value = savedEmail;
    }
}

function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}

function disableAppInterface() {
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) generateBtn.disabled = true;
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) saveBtn.disabled = true;
    
    const container = document.getElementById('flashcards-container');
    if (container) {
        container.innerHTML = '<div class="flashcard-placeholder"><p>Please sign in to generate studycards</p></div>';
    }
}

function enableAppInterface() {
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) generateBtn.disabled = false;
    
    if (typeof updateSaveButtonState === 'function') updateSaveButtonState();
}

async function updateTierInfo() {
    if (!currentUser) return;
    
    try {
        const response = await fetch('/user/tier-info');
        const data = await response.json();
        
        if (data.status === 'success') {
            const info = data.tier_info;
            const tierEl = document.getElementById('user-tier');
            if (tierEl) tierEl.textContent = info.tier.charAt(0).toUpperCase() + info.tier.slice(1) + ' Plan';
            
            const sessionsEl = document.getElementById('sessions-remaining');
            if (sessionsEl) sessionsEl.textContent = `Sessions remaining: ${info.remaining_sessions}`;

            const resetsEl = document.getElementById('resets-in');
            if (resetsEl) resetsEl.textContent = `Resets in: ${info.reset_in}`;

            const topbarEmailEl = document.getElementById('topbar-email');
            if (topbarEmailEl) topbarEmailEl.textContent = currentUser.email;

            // Mobile menu shows its own copies of this info - keep them in sync
            const mobileSessionsEl = document.getElementById('mobile-sessions-info');
            if (mobileSessionsEl) mobileSessionsEl.textContent = `Sessions: ${info.remaining_sessions} remaining`;

            if (typeof syncMobileUserData === 'function') syncMobileUserData();
        }
    } catch (error) {
        console.error('Error fetching tier info:', error);
    }
}