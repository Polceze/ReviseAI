let flashcardsData = [];
let hasSavedCurrentSet = false;
let sessionStartTime = null;
let currentSessionId = null;
let currentQuestionType = 'mcq';
let currentDifficulty = 'normal';

async function generateFlashcards() {
    hasSavedCurrentSet = false;
    sessionStartTime = new Date();
    currentSessionId = null;
    
    const notes = document.getElementById('study-notes').value.trim();
    const count = parseInt(document.getElementById('num-questions').value, 10) || 6;
    const questionType = document.getElementById('question-type')?.value || 'mcq';
    const difficulty = document.getElementById('question-difficulty')?.value || 'normal';
    
    currentQuestionType = questionType;
    currentDifficulty = difficulty;
    
    if (!notes) {
        alert('Please enter some study notes first.');
        return;
    }
    
    const loader = document.getElementById('loader');
    const generateBtn = document.getElementById('generate-btn');
    
    if (loader) loader.style.display = 'block';
    if (generateBtn) generateBtn.disabled = true;
    
    try {
        const response = await fetch('/generate_questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes, num_questions: count, question_type: questionType, difficulty })
        });
        
        if (response.status === 429) {
            const errorData = await response.json();
            throw new Error(`SESSION_LIMIT_EXCEEDED:${errorData.remaining || 0}`);
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`AI_ERROR:${errorData.message || 'Unknown error'}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && Array.isArray(data.questions)) {
            flashcardsData = data.questions.map((q, i) => ({
                id: q.id ?? i,
                question: q.question ?? q.text ?? '',
                options: Array.isArray(q.options) ? q.options : [],
                correctAnswer: q.correctAnswer ?? q.correct_answer ?? 0,
                userAnswer: q.userAnswer ?? q.user_answer ?? null,
                is_correct: q.is_correct ?? null,
                questionType: q.questionType ?? q.question_type ?? 'mcq',
                difficulty: q.difficulty ?? 'normal',
                answered: false
            }));
            
            displayFlashcards();
            
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.textContent = 'Save Session First';
            }
            
            const saveBtn = document.getElementById('save-btn');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save study session';
            }
        } else {
            alert('Error generating questions: ' + (data.message || 'Unknown error'));
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate studycards';
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (error.message.startsWith('SESSION_LIMIT_EXCEEDED')) {
            alert('Daily limit reached. You can create new sessions again at midnight.');
            const generateBtn = document.getElementById('generate-btn');
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.textContent = 'Daily Limit Reached';
            }
        } else {
            alert('Error generating questions. Please try again.');
            const generateBtn = document.getElementById('generate-btn');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate studycards';
            }
        }
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

function displayFlashcards() {
    const container = document.getElementById('flashcards-container');
    const scoreContainer = document.getElementById('score-container');
    
    if (!container) return;
    
    container.innerHTML = '';
    if (scoreContainer) scoreContainer.textContent = 'Score: 0/0 (0%)';
    
    const isTouch = 'ontouchstart' in window;
    const flipInstruction = isTouch ? 'Select answer, tap to flip' : 'Select answer, click to flip';
    
    flashcardsData.forEach((card, index) => {
        const cardEl = document.createElement('div');
        cardEl.className = 'flashcard';
        cardEl.setAttribute('data-index', index);
        
        cardEl.innerHTML = `
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div class="question">${escapeHtml(card.question)}</div>
                    <div class="options">
                        ${card.options.map((opt, optIndex) => {
                            const label = card.questionType === 'tf' 
                                ? (optIndex === 0 ? 'True' : 'False')
                                : `${String.fromCharCode(65 + optIndex)}) ${escapeHtml(opt)}`;
                            return `<div class="option" data-option="${optIndex}">${label}</div>`;
                        }).join('')}
                    </div>
                    <div class="instructions">${flipInstruction}</div>
                </div>
                <div class="flashcard-back">
                    <div class="question">${escapeHtml(card.question)}</div>
                    <div class="feedback" id="feedback-${index}"></div>
                    <div class="instructions">${isTouch ? 'Tap to return' : 'Click to return'}</div>
                </div>
            </div>
        `;
        
        container.appendChild(cardEl);
        
        // Add option listeners
        cardEl.querySelectorAll('.option').forEach(optEl => {
            optEl.addEventListener('click', (e) => {
                e.stopPropagation();
                selectAnswer(parseInt(cardEl.dataset.index), parseInt(optEl.dataset.option));
            });
        });
        
        // Add flip listener
        cardEl.addEventListener('click', () => {
            const cardIndex = parseInt(cardEl.dataset.index);
            const card = flashcardsData[cardIndex];
            
            if (card.userAnswer === null) {
                alert('Please select an answer first.');
                return;
            }
            
            if (!card.answered) {
                card.answered = true;
                updateCardUI(cardIndex);
                updateScore();
                cardEl.classList.add('revealed');
            }
            
            cardEl.classList.toggle('flipped');
        });
    });
    
    setUniformCardHeights();
    if (typeof updateSaveButtonState === 'function') updateSaveButtonState();
}

function selectAnswer(cardIndex, optionIndex) {
    const card = flashcardsData[cardIndex];
    if (card.answered) return;
    
    card.userAnswer = optionIndex;
    
    const cardEl = document.querySelector(`.flashcard[data-index="${cardIndex}"]`);
    cardEl.querySelectorAll('.option').forEach(el => el.classList.remove('selected'));
    cardEl.querySelectorAll('.option')[optionIndex].classList.add('selected');
    
    if (typeof updateSaveButtonState === 'function') updateSaveButtonState();
}

function updateCardUI(cardIndex) {
    const card = flashcardsData[cardIndex];
    const cardEl = document.querySelector(`.flashcard[data-index="${cardIndex}"]`);
    const options = cardEl.querySelectorAll('.option');
    const feedbackEl = document.getElementById(`feedback-${cardIndex}`);
    
    options.forEach((el, idx) => {
        if (idx === card.correctAnswer) {
            el.classList.add('correct');
        }
        if (idx === card.userAnswer) {
            if (idx === card.correctAnswer) {
                el.classList.add('correct');
                if (feedbackEl) feedbackEl.textContent = "Correct! ✅";
            } else {
                el.classList.add('incorrect');
                if (feedbackEl) feedbackEl.textContent = "Incorrect! ❌";
            }
        }
    });
}

function updateScore() {
    const answered = flashcardsData.filter(c => c.answered).length;
    const total = flashcardsData.length;
    const scoreEl = document.getElementById('score-container');
    
    if (answered < total) {
        scoreEl.textContent = `Progress: ${answered}/${total} answered`;
    } else {
        const correct = flashcardsData.filter(c => c.userAnswer === c.correctAnswer).length;
        const percent = Math.round((correct / total) * 100);
        scoreEl.textContent = `Score: ${correct}/${total} (${percent}%)`;
    }
}

async function saveFlashcards() {
    if (hasSavedCurrentSet) {
        alert('This session has already been saved.');
        return;
    }
    
    const notes = document.getElementById('study-notes').value;
    const unanswered = flashcardsData.filter(c => c.userAnswer === null);
    const unrevealed = flashcardsData.filter(c => !c.answered);
    
    if (unanswered.length > 0) {
        alert(`Please answer all ${unanswered.length} questions first.`);
        return;
    }
    if (unrevealed.length > 0) {
        alert(`Please reveal all ${unrevealed.length} answers first.`);
        return;
    }
    
    const saveBtn = document.getElementById('save-btn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    const endTime = new Date();
    const duration = endTime - sessionStartTime;
    
    try {
        const response = await fetch('/save_flashcards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                flashcards: flashcardsData,
                notes: notes,
                session_start_time: sessionStartTime.toISOString(),
                session_end_time: endTime.toISOString(),
                session_duration: duration
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            hasSavedCurrentSet = true;
            saveBtn.disabled = true;
            saveBtn.textContent = '✓ Saved';
            showSuccessModal();
            if (typeof loadSessions === 'function') loadSessions(1);
            if (typeof updateTierInfo === 'function') updateTierInfo();
        } else {
            alert('Error saving session: ' + data.message);
            saveBtn.disabled = false;
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Error saving session');
        saveBtn.disabled = false;
    } finally {
        if (!hasSavedCurrentSet) saveBtn.textContent = originalText;
    }
}

function updateSaveButtonState() {
    const saveBtn = document.getElementById('save-btn');
    if (!saveBtn) return;
    
    if (hasSavedCurrentSet) {
        saveBtn.disabled = true;
        saveBtn.textContent = '✓ Saved';
    } else if (flashcardsData.length > 0) {
        const unanswered = flashcardsData.filter(c => c.userAnswer === null).length;
        saveBtn.disabled = unanswered > 0;
        saveBtn.textContent = 'Save study session';
    } else {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Save study session';
    }
}

function setUniformCardHeights() {
    const cards = document.querySelectorAll('.flashcard');
    if (cards.length === 0) return;
    
    let maxHeight = 0;
    cards.forEach(c => c.style.height = 'auto');
    cards.forEach(c => {
        const front = c.querySelector('.flashcard-front');
        const back = c.querySelector('.flashcard-back');
        const height = Math.max(front?.scrollHeight || 0, back?.scrollHeight || 0);
        maxHeight = Math.max(maxHeight, height);
    });
    cards.forEach(c => c.style.height = `${maxHeight + 20}px`);
}

function escapeHtml(str) {
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function clearChatArea() {
    flashcardsData = [];
    hasSavedCurrentSet = false;
    
    const container = document.getElementById('flashcards-container');
    if (container) {
        container.innerHTML = '<div class="flashcard-placeholder"><p>Your studycards will appear here after generating them from your notes.</p></div>';
    }
    
    const scoreEl = document.getElementById('score-container');
    if (scoreEl) scoreEl.textContent = 'Score: 0/0 (0%)';
    
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Save study session';
    }
    
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate studycards';
    }
}