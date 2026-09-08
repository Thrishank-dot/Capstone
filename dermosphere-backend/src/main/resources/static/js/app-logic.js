let systemLocked = false; 
let globalInactivityTimer;
let isPollingSecurity = false;
const INACTIVITY_LIMIT_MS = 300000;

function resetInactivityClock() {
    clearTimeout(globalInactivityTimer);
    if (!systemLocked) {
        globalInactivityTimer = setTimeout(() => {
            triggerLogout(true);
        }, INACTIVITY_LIMIT_MS);
    }
}
['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(evt => {
    document.addEventListener(evt, resetInactivityClock);
});
resetInactivityClock();

function checkAndBypassAdminMetrics() {
    fetch('/api/v1/security/metrics-status', {
        headers: { 'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'GRANTED') {
            const reqBlock = document.getElementById('request-block');
            const metrics = document.getElementById('classified-metrics');
            if (reqBlock) reqBlock.style.display = 'none';
            if (metrics) metrics.style.filter = 'blur(0px)';
        }
    })
    .catch(err => console.error(err));
}

function routeTo(targetPaneId, evt) {
    if (systemLocked) {
        alert("CRITICAL: Neural processing sequence engaged. Navigation locked until completion.");
        return;
    }
    document.querySelectorAll('.pane-view').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    
    const targetPane = document.getElementById(targetPaneId);
    if (targetPane) targetPane.classList.add('active');
    
    const targetElement = evt ? evt.target : (window.event ? window.event.target : null);
    if (targetElement && targetElement.classList) {
        targetElement.classList.add('active');
    }

    if (targetPaneId === 'pane-hide') {
        checkAndBypassAdminMetrics();
    }
}

async function initiateVisualScanSequence() {
    const fileInput = document.getElementById('lesion-upload');
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Input vector empty. Please supply a dermatological image.");
        return;
    }

    systemLocked = true;
    document.getElementById('processing-matrix').style.display = 'block';
    document.getElementById('final-results').style.display = 'none';
    
    const readout = document.getElementById('status-readout');
    const scannerBox = document.getElementById('scanner-box');
    const scannerImg = document.getElementById('scanner-preview');
    const scannerGrid = document.getElementById('scanner-grid');
    const scannerLaser = document.getElementById('scanner-laser');
    
    scannerImg.src = URL.createObjectURL(fileInput.files[0]);
    scannerBox.style.display = 'block';
    
    readout.innerText = "> Phase 1: Uploading payload to Triage API...";
    scannerGrid.style.opacity = '1';
    scannerImg.style.filter = 'grayscale(0%)'; 
    scannerImg.style.opacity = '1';
    scannerLaser.style.animationDuration = '0.5s'; 

    const token = sessionStorage.getItem('dermoAuthToken');
    if (!token || token.trim() === "") {
        readout.innerText = "> [ERROR] Authentication token missing. Please re-login.";
        systemLocked = false;
        scannerBox.style.display = 'none';
        return;
    }

    const activePatientId = sessionStorage.getItem('dermoPatientId') || sessionStorage.getItem('dermoUserId') || "1";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("patient_id", activePatientId); 

    try {
        readout.innerText = "> Phase 2: Awaiting Neural Inference Engine...";
        
        const response = await fetch('/api/v1/triage/upload', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token
            },
            body: formData
        });

        const responseText = await response.text();

        if (!response.ok) {
            try {
                const errorJson = JSON.parse(responseText);
                readout.innerText = `> [VALIDATION FAILED] ${errorJson.message}`;
            } catch(e) {
                readout.innerText = `> [ERROR] ${responseText}`;
            }
            readout.style.color = "var(--accent-red)";
            scannerBox.style.display = 'none';
            return;
        }

        const data = JSON.parse(responseText);

        readout.innerText = "> Sequence Complete.";
        scannerBox.style.display = 'none';
        
        document.getElementById('final-results').style.display = 'block';
        document.getElementById('res-classification').innerText = `Prediction: ${data.predictedClass}`;
        document.getElementById('res-classification').style.color = "var(--med-coral)";
        document.getElementById('res-accuracy').innerText = `Calculated Confidence: ${(data.confidenceScore * 100).toFixed(2)}% | Tier: ${data.triageTier}`;
        
        appendHistoryLedger(data.predictedClass, `${(data.confidenceScore * 100).toFixed(2)}%`);
        
    } catch (error) {
        console.error("Frontend Exception:", error);
        readout.innerText = `> [CRITICAL] Frontend Error: ${error.message}`;
        scannerBox.style.display = 'none';
    } finally {
        systemLocked = false;
        scannerLaser.style.animationDuration = '2.5s'; 
        scannerGrid.style.opacity = '0';
        resetInactivityClock();
    }
}

