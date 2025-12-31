let socket;
const chatStream = document.getElementById('chat-stream');
const connStatus = document.getElementById('connection-status');
const startBtn = document.getElementById('start-btn');
const manualToggle = document.getElementById('manual-toggle');
const hitlControls = document.getElementById('hitl-controls');
const manualPrice = document.getElementById('manual-price');
const manualMessage = document.getElementById('manual-message');
const btnCounter = document.getElementById('btn-counter');
const btnAccept = document.getElementById('btn-accept');
const sessionList = document.getElementById('session-list');
const displaySessionId = document.getElementById('display-session-id');

const ctx = document.getElementById('convergence-chart').getContext('2d');

let chart;
let isReplayMode = false;
const chartData = {
    labels: [],
    datasets: []
};

const COLORS = ['#00e5ff', '#7000ff', '#00ff88', '#ff3d00', '#f9d423'];

function initChart(numItems = 1) {
    if (chart) chart.destroy();
    chartData.labels = [];
    chartData.datasets = [];

    for (let i = 0; i < numItems; i++) {
        chartData.datasets.push({
            label: numItems > 1 ? `Item ${i + 1}` : 'Negotiation Price',
            borderColor: COLORS[i % COLORS.length],
            backgroundColor: `rgba(${parseInt(COLORS[i % COLORS.length].slice(1, 3), 16)}, ${parseInt(COLORS[i % COLORS.length].slice(3, 5), 16)}, ${parseInt(COLORS[i % COLORS.length].slice(5, 7), 16)}, 0.1)`,
            data: [],
            fill: false,
            tension: 0.4
        });
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: 10 },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255, 255, 255, 0.03)', drawBorder: false },
                    ticks: { color: '#606060', font: { family: 'JetBrains Mono', size: 10 } }
                },
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.03)', drawBorder: false },
                    ticks: { color: '#606060', font: { family: 'JetBrains Mono', size: 10 } }
                }
            },
            plugins: {
                legend: {
                    display: numItems > 1,
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: '#a0a0a0',
                        boxWidth: 12,
                        font: { family: 'Inter', size: 11, weight: '600' }
                    }
                }
            }
        }
    });
}

