    // ============================================
    // SITE-WIDE THEME
    // ============================================

    (function initializeSiteTheme() {
        const isProUser = document.body.dataset.proUser !== 'false';
        const allowedThemes = isProUser ? ['film', 'professional', 'normal', 'ai'] : ['film', 'normal'];
        const savedTheme = localStorage.getItem('amax-site-theme') || localStorage.getItem('amax-home-theme') || 'normal';
        const selectedTheme = allowedThemes.includes(savedTheme) ? savedTheme : 'normal';

        document.body.classList.remove('theme-film', 'theme-professional', 'theme-normal', 'theme-ai');
        document.body.classList.add(`theme-${selectedTheme}`);
        localStorage.setItem('amax-site-theme', selectedTheme);
    })();

    (function initializeSiteLanguage() {
        const translations = {
            en: {
                features: 'Features', about: 'About', explore: 'Explore', pricing: 'Pricing', helpDesk: 'Help Desk', contact: 'Contact', profile: 'Profile', chat: 'Chat', logout: 'Logout', login: 'Login', signUp: 'Sign Up', theme: 'Theme', chooseTheme: 'Choose theme', filmy: 'Filmy', professional: 'Professional', normal: 'Normal', aiTheme: 'AI Theme', language: 'Language', deepResearch: 'Deep Research', openExperience: 'OpenAI-style experience', nextGen: 'NEXT-GEN AI EXPERIENCE', heroTitle: 'Build smarter with AMAX AI', getStarted: 'Get Started Free', pages: 'Pages',
                home: 'Home', dashboard: 'Dashboard', settings: 'Settings', sendMessage: 'Send Message', back: 'Back', goToChat: 'Go to Chat', goToHome: 'Go to Home',
                welcomeToAmax: 'Welcome to AMAX!', welcomeMessage: "Ask me anything and I'll help you out.",
                conversations: 'Conversations', newChat: 'New Chat', oldChats: 'Old Chats', pinChat: 'Pin chat', viewProfile: 'View profile', clearHistory: 'Clear history',
                openConversations: 'Open conversations', closeConversations: 'Close conversations', renameConversation: 'Rename conversation', deleteConversation: 'Delete conversation',
                appearance: 'Appearance', light: 'Light', dark: 'Dark', wallpaper: 'Wallpaper', removeWallpaper: 'Remove wallpaper', defaultWallpaper: 'Default wallpaper',
                typeMessage: 'Type your message here...', attachImage: 'Attach an image', typeVoice: 'Type with your voice', removeImage: 'Remove image',
                amaxThinking: 'AMAX is thinking', proUnlocked: 'Pro Unlocked', upgradeToPro: 'Upgrade to Pro', proPrice: 'Pro ₹2',
                dashboardTitle: 'Dashboard', welcomeBack: 'Welcome back', aiPrompts: 'AI prompts', tasksDone: 'Tasks done', focusScore: 'Focus score', activeProjects: 'Active projects',
                savedNotes: 'Saved notes', productivity: 'Productivity', priorities: 'Priorities', quickLinks: 'Quick Links',
                'AMAX is thinking': 'AMAX is thinking', 'Welcome back': 'Welcome back', 'Pro Unlocked': 'Pro Unlocked', 'Upgrade to Pro': 'Upgrade to Pro'
            },
            mr: {
                features: 'वैशिष्ट्ये', about: 'आमच्याबद्दल', explore: 'पहा', pricing: 'किंमत', helpDesk: 'मदत केंद्र', contact: 'संपर्क', profile: 'प्रोफाइल', chat: 'चॅट', logout: 'लॉगआउट', login: 'लॉगिन', signUp: 'साइन अप', theme: 'थीम', chooseTheme: 'थीम निवडा', filmy: 'फिल्मी', professional: 'व्यावसायिक', normal: 'सामान्य', aiTheme: 'AI थीम', language: 'भाषा', deepResearch: 'सखोल संशोधन', openExperience: 'AI अनुभव', nextGen: 'नवीन AI अनुभव', heroTitle: 'AMAX AI सोबत अधिक हुशारीने काम करा', getStarted: 'मोफत सुरू करा', pages: 'पृष्ठे',
                home: 'मुख्यपृष्ठ', dashboard: 'डॅशबोर्ड', settings: 'सेटिंग्ज', sendMessage: 'संदेश पाठवा', back: 'मागे', goToChat: 'चॅटवर जा', goToHome: 'मुख्यपृष्ठावर जा',
                welcomeToAmax: 'AMAX वर आपले स्वागत आहे!', welcomeMessage: 'माझ्याशी काहीही विचारा, मी मदत करेन.',
                conversations: 'चर्चा', newChat: 'नवीन चॅट', oldChats: 'पूर्वीची चॅटे', pinChat: 'चॅट पिन करा', viewProfile: 'प्रोफाइल पहा', clearHistory: 'इतिहास साफ करा',
                openConversations: 'चर्चा उघडा', closeConversations: 'चर्चा बंद करा', renameConversation: 'चर्चा नाव बदला', deleteConversation: 'चर्चा हटवा',
                appearance: 'अpearance', light: 'उजळ', dark: 'गडद', wallpaper: 'वॉलपेपर', removeWallpaper: 'वॉलपेपर काढा', defaultWallpaper: 'डीफॉल्ट वॉलपेपर',
                typeMessage: 'तुमचा संदेश येथे टाइप करा...', attachImage: 'चित्र जोडा', typeVoice: 'तुमच्या आवाजाने टाइप करा', removeImage: 'चित्र काढा',
                amaxThinking: 'AMAX विचार करत आहे', proUnlocked: 'प्रो अनलॉक', upgradeToPro: 'प्रोमध्ये अपग्रेड करा', proPrice: 'प्रो ₹2',
                dashboardTitle: 'डॅशबोर्ड', welcomeBack: 'पुन्हा स्वागत', aiPrompts: 'AI प्रॉम्प्ट्स', tasksDone: 'पूर्ण कामे', focusScore: 'फोकस स्कोअर', activeProjects: 'सक्रिय प्रोजेक्ट्स',
                savedNotes: 'जतन केलेली नोंदी', productivity: 'उत्पादकता', priorities: 'प्राधान्ये', quickLinks: 'जलद दुवे'
            },
            hi: {
                features: 'विशेषताएँ', about: 'हमारे बारे में', explore: 'देखें', pricing: 'कीमत', helpDesk: 'सहायता केंद्र', contact: 'संपर्क', profile: 'प्रोफ़ाइल', chat: 'चैट', logout: 'लॉगआउट', login: 'लॉगिन', signUp: 'साइन अप', theme: 'थीम', chooseTheme: 'थीम चुनें', filmy: 'फ़िल्मी', professional: 'प्रोफेशनल', normal: 'सामान्य', aiTheme: 'AI थीम', language: 'भाषा', deepResearch: 'गहन शोध', openExperience: 'AI अनुभव', nextGen: 'नई पीढ़ी का AI अनुभव', heroTitle: 'AMAX AI के साथ बेहतर काम करें', getStarted: 'मुफ्त शुरू करें', pages: 'पेज',
                home: 'होम', dashboard: 'डैशबोर्ड', settings: 'सेटिंग्स', sendMessage: 'संदेश भेजें', back: 'वापस', goToChat: 'चैट पर जाएँ', goToHome: 'होम पर जाएँ',
                welcomeToAmax: 'AMAX में आपका स्वागत है!', welcomeMessage: 'मुझसे कुछ भी पूछें, मैं मदद करूँगा।',
                conversations: 'बातचीत', newChat: 'नई चैट', oldChats: 'पुरानी चैट', pinChat: 'चैट पिन करें', viewProfile: 'प्रोफ़ाइल देखें', clearHistory: 'इतिहास साफ़ करें',
                openConversations: 'बातचीत खोलें', closeConversations: 'बातचीत बंद करें', renameConversation: 'चैट का नाम बदलें', deleteConversation: 'चैट हटाएँ',
                appearance: 'दिखावट', light: 'हल्का', dark: 'गहरा', wallpaper: 'वालपेपर', removeWallpaper: 'वालपेपर हटाएँ', defaultWallpaper: 'डिफ़ॉल्ट वालपेपर',
                typeMessage: 'अपना संदेश यहाँ लिखें...', attachImage: 'चित्र जोड़ें', typeVoice: 'अपने आवाज से लिखें', removeImage: 'चित्र हटाएँ',
                amaxThinking: 'AMAX सोच रहा है', proUnlocked: 'प्रो अनलॉक', upgradeToPro: 'प्रो में अपग्रेड करें', proPrice: 'प्रो ₹2',
                dashboardTitle: 'डैशबोर्ड', welcomeBack: 'फिर से स्वागत है', aiPrompts: 'AI प्रॉम्प्ट्स', tasksDone: 'पूर्ण कार्य', focusScore: 'फ़ोकस स्कोर', activeProjects: 'सक्रिय प्रोजेक्ट्स',
                savedNotes: 'सहेजे गए नोट्स', productivity: 'उत्पादकता', priorities: 'प्राथमिकताएँ', quickLinks: 'त्वरित लिंक'
            },
            ta: {
                features: 'அம்சங்கள்', about: 'எங்களைப் பற்றி', explore: 'ஆராயுங்கள்', pricing: 'விலை', helpDesk: 'உதவி மையம்', contact: 'தொடர்பு', profile: 'சுயவிவரம்', chat: 'அரட்டை', logout: 'வெளியேறு', login: 'உள்நுழைவு', signUp: 'பதிவு செய்க', theme: 'தீம்', chooseTheme: 'தீமைத் தேர்ந்தெடுக்கவும்', filmy: 'திரைப்படம்', professional: 'தொழில்முறை', normal: 'சாதாரணம்', aiTheme: 'AI தீம்', language: 'மொழி', deepResearch: 'ஆழமான ஆய்வு', openExperience: 'AI அனுபவம்', nextGen: 'புதிய தலைமுறை AI அனுபவம்', heroTitle: 'AMAX AI மூலம் சிறப்பாக செயல்படுங்கள்', getStarted: 'இலவசமாக தொடங்குங்கள்', pages: 'பக்கங்கள்',
                home: 'முகப்பு', dashboard: 'டாஷ்போர்டு', settings: 'அமைப்புகள்', sendMessage: 'செய்தி அனுப்பு', back: 'பின்னால்', goToChat: 'அரட்டைக்குச் செல்லவும்', goToHome: 'முகப்புக்குச் செல்லவும்',
                welcomeToAmax: 'AMAXக்கு வருக!', welcomeMessage: 'என்னையும் கேளுங்கள், நான் உதவுவேன்.',
                conversations: 'உரையாடல்கள்', newChat: 'புதிய அரட்டை', oldChats: 'பழைய அரட்டைகள்', pinChat: 'அரட்டையைப் பின் செய்யவும்', viewProfile: 'சுயவிவரத்தைப் பார்க்கவும்', clearHistory: 'வரலாற்றை அழிக்கவும்',
                openConversations: 'உரையாடல்களைத் திற', closeConversations: 'உரையாடல்களை மூடு', renameConversation: 'அரட்டை பெயரை மாற்று', deleteConversation: 'அரட்டையை நீக்கு',
                appearance: 'தோற்றம்', light: 'ஒளி', dark: 'இருள்', wallpaper: 'வால்பேப்பர்', removeWallpaper: 'வால்பேப்பரை அகற்று', defaultWallpaper: 'இயல்புநிலை வால்பேப்பர்',
                typeMessage: 'உங்கள் செய்தியை இங்கே தட்டச்சு செய்யுங்கள்...', attachImage: 'படம் இணை', typeVoice: 'குரல் மூலம் தட்டச்சு செய்யுங்கள்', removeImage: 'படத்தை நீக்கு',
                amaxThinking: 'AMAX சிந்திக்கிறது', proUnlocked: 'ப்ரோ திறக்கப்பட்டது', upgradeToPro: 'ப்ரோவுக்கு மேம்படுத்து', proPrice: 'ப்ரோ ₹2',
                dashboardTitle: 'டாஷ்போர்டு', welcomeBack: 'மீண்டும் வரவேற்கிறோம்', aiPrompts: 'AI தூண்டுதல்கள்', tasksDone: 'முடிக்கப்பட்ட பணிகள்', focusScore: 'கவனம் மதிப்பெண்', activeProjects: 'செயலில் உள்ள திட்டங்கள்',
                savedNotes: 'சேமித்த குறிப்புகள்', productivity: 'உற்பத்தித்திறன்', priorities: 'முன்னுரிமைகள்', quickLinks: 'விரைவு இணைப்புகள்'
            }
        };

        const selectedLanguage = localStorage.getItem('amax-site-language') || 'en';

        const applyLanguage = language => {
            const dictionary = translations[language] || translations.en;
            document.documentElement.lang = language;

            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.dataset.i18n;
                if (dictionary[key]) {
                    element.textContent = dictionary[key];
                }
            });

            const translatableTextMap = new Map(Object.entries(dictionary));
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
                acceptNode(node) {
                    const parent = node.parentElement;
                    if (!parent || parent.closest('[data-no-translate]')) return NodeFilter.FILTER_REJECT;
                    if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                }
            });

            while (walker.nextNode()) {
                const node = walker.currentNode;
                const value = node.nodeValue.trim();
                if (!value || !translatableTextMap.has(value)) continue;
                node.nodeValue = node.nodeValue.replace(value, translatableTextMap.get(value));
            }

            document.querySelectorAll('[data-i18n-title]').forEach(element => {
                const key = element.dataset.i18nTitle;
                if (dictionary[key]) {
                    element.title = dictionary[key];
                }
            });

            document.querySelectorAll('[placeholder]').forEach(element => {
                const placeholder = element.getAttribute('placeholder');
                if (placeholder && dictionary[placeholder]) {
                    element.setAttribute('placeholder', dictionary[placeholder]);
                }
            });

            document.querySelectorAll('[aria-label]').forEach(element => {
                const label = element.getAttribute('aria-label');
                if (label && dictionary[label]) {
                    element.setAttribute('aria-label', dictionary[label]);
                }
            });

            document.querySelectorAll('[title]').forEach(element => {
                const title = element.getAttribute('title');
                if (title && dictionary[title]) {
                    element.setAttribute('title', dictionary[title]);
                }
            });

            document.querySelectorAll('[alt]').forEach(element => {
                const alt = element.getAttribute('alt');
                if (alt && dictionary[alt]) {
                    element.setAttribute('alt', dictionary[alt]);
                }
            });

            document.querySelectorAll('[data-site-language]').forEach(option => {
                option.classList.toggle('selected', option.dataset.siteLanguage === language);
            });

            localStorage.setItem('amax-site-language', language);
            document.body.dataset.currentLanguage = language;
        };

        applyLanguage(selectedLanguage);
        document.querySelectorAll('[data-site-language]').forEach(option => {
            option.addEventListener('click', () => applyLanguage(option.dataset.siteLanguage));
        });
    })();

    // ============================================
    // SITE-WIDE MOTION
    // ============================================

    (function initializeSiteMotion() {
        document.body.classList.add('motion-ready');

        const revealItems = document.querySelectorAll('.reveal, .summary-card, .metric-card, .feature-card, .platform-card, .model-card, .quick-link, .contact-box');
        revealItems.forEach((item, index) => {
            if (!item.classList.contains('reveal')) {
                item.classList.add('motion-item');
                item.style.transitionDelay = `${Math.min(index * 45, 360)}ms`;
            }
        });

        const showItem = item => item.classList.add(item.classList.contains('reveal') ? 'visible' : 'motion-visible');
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries, currentObserver) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        showItem(entry.target);
                        currentObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.12 });
            revealItems.forEach(item => observer.observe(item));
        } else {
            revealItems.forEach(showItem);
        }

        document.querySelectorAll('.btn, .nav-btn, button').forEach(button => {
            button.addEventListener('click', event => {
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
                button.style.position = button.style.position || 'relative';
                button.style.overflow = 'hidden';
                const ripple = document.createElement('span');
                ripple.className = 'ripple';
                const bounds = button.getBoundingClientRect();
                ripple.style.left = `${event.clientX - bounds.left}px`;
                ripple.style.top = `${event.clientY - bounds.top}px`;
                button.appendChild(ripple);
                ripple.addEventListener('animationend', () => ripple.remove(), { once: true });
            });
        });

        document.querySelectorAll('[data-copy-upi]').forEach(button => {
            button.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(button.dataset.copyUpi);
                    button.innerHTML = '<i class="fas fa-check"></i> UPI ID Copied';
                    setTimeout(() => {
                        button.innerHTML = '<i class="fas fa-copy"></i> Copy UPI ID';
                    }, 1800);
                } catch (error) {
                    console.error('Unable to copy UPI ID:', error);
                }
            });
        });

        document.querySelectorAll('[data-upi-pay]').forEach(link => {
            link.addEventListener('click', () => {
                const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
                if (!isMobile) {
                    setTimeout(() => window.alert('UPI apps open on a phone. Scan the QR code or copy the UPI ID and pay using PhonePe, Google Pay, or another UPI app.'), 250);
                }
            });
        });
    })();

    // ============================================
    // DOM CONTENT LOADED - INITIALIZE EVERYTHING
    // ============================================

    document.addEventListener('DOMContentLoaded', function() {

        // ============================================
        // DOM ELEMENTS
        // ============================================

        const chatBox = document.getElementById('chat-box');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        const clearBtn = document.getElementById('clear-history-btn');
        const themeToggle = document.getElementById('theme-toggle');
        const typingIndicator = document.getElementById('typing-indicator');

        // ============================================
        // STATE
        // ============================================

        let isSending = false;
        let currentTheme = localStorage.getItem('amax-theme') || 'light';

        // ============================================
        // INITIALIZE
        // ============================================

        applyTheme(currentTheme);
        setupAutoResize();
        scrollToBottom();
        focusInput();

        // ============================================
        // EVENT LISTENERS
        // ============================================

        // Send button click
        if (sendBtn) {
            sendBtn.addEventListener('click', sendMessage);
        }

        // Enter key (Shift+Enter for new line)
        if (userInput) {
            userInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

        // Clear history button
        if (clearBtn) {
            clearBtn.addEventListener('click', clearHistory);
        }

        // Theme toggle button
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }

        // ============================================
        // CORE FUNCTIONS
        // ============================================

        /**
         * Send message to server and get AI response
         */
        async function sendMessage() {
            if (isSending) return;

            const message = userInput.value.trim();
            if (!message) return;

            // Disable input while sending
            isSending = true;
            userInput.disabled = true;
            sendBtn.disabled = true;
            sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            // Remove welcome message if exists
            removeWelcomeMessage();

            // Add user message to chat
            addMessage(message, 'user');

            // Clear input
            userInput.value = '';
            userInput.style.height = 'auto';

            // Show typing indicator
            showTypingIndicator();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const contentType = response.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) {
                    const text = await response.text();
                    throw new Error(text.includes('<!doctype html') ? 'Session expired. Please log in again.' : (text || 'Server returned an invalid response.'));
                }

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Server error');
                }

                // Hide typing indicator
                hideTypingIndicator();

                // Add AI response (Yahan data.reply use karna hai, data.response nahi)
                addMessage(data.reply, 'ai', data.timestamp);

            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessage(`⚠️ ${error.message || 'Sorry, I encountered an error. Please try again.'}`, 'ai');
            } finally {
                // Re-enable input
                isSending = false;
                userInput.disabled = false;
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
                focusInput();
            }
        }

        /**
         * Add a message to the chat box
         */
        function addMessage(content, type, timestamp = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';

            // Header
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';

            const strong = document.createElement('strong');
            strong.textContent = type === 'user' ? 'You' : 'AMAX AI';
            headerDiv.appendChild(strong);

            // Timestamp
            if (!timestamp) {
                const now = new Date();
                timestamp = now.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }

            const timeSpan = document.createElement('span');
            timeSpan.className = 'message-time';
            timeSpan.textContent = timestamp;
            headerDiv.appendChild(timeSpan);

            // Actions (for AI messages)
            if (type === 'ai') {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-message-btn';
                copyBtn.title = 'Copy';
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                copyBtn.addEventListener('click', function() {
                    copyMessage(this);
                });
                headerDiv.appendChild(copyBtn);
            }

            contentDiv.appendChild(headerDiv);

            // Message text
            const p = document.createElement('p');
            p.textContent = content;
            contentDiv.appendChild(p);

            messageDiv.appendChild(contentDiv);
            chatBox.appendChild(messageDiv);

            // Scroll to bottom
            scrollToBottom();
        }

        /**
         * Remove welcome message
         */
        function removeWelcomeMessage() {
            const welcome = chatBox.querySelector('.welcome-message');
            if (welcome) {
                welcome.style.opacity = '0';
                welcome.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    welcome.remove();
                }, 300);
            }
        }

        /**
         * Show typing indicator
         */
        function showTypingIndicator() {
            if (typingIndicator) {
                typingIndicator.classList.add('active');
                scrollToBottom();
            }
        }

        /**
         * Hide typing indicator
         */
        function hideTypingIndicator() {
            if (typingIndicator) {
                typingIndicator.classList.remove('active');
            }
        }

        /**
         * Scroll chat box to bottom
         */
        function scrollToBottom() {
            if (chatBox) {
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        /**
         * Focus on input field
         */
        function focusInput() {
            if (userInput) {
                setTimeout(() => {
                    userInput.focus();
                }, 100);
            }
        }

        /**
         * Auto-resize textarea
         */
        function setupAutoResize() {
            if (userInput) {
                userInput.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
                });
            }
        }

        // ============================================
        // CLEAR HISTORY
        // ============================================

        async function clearHistory() {
            if (!confirm('Are you sure you want to clear all chat history?')) {
                return;
            }

            try {
                // Remove all messages
                const messages = chatBox.querySelectorAll('.message');
                messages.forEach(msg => msg.remove());

                // Add welcome message back
                addWelcomeMessage();

                // Show success feedback
                showToast('Chat history cleared!', 'success');
            } catch (error) {
                console.error('Error clearing history:', error);
                showToast('Error clearing history', 'error');
            }
        }

        /**
         * Add welcome message back
         */
        function addWelcomeMessage() {
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome-message';
            welcomeDiv.innerHTML = `
                <span class="welcome-icon">👋</span>
                <h3>Welcome to AMAX!</h3>
                <p>Ask me anything and I'll help you out.</p>
                <div class="quick-suggestions">
                    <button class="suggestion-btn" onclick="window.sendSuggestion('What is artificial intelligence?')">
                        🤖 What is AI?
                    </button>
                    <button class="suggestion-btn" onclick="window.sendSuggestion('Tell me a fun fact')">
                        💡 Fun fact
                    </button>
                    <button class="suggestion-btn" onclick="window.sendSuggestion('How does machine learning work?')">
                        🧠 Machine Learning
                    </button>
                    <button class="suggestion-btn" onclick="window.sendSuggestion('What is the meaning of life?')">
                        🌌 Life meaning
                    </button>
                </div>
            `;
            chatBox.appendChild(welcomeDiv);

            // Add event listeners to suggestion buttons
            welcomeDiv.querySelectorAll('.suggestion-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const text = this.textContent.trim();
                    userInput.value = text;
                    sendMessage();
                });
            });
        }

        // ============================================
        // COPY MESSAGE
        // ============================================

        function copyMessage(buttonElement) {
            const messageContent = buttonElement.closest('.message-content');
            const p = messageContent.querySelector('p');
            const text = p.textContent;

            navigator.clipboard.writeText(text).then(() => {
                // Show success feedback
                const icon = buttonElement.querySelector('i');
                const originalClass = icon.className;

                icon.className = 'fas fa-check';
                buttonElement.style.color = '#28a745';

                setTimeout(() => {
                    icon.className = originalClass;
                    buttonElement.style.color = '';
                }, 2000);

                showToast('Copied to clipboard!', 'success');
            }).catch(err => {
                console.error('Failed to copy:', err);
                showToast('Failed to copy', 'error');
            });
        }

        // ============================================
        // THEME (DARK/LIGHT MODE)
        // ============================================

        function toggleTheme() {
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
            localStorage.setItem('amax-theme', newTheme);
            currentTheme = newTheme;

            // Update icon
            if (themeToggle) {
                const icon = themeToggle.querySelector('i');
                if (newTheme === 'dark') {
                    icon.className = 'fas fa-sun';
                } else {
                    icon.className = 'fas fa-moon';
                }
            }
        }

        function applyTheme(theme) {
            if (theme === 'dark') {
                document.body.classList.add('dark-mode');
                if (themeToggle) {
                    const icon = themeToggle.querySelector('i');
                    icon.className = 'fas fa-sun';
                }
            } else {
                document.body.classList.remove('dark-mode');
                if (themeToggle) {
                    const icon = themeToggle.querySelector('i');
                    icon.className = 'fas fa-moon';
                }
            }
        }

        // ============================================
        // SUGGESTION BUTTONS (Quick questions)
        // ============================================

        // Make sendSuggestion globally accessible for inline onclick
        window.sendSuggestion = function(text) {
            if (userInput) {
                userInput.value = text;
                sendMessage();
            }
        };

        // ============================================
        // TOAST NOTIFICATIONS
        // ============================================

        function showToast(message, type = 'info') {
            // Remove existing toast
            const existingToast = document.querySelector('.toast-notification');
            if (existingToast) {
                existingToast.remove();
            }

            const toast = document.createElement('div');
            toast.className = `toast-notification toast-${type}`;

            const colors = {
                success: '#28a745',
                error: '#dc3545',
                warning: '#ffc107',
                info: '#17a2b8'
            };

            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };

            toast.innerHTML = `
                <i class="fas ${icons[type] || icons.info}"></i>
                <span>${message}</span>
            `;

            toast.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                padding: 14px 24px;
                background: ${colors[type] || colors.info};
                color: white;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
                box-shadow: 0 8px 30px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 12px;
                z-index: 9999;
                animation: slideUp 0.3s ease-out;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 400px;
            `;

            document.body.appendChild(toast);

            // Auto dismiss after 3 seconds
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, 3000);
        }

        // ============================================
        // KEYBOARD SHORTCUTS
        // ============================================

        document.addEventListener('keydown', function(e) {
            // Ctrl+Enter to send (fallback)
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                if (userInput && userInput === document.activeElement) {
                    sendMessage();
                }
            }

            // Escape to clear input
            if (e.key === 'Escape' && userInput === document.activeElement) {
                userInput.value = '';
                userInput.style.height = 'auto';
            }
        });

        // ============================================
        // CONSOLE WELCOME MESSAGE
        // ============================================

        console.log('%c⚡ AMAX AI Assistant', 'font-size: 24px; font-weight: bold; color: #6C3CE1;');
        console.log('%cWelcome to AMAX! Chat with AI powered by Gemini.', 'font-size: 14px; color: #666;');
        console.log('%c🔗 https://amax-ai.com', 'font-size: 12px; color: #6C3CE1;');

    });

    // ============================================
    // LOADING STATE (Optional - for page load)
    // ============================================

    window.addEventListener('load', function() {
        // Check if chat is empty, show welcome
        const messages = document.querySelectorAll('.message');
        if (messages.length === 0 && document.querySelector('.welcome-message') === null) {
            const chatBox = document.getElementById('chat-box');
            if (chatBox) {
                const welcomeDiv = document.createElement('div');
                welcomeDiv.className = 'welcome-message';
                welcomeDiv.innerHTML = `
                    <span class="welcome-icon">👋</span>
                    <h3>Welcome to AMAX!</h3>
                    <p>Ask me anything and I'll help you out.</p>
                    <div class="quick-suggestions">
                        <button class="suggestion-btn" onclick="window.sendSuggestion('What is artificial intelligence?')">
                            🤖 What is AI?
                        </button>
                        <button class="suggestion-btn" onclick="window.sendSuggestion('Tell me a fun fact')">
                            💡 Fun fact
                        </button>
                        <button class="suggestion-btn" onclick="window.sendSuggestion('How does machine learning work?')">
                            🧠 Machine Learning
                        </button>
                        <button class="suggestion-btn" onclick="window.sendSuggestion('What is the meaning of life?')">
                            🌌 Life meaning
                        </button>
                    </div>
                `;
                chatBox.appendChild(welcomeDiv);

                // Add event listeners to suggestion buttons
                welcomeDiv.querySelectorAll('.suggestion-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const text = this.textContent.trim();
                        const userInput = document.getElementById('user-input');
                        if (userInput) {
                            userInput.value = text;
                            // Trigger send
                            const event = new Event('input');
                            userInput.dispatchEvent(event);
                            document.getElementById('send-btn')?.click();
                        }
                    });
                });
            }
        }
    });