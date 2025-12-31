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

const ctx = document.getElementById('convergence-chart').getContext('2d');

let chart;
const chartData = {
    labels: [],
    datasets: [
        {
            label: 'Negotiation Price',
            borderColor: '#00d2ff',
            backgroundColor: 'rgba(0, 210, 255, 0.1)',
            data: [],
            fill: true,
            tension: 0.4
        }
    ]
};

function initChart() {
    chart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#b0b0b0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#b0b0b0' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function addMessage(agent, text, action) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${agent}`;

    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.innerText = `${agent.toUpperCase()} | ${action}`;

    const content = document.createElement('div');
    content.innerText = text || (action === "ACCEPT" ? "Deal accepted!" : "Negotiation ended.");

    msgDiv.appendChild(meta);
    msgDiv.appendChild(content);
    chatStream.appendChild(msgDiv);
    chatStream.scrollTop = chatStream.scrollHeight;
}

function updateStats(data) {
    if (data.type === 'init') {
        document.getElementById('val-s').innerText = `$${data.val_s.toFixed(2)}`;
        document.getElementById('val-r').innerText = `$${data.val_r.toFixed(2)}`;
        // Set initial reasonable price in manual input
        manualPrice.value = Math.round((data.val_s + data.val_r) / 2);
    } else if (data.type === 'turn') {
        document.getElementById('current-round').innerText = `${data.round} / 10`;
        document.getElementById('agreement-status').innerText = 'NEGOTIATING';

        // Update Chart
        chartData.labels.push(`R${data.round}`);
        chartData.datasets[0].data.push(data.price);
        chart.update();

        // Update Chat
        addMessage(data.agent, data.message, data.action);

        // Reset manual messaging
        manualMessage.value = "";
    } else if (data.type === 'wait_for_human') {
        document.getElementById('agreement-status').innerText = `WAITING FOR ${data.agent.toUpperCase()}`;
        hitlControls.style.display = 'block';
        // Highlight whose turn it is
        hitlControls.style.borderColor = data.agent === 'supplier' ? 'var(--accent-blue)' : 'var(--accent-purple)';
    } else if (data.type === 'log') {
        console.log("SERVER:", data.message);
    }

    if (data.type === 'end') {
        startBtn.disabled = false;
        startBtn.innerText = 'RESTART SESSION';
        hitlControls.style.display = 'none';
        socket.close();
        document.getElementById('agreement-status').innerText = data.deal_price ? 'DEAL REACHED' : 'FAILED';
        if (data.deal_price) {
            document.getElementById('agreement-status').style.color = '#00ff00';
        } else {
            document.getElementById('agreement-status').style.color = '#ff4b2b';
        }
    }
}

startBtn.addEventListener('click', () => {
    // Reset
    chartData.labels = [];
    chartData.datasets[0].data = [];
    chart.update();
    chatStream.innerHTML = '';
    startBtn.disabled = true;
    startBtn.innerText = 'NEGOTIATING...';

    socket = new WebSocket('ws://localhost:8000/ws/negotiate');

    socket.onopen = () => {
        connStatus.innerText = 'API CONNECTED';
        connStatus.style.background = 'rgba(0, 255, 0, 0.1)';
        connStatus.style.color = '#00ff00';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateStats(data);

        if (data.type === 'turn') {
            // Update Chart
            chartData.labels.push(`R${data.round}`);
            chartData.datasets[0].data.push(data.price);
            chart.update();

            // Update Chat
            addMessage(data.agent, data.message, data.action);
        }

        if (data.type === 'end') {
            startBtn.disabled = false;
            startBtn.innerText = 'RESTART SESSION';
            socket.close();
        }
    };

    socket.onclose = () => {
        connStatus.innerText = 'API DISCONNECTED';
        connStatus.style.background = 'rgba(255, 0, 0, 0.1)';
        connStatus.style.color = '#ff4b2b';
    };
});

initChart();