function typeWriter(element, text, speed = 20) {
    let i = 0;
    element.innerText = '';
    function type() {
        if (i < text.length) {
            element.innerText += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

function addMessage(agent, text, action) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${agent}`;

    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.innerText = `${agent.toUpperCase()} | ${action}`;

    const content = document.createElement('div');
    if (text) {
        typeWriter(content, text);
    } else {
        content.innerText = action === "ACCEPT" ? "Deal accepted!" : "Negotiation ended.";
    }

    msgDiv.appendChild(meta);
    msgDiv.appendChild(content);
    chatStream.appendChild(msgDiv);
    chatStream.scrollTop = chatStream.scrollHeight;
}

function updateStats(data) {
    if (data.type === 'init') {
        if (data.session_id) {
            displaySessionId.innerText = data.session_id.toUpperCase();
        }

        // Handle array or scalar valuations
        if (Array.isArray(data.val_s)) {
            const avg_s = data.val_s.reduce((a, b) => a + b, 0) / data.val_s.length;
            const avg_r = data.val_r.reduce((a, b) => a + b, 0) / data.val_r.length;
            document.getElementById('val-s').innerText = `$${avg_s.toFixed(0)}*`;
            document.getElementById('val-r').innerText = `$${avg_r.toFixed(0)}*`;
            document.getElementById('val-s').title = "Average Supplier Cost: " + data.val_s.map(v => `$${v.toFixed(0)}`).join(", ");
            document.getElementById('val-r').title = "Average Retailer Value: " + data.val_r.map(v => `$${v.toFixed(0)}`).join(", ");
            manualPrice.value = Math.round((avg_s + avg_r) / 2);
        } else {
            document.getElementById('val-s').innerText = `$${data.val_s.toFixed(2)}`;
            document.getElementById('val-r').innerText = `$${data.val_r.toFixed(2)}`;
            manualPrice.value = Math.round((data.val_s + data.val_r) / 2);
        }
    } else if (data.type === 'turn') {
        document.getElementById('current-round').innerText = `${data.round} / 10`;
        document.getElementById('agreement-status').innerText = 'NEGOTIATING';

        // Update Chart with prices (can be array or scalar)
        chartData.labels.push(`R${data.round}`);
        if (Array.isArray(data.price)) {
            data.price.forEach((p, i) => {
                if (chartData.datasets[i]) chartData.datasets[i].data.push(p);
            });
        } else {
            chartData.datasets[0].data.push(data.price);
        }
        chart.update();

        // Update Chat
        addMessage(data.agent, data.message, data.action);
        manualMessage.value = "";
    } else if (data.type === 'wait_for_human') {
        document.getElementById('agreement-status').innerText = `WAITING FOR ${data.agent.toUpperCase()}`;
        hitlControls.style.display = 'block';
        hitlControls.style.borderColor = data.agent === 'supplier' ? 'var(--accent-blue)' : 'var(--accent-purple)';
    } else if (data.type === 'log') {
        console.log("SERVER:", data.message);
    }

    if (data.type === 'end') {
        if (!isReplayMode) {
            startBtn.disabled = false;
            startBtn.innerText = 'RESTART SESSION';
            hitlControls.style.display = 'none';
            if (socket) socket.close();
            fetchSessions(); // Refresh history
        }
        document.getElementById('agreement-status').innerText = data.deal_price ? 'DEAL REACHED' : 'FAILED';
        document.getElementById('agreement-status').style.color = data.deal_price ? '#00ff00' : '#ff4b2b';
    }
}

async function fetchSessions() {
    try {
        const resp = await fetch('/api/sessions');
        const sessions = await resp.json();
        renderSessions(sessions);
    } catch (e) {
        console.error("Failed to fetch sessions", e);
    }
}

function renderSessions(sessions) {
    sessionList.innerHTML = '';
    if (sessions.length === 0) {
        sessionList.innerHTML = '<div style="font-size: 0.8rem; opacity: 0.5;">No history yet.</div>';
        return;
    }
    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'history-item';
        const date = new Date(s.timestamp).toLocaleString();
        item.innerHTML = `
            <div style="font-weight: 600;">${s.result} (${s.rounds} rounds)</div>
            <div class="meta">
                <span>${date}</span>
            </div>
        `;
        item.onclick = () => replaySession(s.id);
        sessionList.appendChild(item);
    });
}

async function replaySession(sessionId) {
    if (socket && socket.readyState === WebSocket.OPEN) socket.close();
    isReplayMode = true;
    startBtn.disabled = true;
    startBtn.innerText = 'REPLAYING...';
    chatStream.innerHTML = '';

    // Add replay badge
    let badge = document.querySelector('.replay-badge');
    if (!badge) {
        badge = document.createElement('div');
        badge.className = 'replay-badge';
        badge.innerText = 'REPLAY MODE';
        document.querySelector('.viz-area').appendChild(badge);
    }

    try {
        const resp = await fetch(`/api/sessions/${sessionId}`);
        const data = await resp.json();

        // Init
        updateStats({
            type: 'init',
            val_s: data.initial_state.val_s,
            val_r: data.initial_state.val_r,
            num_items: data.config.num_items
        });

        // Play turns
        for (const turn of data.turns) {
            await new Promise(r => setTimeout(r, 800));
            updateStats(turn);
        }

        // End
        updateStats({
            type: 'end',
            deal_price: data.deal_price,
            final_rewards: data.final_rewards
        });

    } catch (e) {
        console.error("Replay failed", e);
    } finally {
        startBtn.disabled = false;
        startBtn.innerText = 'START LIVE SESSION';
        isReplayMode = false;
        // Option to clear badge
        setTimeout(() => {
            if (!isReplayMode && badge) badge.remove();
        }, 3000);
    }
}

startBtn.addEventListener('click', () => {
    isReplayMode = false;
    chatStream.innerHTML = '';
    startBtn.disabled = true;
    startBtn.innerText = 'NEGOTIATING...';

    const badge = document.querySelector('.replay-badge');
    if (badge) badge.remove();

    // Reset chart will be handled in 'init' message handler
    socket = new WebSocket(`ws://${window.location.host}/ws/negotiate`);

    socket.onopen = () => {
        connStatus.innerText = 'API CONNECTED';
        connStatus.style.background = 'rgba(0, 255, 0, 0.1)';
        connStatus.style.color = '#00ff00';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateStats(data);
    };

    socket.onclose = () => {
        connStatus.innerText = 'API DISCONNECTED';
        connStatus.style.background = 'rgba(255, 0, 0, 0.1)';
        connStatus.style.color = '#ff4b2b';
    };
});

manualToggle.addEventListener('change', (e) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'toggle_manual', value: e.target.checked }));
    }
});

btnCounter.addEventListener('click', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'human_action',
            action: 1, // COUNTER
            price: parseFloat(manualPrice.value),
            message: manualMessage.value
        }));
        hitlControls.style.display = 'none';
    }
});

btnAccept.addEventListener('click', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: 'human_action',
            action: 0, // ACCEPT
            price: parseFloat(manualPrice.value),
            message: manualMessage.value
        }));
        hitlControls.style.display = 'none';
    }
});

initChart(1);
fetchSessions();
