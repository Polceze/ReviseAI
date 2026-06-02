let progressChart = null;
let trendsChart = null;
let typePerformanceChart = null;
let difficultyChart = null;
let currentRangeFilter = '5';
let currentTimeFilter = '30';

function initProgressChart() {
    const canvas = document.getElementById('progress-chart');
    if (!canvas) return null;
    
    return new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels: [], datasets: [
            { label: 'Score (%)', data: [], borderColor: '#6e8efb', backgroundColor: 'rgba(110, 142, 251, 0.1)', yAxisID: 'y', tension: 0.3, fill: true },
            { label: 'Avg Time/Question (s)', data: [], borderColor: '#a777e3', backgroundColor: 'rgba(167, 119, 227, 0.1)', yAxisID: 'y1', tension: 0.3, fill: true }
        ] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { title: { display: true, text: 'Score (%)', color: '#f1f5f9' }, min: 0, max: 100, ticks: { color: '#f1f5f9' } },
                y1: { title: { display: true, text: 'Time (seconds)', color: '#f1f5f9' }, ticks: { color: '#f1f5f9' }, grid: { drawOnChartArea: false } },
                x: { ticks: { color: '#f1f5f9' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}

function initTrendsChart() {
    const canvas = document.getElementById('trends-chart');
    if (!canvas) return null;
    
    return new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels: [], datasets: [
            { label: 'Questions', data: [], borderColor: '#48bb78', backgroundColor: 'rgba(72, 187, 120, 0.1)', yAxisID: 'y', tension: 0.4, fill: true },
            { label: 'Duration (min)', data: [], borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', yAxisID: 'y1', tension: 0.4, fill: true }
        ] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { title: { display: true, text: 'Questions', color: '#f1f5f9' }, ticks: { color: '#f1f5f9' } },
                y1: { title: { display: true, text: 'Duration (min)', color: '#f1f5f9' }, ticks: { color: '#f1f5f9' }, grid: { drawOnChartArea: false } },
                x: { ticks: { color: '#f1f5f9' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}

function initTypePerformanceChart() {
    const canvas = document.getElementById('type-performance-chart');
    if (!canvas) return null;
    
    return new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: { labels: ['Multiple Choice', 'True/False'], datasets: [{ data: [0, 0], backgroundColor: ['#4299e1', '#9f7aea'] }] },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function initDifficultyChart() {
    const canvas = document.getElementById('difficulty-chart');
    if (!canvas) return null;
    
    return new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: { labels: ['Normal', 'Difficult'], datasets: [{ label: 'Accuracy %', data: [0, 0], backgroundColor: ['#48bb78', '#f56565'], borderRadius: 6 }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Accuracy (%)' }, ticks: { color: '#f1f5f9' } }, x: { ticks: { color: '#f1f5f9' } } },
            plugins: { legend: { display: false } }
        }
    });
}

function initAllCharts() {
    if (document.getElementById('progress-chart') && !progressChart) progressChart = initProgressChart();
    if (document.getElementById('trends-chart') && !trendsChart) trendsChart = initTrendsChart();
    if (document.getElementById('type-performance-chart') && !typePerformanceChart) typePerformanceChart = initTypePerformanceChart();
    if (document.getElementById('difficulty-chart') && !difficultyChart) difficultyChart = initDifficultyChart();
}

function updateProgressChart(sessions, limit = 5) {
    if (!progressChart) return;
    
    if (!sessions || sessions.length === 0) {
        progressChart.data.labels = [];
        progressChart.data.datasets[0].data = [];
        progressChart.data.datasets[1].data = [];
        progressChart.update();
        return;
    }
    
    const sorted = [...sessions].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, limit);
    const chartSessions = [...sorted].reverse();
    
    progressChart.data.labels = chartSessions.map(s => new Date(s.created_at).toLocaleDateString());
    progressChart.data.datasets[0].data = chartSessions.map(s => s.score_percentage);
    progressChart.data.datasets[1].data = chartSessions.map(s => Math.round(s.session_duration / (s.total_questions || 1)));
    progressChart.update();
}

function updateTrendsChart(sessions) {
    if (!trendsChart) return;
    
    const sorted = [...sessions].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    trendsChart.data.labels = sorted.map(s => new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    trendsChart.data.datasets[0].data = sorted.map(s => s.total_questions || 0);
    trendsChart.data.datasets[1].data = sorted.map(s => Math.round(((s.session_duration || 0) / 60) * 10) / 10);
    trendsChart.update();
}

function updateTypePerformanceChart(typeData) {
    if (!typePerformanceChart) return;
    typePerformanceChart.data.datasets[0].data = [
        typeData.mcq.total > 0 ? (typeData.mcq.correct / typeData.mcq.total) * 100 : 0,
        typeData.tf.total > 0 ? (typeData.tf.correct / typeData.tf.total) * 100 : 0
    ];
    typePerformanceChart.update();
}

function updateDifficultyChart(difficultyData) {
    if (!difficultyChart) return;
    difficultyChart.data.datasets[0].data = [
        difficultyData.normal.total > 0 ? (difficultyData.normal.correct / difficultyData.normal.total) * 100 : 0,
        difficultyData.difficult.total > 0 ? (difficultyData.difficult.correct / difficultyData.difficult.total) * 100 : 0
    ];
    difficultyChart.update();
}

function updateSummaryStats(sessions) {
    const avgScoreEl = document.getElementById('average-score');
    const totalQuestionsEl = document.getElementById('total-questions');
    const sessionsCountEl = document.getElementById('sessions-count');
    const successRateEl = document.getElementById('success-rate');
    
    if (!avgScoreEl) return;
    
    if (!sessions || sessions.length === 0) {
        avgScoreEl.textContent = '0%';
        totalQuestionsEl.textContent = '0';
        sessionsCountEl.textContent = '0';
        successRateEl.textContent = '0%';
        return;
    }
    
    const totalSessions = sessions.length;
    const totalQuestions = sessions.reduce((sum, s) => sum + (Number(s.total_questions) || 0), 0);
    const avgScore = sessions.reduce((sum, s) => sum + (Number(s.score_percentage) || 0), 0) / totalSessions;
    const successful = sessions.filter(s => (Number(s.score_percentage) || 0) >= 80).length;
    
    avgScoreEl.textContent = `${avgScore.toFixed(1)}%`;
    totalQuestionsEl.textContent = totalQuestions;
    sessionsCountEl.textContent = totalSessions;
    successRateEl.textContent = `${((successful / totalSessions) * 100).toFixed(1)}%`;
}

function applyAnalyticsFilters() {
    const rangeSelect = document.getElementById('sessions-range');
    const timeSelect = document.getElementById('time-period');
    
    if (!rangeSelect || !timeSelect) return;
    
    currentRangeFilter = rangeSelect.value;
    currentTimeFilter = timeSelect.value;
    
    const rangeLimit = currentRangeFilter === 'all' ? allSessions.length : parseInt(currentRangeFilter);
    const daysLimit = currentTimeFilter === 'all' ? null : parseInt(currentTimeFilter);
    
    let filtered = [...allSessions];
    
    if (daysLimit) {
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - daysLimit);
        filtered = filtered.filter(s => new Date(s.created_at) >= cutoff);
    }
    
    filtered = filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, rangeLimit);
    
    updateSummaryStats(filtered);
    updateProgressChart(filtered, rangeLimit);
    updateTrendsChart(filtered);
    loadAdvancedAnalyticsForSessions(filtered);
}

async function loadAdvancedAnalyticsForSessions(sessions) {
    const sessionIds = sessions.map(s => s.id);
    
    if (sessionIds.length === 0) {
        updateTypePerformanceChart({ mcq: { total: 0, correct: 0 }, tf: { total: 0, correct: 0 } });
        updateDifficultyChart({ normal: { total: 0, correct: 0 }, difficult: { total: 0, correct: 0 } });
        return;
    }
    
    try {
        const response = await fetch('/analytics/type-difficulty-filtered', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_ids: sessionIds })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const typeData = { mcq: { total: 0, correct: 0 }, tf: { total: 0, correct: 0 } };
            const difficultyData = { normal: { total: 0, correct: 0 }, difficult: { total: 0, correct: 0 } };
            
            data.data.question_types?.forEach(item => {
                if (item.question_type in typeData) {
                    typeData[item.question_type] = { total: item.total_questions, correct: item.correct_answers };
                }
            });
            
            data.data.difficulties?.forEach(item => {
                if (item.difficulty in difficultyData) {
                    difficultyData[item.difficulty] = { total: item.total_questions, correct: item.correct_answers };
                }
            });
            
            updateTypePerformanceChart(typeData);
            updateDifficultyChart(difficultyData);
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}