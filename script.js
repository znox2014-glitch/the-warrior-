// spider_web/static/js/script.js

let eventSource = null;
let isRunning = false;
let stats = {
    generated: 0,
    rare: 0,
    couples: 0,
    errors: 0
};

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('generatorForm');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusBadge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    const logsContainer = document.getElementById('logsContainer');
    const accountsContainer = document.getElementById('accountsContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    // Load initial accounts
    refreshAccounts();

    // Form submit - Start generation
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (isRunning) return;

        const formData = new FormData(form);
        const data = {
            region: formData.get('region'),
            nickname: formData.get('nickname') || 'SPIDER',
            password: formData.get('password') || 'SPIDY',
            total: parseInt(formData.get('total')) || 100,
            threads: parseInt(formData.get('threads')) || 50,
            ghost: formData.has('ghost'),
            auto_activate: formData.has('auto_activate')
        };

        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (result.status === 'started') {
                isRunning = true;
                updateUI();
                connectSSE();
                addLog('🚀 Generation started', 'success');
                startBtn.disabled = true;
                stopBtn.disabled = false;
                statusBadge.textContent = '● Running';
                statusBadge.className = 'status-badge running';
                statusText.textContent = '🔄 Generating accounts...';
                resetStats();
            } else {
                addLog('❌ Failed to start: ' + result.message, 'error');
            }
        } catch (error) {
            addLog('❌ Error: ' + error.message, 'error');
        }
    });

    // Stop button
    stopBtn.addEventListener('click', async function() {
        if (!isRunning) return;
        try {
            await fetch('/api/stop', { method: 'POST' });
            isRunning = false;
            updateUI();
            addLog('⏹ Generation stopped by user', 'error');
            statusText.textContent = '⏹ Stopped';
        } catch (error) {
            addLog('❌ Stop error: ' + error.message, 'error');
        }
    });

    // Clear logs
    document.getElementById('clearLogsBtn').addEventListener('click', function() {
        logsContainer.innerHTML = '';
        addLog('🗑️ Logs cleared', 'info');
    });

    // Refresh accounts
    document.getElementById('refreshAccountsBtn').addEventListener('click', refreshAccounts);

    function connectSSE() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource('/api/stream');

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleSSEMessage(data);
            } catch (e) {
                console.error('SSE parse error:', e);
            }
        };

        eventSource.onerror = function() {
            if (isRunning) {
                // Try to reconnect after delay
                setTimeout(connectSSE, 3000);
            }
        };
    }

    function handleSSEMessage(data) {
        switch(data.type) {
            case 'info':
                addLog('ℹ️ ' + data.message, 'info');
                break;
            case 'success':
                addLog('✅ ' + data.message, 'success');
                break;
            case 'error':
                addLog('❌ ' + data.message, 'error');
                stats.errors++;
                updateStats();
                break;
            case 'account':
                addLog('📝 ' + data.message, 'account');
                stats.generated++;
                updateStats();
                updateProgress();
                break;
            case 'rare':
                addLog('💎 ' + data.message, 'rare');
                stats.rare++;
                updateStats();
                break;
            case 'couple':
                addLog('💑 ' + data.message, 'couple');
                stats.couples++;
                updateStats();
                break;
            case 'done':
                addLog('✅ ' + data.message, 'success');
                isRunning = false;
                updateUI();
                startBtn.disabled = false;
                stopBtn.disabled = true;
                statusBadge.textContent = '● Done';
                statusBadge.className = 'status-badge';
                statusText.textContent = '✅ Generation complete!';
                refreshAccounts();
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                break;
            case 'ping':
                // Keep-alive, do nothing
                break;
            default:
                if (data.message) {
                    addLog(data.message, 'info');
                }
        }
    }

    function addLog(message, type = 'info') {
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        div.textContent = message;
        logsContainer.appendChild(div);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    function updateStats() {
        document.getElementById('statGenerated').textContent = stats.generated;
        document.getElementById('statRare').textContent = stats.rare;
        document.getElementById('statCouples').textContent = stats.couples;
        document.getElementById('statErrors').textContent = stats.errors;
    }

    function resetStats() {
        stats.generated = 0;
        stats.rare = 0;
        stats.couples = 0;
        stats.errors = 0;
        updateStats();
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
    }

    function updateProgress() {
        const total = parseInt(document.getElementById('total').value) || 100;
        const percent = Math.min((stats.generated / total) * 100, 100);
        progressBar.style.width = percent + '%';
        progressText.textContent = Math.round(percent) + '%';
    }

    function updateUI() {
        if (isRunning) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusBadge.textContent = '● Running';
            statusBadge.className = 'status-badge running';
            statusText.textContent = '🔄 Generating accounts...';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusBadge.textContent = '● Ready';
            statusBadge.className = 'status-badge';
            statusText.textContent = 'Ready to generate';
        }
    }

    async function refreshAccounts() {
        try {
            const response = await fetch('/api/accounts');
            const data = await response.json();
            
            accountsContainer.innerHTML = '';
            if (data.length === 0) {
                accountsContainer.innerHTML = '<div class="empty-state">No accounts generated yet</div>';
                return;
            }

            data.forEach(acc => {
                const div = document.createElement('div');
                div.className = 'log-entry account';
                div.textContent = `[${acc.region}] ${acc.line}`;
                accountsContainer.appendChild(div);
            });
        } catch (error) {
            console.error('Refresh accounts error:', error);
        }
    }

    // Periodic status check
    setInterval(async function() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            if (data.running !== isRunning) {
                isRunning = data.running;
                updateUI();
                if (!isRunning && eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
            }
        } catch (e) {
            // ignore
        }
    }, 5000);
});