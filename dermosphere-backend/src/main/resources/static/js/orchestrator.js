document.addEventListener("DOMContentLoaded", () => {
    const skipBtn = document.getElementById('skip-sequence-btn');
    const introScreen = document.getElementById('intro-screen');
    const title = document.getElementById('vast-title');
    const deck = document.getElementById('interactive-deck');

    let timelineActive = true;

    // Master Timeline Fallback (2s loader + 5s intro + 2s shift)
    setTimeout(() => {
        if (timelineActive) deck.style.opacity = '1';
    }, 9000);

    // Skip Logic
    skipBtn.addEventListener('click', () => {
        timelineActive = false;
        introScreen.style.display = 'none';
        
        // Force title immediately to terminal position
        title.style.animation = 'none';
        title.style.top = '12%'; 
        title.style.opacity = '1'; 
        title.style.fontSize = '3rem';
        
        // Reveal deck smoothly
        setTimeout(() => deck.style.opacity = '1', 300);
    });
});

// Dialogue fading and Button reveal logic
window.triggerReveal = function(type) {
    const textNode = document.getElementById(`text-${type}`);
    const btnNode = document.getElementById(`btn-${type}`);
    
    textNode.style.opacity = '0';
    textNode.style.pointerEvents = 'none';
    
    setTimeout(() => {
        btnNode.classList.add('revealed');
    }, 500); // Wait for dialogue to fade before snapping the button in
};