if (!sessionStorage.getItem('dermoAuthToken')) {
    window.location.replace('admin-login.html');
}

function logoutAdmin() {
    sessionStorage.removeItem('dermoAuthToken');
    window.location.replace('admin-login.html');
}

let chartsInitialized = false;
let isObfuscated = true;
let currentDataset = [];

function switchTab(tabId, evt) {
    ['sql-tab', 'matrix-tab', 'sec-tab'].forEach(id => {
        const pane = document.getElementById(id);
        if (pane) {
            pane.className = (id === tabId) ? 'tab-active' : 'tab-hidden';
        }
    });
    
    document.querySelectorAll('.nav-icon').forEach(el => el.classList.remove('active'));
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add('active');
    } else if (evt && evt.target) {
        evt.target.classList.add('active');
    }
    
    if (tabId === 'matrix-tab' && !chartsInitialized) initChartMatrix();
    if (tabId === 'sec-tab') fetchPendingRequests();
}

function initChartMatrix() {
    chartsInitialized = true;
    const matrixGrid = document.getElementById('chart-matrix');
    if (!matrixGrid) return;
    matrixGrid.replaceChildren();
    
    for (let i = 1; i <= 20; i++) {
        const card = document.createElement('div');
        card.className = 'chart-card';
        card.innerHTML = `<canvas id="telemetryChart${i}"></canvas>`;
        matrixGrid.appendChild(card);
        
        const canvasElem = document.getElementById(`telemetryChart${i}`);
        if (canvasElem) {
            const ctx = canvasElem.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(10).fill(''),
                    datasets: [{ data: Array(10).fill(0).map(() => Math.random() * 100), borderColor: '#06b6d4', tension: 0.4 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }
    }
}

async function fetchPendingRequests() {
    try {
        const response = await fetch('/api/v1/admin/security/pending-requests', {
            headers: { 'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken') }
        });
        if (!response.ok) return;
        const data = await response.json();
        const tbody = document.getElementById('clearance-body');
        if (!tbody) return;
        tbody.replaceChildren();
        
        (data.requests || []).forEach(req => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${req.username}</td>
                <td>${req.status}</td>
                <td><button onclick="resolveClearance('${req.id}', 'GRANTED')" class="btn-execute">APPROVE</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to fetch clearance queue:", err);
    }
}

async function resolveClearance(requestId, actionStatus) {
    try {
        const response = await fetch(`/api/v1/admin/security/resolve/${requestId}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken') 
            },
            body: JSON.stringify({ status: actionStatus })
        });
        if (response.ok) {
            fetchPendingRequests();
        }
    } catch (err) {
        console.error("Failed to resolve clearance request:", err);
    }
}

function updateSyntax() {
    const textElem = document.getElementById('sql-input');
    const highlightElem = document.getElementById('highlight-layer');
    if (!textElem || !highlightElem) return;
    
    const text = textElem.value;
    let highlighted = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|DROP|ALTER|AND|OR|JOIN|INNER|LEFT|ON|GROUP BY|ORDER BY|LIMIT)\b/gi, '<span class="sql-keyword">$&</span>')
        .replace(/\b(COUNT|MAX|MIN|AVG|SUM)\b/gi, '<span class="sql-function">$&</span>')
        .replace(/('.*?')/g, '<span class="sql-string">$&</span>');
        
    highlightElem.innerHTML = highlighted + '<br>'; 
}

const sqlInputElem = document.getElementById('sql-input');
if (sqlInputElem) {
    sqlInputElem.addEventListener('scroll', function() {
        const highlightElem = document.getElementById('highlight-layer');
        if (highlightElem) {
            highlightElem.scrollTop = this.scrollTop;
            highlightElem.scrollLeft = this.scrollLeft;
        }
    });
}

function toggleObfuscation() {
    isObfuscated = !isObfuscated;
    const btn = document.getElementById('obfuscate-btn');
    if (btn) {
        btn.innerText = `Mask Data: ${isObfuscated ? 'ON' : 'OFF'}`;
        btn.style.color = isObfuscated ? 'var(--accent-cyan)' : 'var(--accent-red)';
        btn.style.borderColor = isObfuscated ? 'var(--accent-cyan)' : 'var(--accent-red)';
    }
    renderTable(currentDataset);
}

function obfuscateString(str) {
    if (!str || str.length < 3) return "***";
    if (str.includes('@')) {
        const parts = str.split('@');
        return parts[0].charAt(0) + "***@" + parts[1];
    }
    return str.charAt(0) + "***" + str.charAt(str.length - 1);
}

async function executeSQL() {
    const queryElem = document.getElementById('sql-input');
    if (!queryElem) return;
    const query = queryElem.value;
    
    try {
        const response = await fetch('/api/v1/admin/workbench/execute-sql', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken') 
            },
            body: JSON.stringify({ query: query })
        });
        const result = await response.json();
        
        if (response.status === 403 || response.status === 401) {
            alert("SECURITY LOCKOUT: " + (result.error || "Unauthorized Request"));
            return;
        }
        if (result.data) {
            currentDataset = result.data;
            renderTable(currentDataset);
        }
    } catch (error) { console.error("Execution failed:", error); }
}

function renderTable(dataArray) {
    const table = document.getElementById('sql-results-table');
    if (!table) return;
    table.replaceChildren();
    if (!dataArray || dataArray.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.style.textAlign = 'center';
        td.style.color = '#64748b';
        td.textContent = 'No records returned.';
        tr.appendChild(td);
        table.appendChild(tr);
        return;
    }
    const headers = Object.keys(dataArray[0]);
    const headerRow = document.createElement('tr');
    headers.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h.toUpperCase();
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    
    dataArray.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(key => {
            let val = row[key];
            if (isObfuscated && (key.includes('name') || key.includes('email') || key.includes('ip'))) {
                val = obfuscateString(String(val));
            }
            const td = document.createElement('td');
            td.textContent = val !== null && val !== undefined ? val : 'NULL';
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
}
