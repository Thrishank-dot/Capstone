
document.addEventListener("DOMContentLoaded", () => {
    
    // 1. INPUT SANITIZATION
    document.querySelectorAll('.letter-only-input').forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-Z]/g, '');
        });
    });

    

    // 3. CAPTCHA GENERATION
    let currentCaptchaString = "";
    const canvas = document.getElementById('captcha-canvas');
    
    function renderCaptcha() {
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = "#FDFBF7";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        currentCaptchaString = "";
        
        for(let i=0; i<4; i++) {
            ctx.strokeStyle = `rgba(${Math.random()*255}, ${Math.random()*255}, ${Math.random()*255}, 0.5)`;
            ctx.beginPath();
            ctx.moveTo(Math.random()*canvas.width, Math.random()*canvas.height);
            ctx.lineTo(Math.random()*canvas.width, Math.random()*canvas.height);
            ctx.stroke();
        }

        for (let i = 0; i < 5; i++) {
            const char = chars.charAt(Math.floor(Math.random() * chars.length));
            currentCaptchaString += char;
            ctx.font = `bold ${20 + Math.random()*6}px monospace`;
            ctx.fillStyle = "#264653";
            ctx.save();
            ctx.translate(15 + (i * 20), 30 + (Math.random() * 8 - 4));
            ctx.rotate((Math.random() * 0.4) - 0.2);
            ctx.fillText(char, 0, 0);
            ctx.restore();
        }
    }
    renderCaptcha();

    // 4. LOGIN ROUTING
    const loginForm = document.getElementById('secure-login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputCaptcha = document.getElementById('auth-captcha').value.toUpperCase();
            const msgBox = document.getElementById('auth-message');
            
            if (inputCaptcha !== currentCaptchaString) {
                alert("Security Verification Failed. Generating new parameters.");
                renderCaptcha();
                document.getElementById('auth-captcha').value = '';
                return;
            }
            
            const uname = document.getElementById('auth-username').value;
            const pass = document.getElementById('auth-password').value;
            
            const payload = {
                username: uname,
                password: pass
            };

            try {
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const data = await response.json();
                    sessionStorage.setItem('dermoUsername', uname);
                    sessionStorage.setItem('dermoAuthToken', data.token);
                    sessionStorage.setItem('dermoLastActivity', Date.now().toString());
                    
                    window.location.replace('welcome.html');
                } else {
                    const errorText = await response.text();
                    msgBox.style.color = 'red';
                    msgBox.innerText = `Error: ${errorText || "Invalid Credentials."}`;
                    msgBox.style.display = 'block';
                    renderCaptcha();
                    document.getElementById('auth-captcha').value = '';
                }
            } catch (error) {
                msgBox.style.color = 'red';
                msgBox.innerText = "Gateway Connection Failed.";
                msgBox.style.display = 'block';
            }
        });
    }

    // 5. REGISTRATION PROTOCOL
    const signupForm = document.getElementById('secure-signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const msgBox = document.getElementById('auth-message');
            const p1 = document.getElementById('reg-password-initial').value;
            const p2 = document.getElementById('reg-password-confirm').value;
            
            if(p1 !== p2) {
                msgBox.style.color = 'red';
                msgBox.innerText = "Cryptographic keys do not match. Review invisible entry.";
                msgBox.style.display = 'block';
                return;
            }
            
            const payload = {
                username: document.getElementById('reg-username').value,
                email: document.getElementById('reg-email').value,
                password: p1,
                role: "PATIENT"
            };

            try {
                const response = await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    msgBox.style.color = 'green';
                    msgBox.innerText = "Registration successful! Redirecting to Auth Node...";
                    msgBox.style.display = 'block';
                    setTimeout(() => window.location.replace('login.html'), 2000);
                } else {
                    const errorText = await response.text();
                    msgBox.style.color = 'red';
                    msgBox.innerText = `Error: ${errorText}`;
                    msgBox.style.display = 'block';
                }
            } catch (error) {
                msgBox.style.color = 'red';
                msgBox.innerText = "Gateway Connection Failed.";
                msgBox.style.display = 'block';
            }
        });
    }
});