function appendHistoryLedger(diagnosis, accuracy) {
    const container = document.getElementById('history-container');
    if (!container) return;
    if (container.children.length >= 10) container.removeChild(container.lastChild);
    
    const record = document.createElement('div');
    record.className = 'history-record';
    const timestamp = new Date().toLocaleTimeString();
    record.innerHTML = `
        <div>
            <span style="font-family: monospace; color: var(--text-secondary); margin-right: 15px;">[${timestamp}]</span>
            <strong>${diagnosis}</strong> (Confidence: ${accuracy})
        </div>
        <button class="clinical-btn" style="background: transparent; border: 1px solid var(--med-coral); color: var(--med-coral); padding: 8px 16px;" onclick="this.parentElement.remove()">Delete</button>
    `;
    container.prepend(record);
}

const valFile = document.getElementById('validation-file');
if (valFile) {
    valFile.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const resultElem = document.getElementById('validation-result');
            if (resultElem) resultElem.style.display = 'block';
        }
    });
}
function transferValidationToEngine() {
    const valInput = document.getElementById('validation-file');
    const mainInput = document.getElementById('lesion-upload');
    if (valInput && mainInput && valInput.files.length > 0) {
        mainInput.files = valInput.files;
    }
    const resultElem = document.getElementById('validation-result');
    if (resultElem) resultElem.style.display = 'none';
    routeTo('pane-home');
    initiateVisualScanSequence();
}

function initiateClearanceRequest() {
    const log = document.getElementById('clearance-log');
    if (!log) return;
    log.innerText = "> Transmitting authorization packet to Admin node...";
    log.style.color = "var(--med-teal-deep)";

    fetch('/api/v1/security/request-metrics-access', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken')
        }
    })
    .then(response => response.text())
    .then(responseText => {
        log.innerText = "> [PENDING] Request transmitted. Awaiting Admin Overlord Approval...";
        log.style.color = "var(--med-peach)";
        
        isPollingSecurity = true;
        pollSecurityStatus(log); 
    })
    .catch(error => {
        log.innerText = "> [ERROR] Connection to Admin Node Refused.";
        log.style.color = "red";
    });
}

function pollSecurityStatus(logElement) {
    if (!isPollingSecurity) return;

    fetch('/api/v1/security/metrics-status', {
        headers: {
            'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken')
        }
    })
        .then(res => res.text())
        .then(responseText => {
            try {
                const statusData = JSON.parse(responseText);
                if (statusData.status === 'GRANTED') {
                    isPollingSecurity = false;
                    logElement.innerText = "> [ACCESS GRANTED] Clearance Level ALPHA Authorized.";
                    logElement.style.color = "green";
                    const metrics = document.getElementById('classified-metrics');
                    if (metrics) metrics.style.filter = "blur(0px)";
                    activateSecurityProtocols();
                } else if (statusData.status === 'REJECTED' || statusData.status === 'REVOKED') {
                    isPollingSecurity = false;
                    logElement.innerText = "> [ACCESS DENIED] Admin Overlord rejected clearance.";
                    logElement.style.color = "red";
                } else {
                    setTimeout(() => pollSecurityStatus(logElement), 3000);
                }
            } catch(e) {
                setTimeout(() => pollSecurityStatus(logElement), 3000);
            }
        })
        .catch(err => {
            isPollingSecurity = false;
            logElement.innerText = "> [ERROR] Polling connection severed.";
            logElement.style.color = "red";
        });
}

function activateSecurityProtocols() {
    const metrics = document.getElementById('classified-metrics');
    if (metrics) {
        metrics.addEventListener('contextmenu', e => e.preventDefault());
    }
    window.addEventListener('blur', () => {
        const vault = document.getElementById('classified-metrics');
        if (vault) {
            vault.style.transition = 'none'; 
            vault.style.filter = 'blur(30px)';
        }
        document.title = "⚠️ SECURITY VIOLATION ⚠️";
        if (navigator.clipboard) {
            navigator.clipboard.writeText("DermoSphere Security: Unauthorized extraction attempt logged.");
        }
    });
    window.addEventListener('focus', () => {
        const vault = document.getElementById('classified-metrics');
        if (vault) {
            vault.style.transition = 'filter 1s ease'; 
            vault.style.filter = 'blur(0px)';
        }
        document.title = "DermoSphere | Portal";
    });
}

window.triggerLogout = function(forced = false) {
    if (systemLocked && !forced) {
        alert("CRITICAL ERROR: Cannot sever neural link while processing is active.");
        return;
    }
    clearTimeout(globalInactivityTimer);
    isPollingSecurity = false; 
    
    document.body.innerHTML = `
        <div style="height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; background: var(--med-teal-deep); color: white;">
            <div class="medical-cross-core" style="margin-bottom: 2rem; background: var(--med-coral);"></div>
            <h1 style="font-family: monospace; letter-spacing: 3px;">Severing Neural Link...</h1>
        </div>
    `;
    setTimeout(() => {
        sessionStorage.clear();
        window.location.replace('index.html');
    }, 3000);
};