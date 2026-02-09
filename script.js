
// Typing Animation

const textSequences = [
    'that identifies conversion barriers.',
    'to boost your growth.',
    'powered by advanced AI.',
    'for business success.'
];

let currentIndex = 0;
let charIndex = 0;
let isDeleting = false;

function typeText() {
    const typingElement = document.querySelector('.typing-text');
    const currentText = textSequences[currentIndex];
    
    if (!isDeleting) {
        // Typing out
        if (charIndex < currentText.length) {
            typingElement.innerHTML += currentText[charIndex];
            charIndex++;
            setTimeout(typeText, 50);
        } else {
            // Pause before deleting
            setTimeout(() => {
                isDeleting = true;
                typeText();
            }, 2000);
        }
    } else {
        // Deleting
        if (charIndex > 0) {
            typingElement.innerHTML = currentText.substring(0, charIndex - 1);
            charIndex--;
            setTimeout(typeText, 30);
        } else {
            // Move to next text
            isDeleting = false;
            currentIndex = (currentIndex + 1) % textSequences.length;
            setTimeout(typeText, 500);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    typeText();
});
// Mobile Menu Toggle
const menuBtn = document.getElementById('menu-btn');
const nav = document.querySelector('nav');

menuBtn.addEventListener('click', () => {
    nav.classList.toggle('active');
});

// Close menu when a link is clicked
document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', () => {
        nav.classList.remove('active');
    });
});

// Back to Top Button
const backToTop = document.getElementById('back-to-top');

window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});

backToTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Scroll Animation for Sections
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);


// Observe all sections
document.querySelectorAll('.content-section').forEach(section => {
    observer.observe(section);
});


// Contact Form Submission

const contactForm = document.getElementById('contact-form');
const formStatus = document.getElementById('form-status');

contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = contactForm.querySelector('input[name="name"]').value;
    const email = contactForm.querySelector('input[name="email"]').value;
    const message = contactForm.querySelector('textarea[name="message"]').value;

    // Simulate form submission with delay
    contactForm.classList.add('form-submitted');
    formStatus.textContent = 'Sending your message...';
    formStatus.style.opacity = '1';

    setTimeout(() => {
        formStatus.innerHTML = `<span style="color: #4caf50;">✓ Message sent successfully! We'll get back to you soon.</span>`;
        
        // Reset form after 3 seconds
        setTimeout(() => {
            contactForm.reset();
            contactForm.classList.remove('form-submitted');
            formStatus.style.opacity = '0';
        }, 3000);
    }, 1500);

    console.log('Form Data:', { name, email, message });
});

// Analyzer Form Submission
const analyzerForm = document.getElementById('analyzer-form');
const analyzerStatus = document.getElementById('analyzer-status');

analyzerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = document.getElementById('website-url').value;
    const email = document.getElementById('email').value;
    const selectedAnalysis = Array.from(document.querySelectorAll('.analysis-options input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);

    if (selectedAnalysis.length === 0) {
        analyzerStatus.textContent = 'Please select at least one analysis type.';
        analyzerStatus.classList.remove('success');
        analyzerStatus.classList.add('error');
        analyzerStatus.style.opacity = '1';
        analyzerStatus.style.display = 'block';
        return;
    }

    // Show loading message
    analyzerStatus.textContent = 'Analyzing your website... This may take a few moments (email sending included).';
    analyzerStatus.classList.remove('error');
    analyzerStatus.classList.add('success');
    
    analyzerStatus.style.opacity = '1';
    analyzerStatus.style.display = 'block';

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

    // Call backend API
    try {
        console.log('Sending request to backend...');
        console.log('URL:', url);
        console.log('Email:', email);
        
        const response = await fetch('http://127.0.0.1:5000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                email: email
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        console.log('Response received:', response.status);
        console.log('Response ok:', response.ok);
        
        const data = await response.json();
        console.log('Response data:', data);

        if (response.ok) {
            console.log('Analysis successful, showing success message');
            // Show success message prominently
            const successHTML = `
                <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <span style="color: #155724; font-size: 16px; font-weight: bold; display: block; margin-bottom: 10px;">
                        ✓ SUCCESS! Analysis Complete
                    </span>
                    <p style="color: #155724; margin: 0; font-size: 14px;">
                        A detailed PDF report with recommendations has been sent to <strong>${email}</strong>
                    </p>
                </div>
            `;
            console.log('Setting HTML:', successHTML);
            analyzerStatus.innerHTML = successHTML;
            analyzerStatus.style.display = 'block';
            analyzerStatus.style.opacity = '1';
            console.log('Success message displayed');
            
            // Scroll to message
            setTimeout(() => {
                analyzerStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
            
            // Keep message visible for 30 seconds before clearing the form
            setTimeout(() => {
                analyzerForm.reset();
                // Don't hide the message - keep it visible
            }, 30000);
        } else {
            console.log('Error response from backend');
            analyzerStatus.innerHTML = `
                <div style="background: #f8d7da; border: 2px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <span style="color: #721c24; font-size: 14px; display: block; margin-bottom: 5px; font-weight: bold;">
                        ✗ Error: ${data.error || 'Failed to analyze website'}
                    </span>
                </div>
            `;
            analyzerStatus.style.display = 'block';
            analyzerStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } catch (error) {
        console.error('Fetch error:', error);
        console.error('Error message:', error.message);
        analyzerStatus.innerHTML = `
            <div style="background: #f8d7da; border: 2px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <span style="color: #721c24; font-size: 14px; display: block; margin-bottom: 5px; font-weight: bold;">
                    ✗ Error connecting to backend
                </span>
                <p style="color: #721c24; margin: 0; font-size: 12px;">
                    Make sure the Flask server is running on port 5000<br>
                    Error: ${error.message}
                </p>
            </div>
        `;
        analyzerStatus.style.display = 'block';
        analyzerStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    console.log('Analyzer Data:', { url, email, selectedAnalysis });                                                                                                                                              
});

// Lock/Prevent Smooth Scroll Behavior on Pre-filled Form Fields
document.querySelectorAll('input, textarea').forEach(field => {
    field.addEventListener('focus', () => {
        document.documentElement.style.scrollBehavior = 'auto';
    });
    field.addEventListener('blur', () => {
        document.documentElement.style.scrollBehavior = 'smooth';
    });
});

// Initialize Page
console.log('✓ WebAnalyzer script loaded successfully!');

