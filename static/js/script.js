

// Function to handle the visibility of elements on scroll (fade, slide, bounce)
function revealOnScroll() {
    let elements = document.querySelectorAll('.fade-in-on-scroll, .slide-up-on-scroll, .bounce-on-scroll');
    elements.forEach(element => {
        let position = element.getBoundingClientRect().top;
        let windowHeight = window.innerHeight;
        if (position < windowHeight - 100) {
            element.classList.add('visible');
        }
    });
}
document.addEventListener('DOMContentLoaded', () => {
const circles = document.querySelectorAll('.circle');

function animateCircle(circle) {
    const percent = parseInt(circle.getAttribute('data-percent'), 10);
    if (isNaN(percent) || percent < 0 || percent > 100) {
        console.error('Invalid data-percent value:', circle.getAttribute('data-percent'));
        return; // Skip invalid circle
    }

    let currentPercent = 0;

    function updateAnimation() {
        if (currentPercent <= percent) {
            const degrees = (360 * currentPercent) / 100;
            circle.style.backgroundImage = `conic-gradient(#831238 ${degrees}deg, #7b7b7b4c 0deg)`;
            circle.querySelector('.percent').textContent = `${currentPercent}%`;
            currentPercent++;
            requestAnimationFrame(updateAnimation);
        }
    }

    updateAnimation();
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCircle(entry.target);
            observer.unobserve(entry.target); // Stop observing after animation starts
        }
    });
}, { threshold: 1.0 }); // Animation triggers only when the circle is fully visible

circles.forEach(circle => observer.observe(circle));
});
document.addEventListener('DOMContentLoaded', () => {
const statBoxes = document.querySelectorAll('.stat-box');

function animateFill(statBox) {
    const percent = parseInt(statBox.getAttribute('data-percent'), 10);
    if (isNaN(percent) || percent < 0 || percent > 100) {
        console.error('Invalid data-percent value:', statBox.getAttribute('data-percent'));
        return;
    }

    const fillElement = statBox.querySelector('.fill');
    fillElement.style.height = `${percent}%`;
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateFill(entry.target);
            observer.unobserve(entry.target); // Stop observing after animation starts
        }
    });
}, { threshold: 0.5 }); // Animation triggers when 50% of the section is visible

statBoxes.forEach(statBox => observer.observe(statBox));
});


// Trigger the revealOnScroll function when the page is scrolled or loaded
window.addEventListener('scroll', revealOnScroll);
document.addEventListener('DOMContentLoaded', revealOnScroll);


// fqa
document.addEventListener("DOMContentLoaded", function () {
    const faqs = document.querySelectorAll(".faq");

    faqs.forEach(faq => {
        const question = faq.querySelector(".faq-question");
        const answer = faq.querySelector(".faq-answer");
        const toggleBtn = faq.querySelector(".toggle-btn");

        question.addEventListener("click", () => {
            const isOpen = answer.style.maxHeight;

            // Close all answers before opening a new one (optional)
            document.querySelectorAll(".faq-answer").forEach(ans => {
                ans.style.maxHeight = null;
                ans.style.padding = "0 10px";
            });
            document.querySelectorAll(".toggle-btn").forEach(btn => btn.textContent = "+");

            if (!isOpen || isOpen === "0px") {
                answer.style.maxHeight = answer.scrollHeight + "px";
                answer.style.padding = "10px 10px";
                toggleBtn.textContent = "-";
            }
        });
    });
});
