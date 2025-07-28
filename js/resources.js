// JavaScript pour les pages ressources

// Fonction pour gérer les onglets dans la documentation
function setupDocTabs() {
    const tabButtons = document.querySelectorAll('.doc-tab');
    if (tabButtons.length === 0) return;

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Désactiver tous les onglets
            document.querySelectorAll('.doc-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Cacher tous les contenus d'onglets
            document.querySelectorAll('.doc-tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Activer l'onglet cliqué
            button.classList.add('active');
            
            // Afficher le contenu correspondant
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// Fonction pour gérer les catégories dans la FAQ
function setupFaqCategories() {
    const categoryButtons = document.querySelectorAll('.faq-category');
    if (categoryButtons.length === 0) return;

    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Désactiver toutes les catégories
            document.querySelectorAll('.faq-category').forEach(cat => {
                cat.classList.remove('active');
            });
            
            // Cacher toutes les listes de FAQ
            document.querySelectorAll('.faq-list').forEach(list => {
                list.classList.add('hidden');
            });
            
            // Activer la catégorie cliquée
            button.classList.add('active');
            
            // Afficher la liste correspondante
            const categoryId = button.getAttribute('data-category');
            document.getElementById(categoryId).classList.remove('hidden');
        });
    });
}

// Fonction pour gérer les questions/réponses dans la FAQ
function setupFaqItems() {
    const faqQuestions = document.querySelectorAll('.faq-question, .support-faq-question');
    if (faqQuestions.length === 0) return;

    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            const isActive = faqItem.classList.contains('active');
            
            // Fermer toutes les questions ouvertes
            document.querySelectorAll('.faq-item, .support-faq-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Si la question n'était pas active, l'activer
            if (!isActive) {
                faqItem.classList.add('active');
            }
        });
    });
}

// Fonction pour gérer le chat en direct
function setupLiveChat() {
    const liveChatBtn = document.getElementById('live-chat-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatContainer = document.getElementById('live-chat-container');
    
    if (!liveChatBtn || !closeChatBtn || !chatContainer) return;
    
    liveChatBtn.addEventListener('click', () => {
        chatContainer.classList.add('active');
    });
    
    closeChatBtn.addEventListener('click', () => {
        chatContainer.classList.remove('active');
    });
    
    // Simuler une conversation de chat
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.querySelector('.send-message');
    const chatInput = document.querySelector('.chat-input textarea');
    
    if (sendButton && chatInput && chatMessages) {
        sendButton.addEventListener('click', () => {
            const message = chatInput.value.trim();
            if (message) {
                // Ajouter le message de l'utilisateur
                addChatMessage(message, 'user');
                chatInput.value = '';
                
                // Simuler une réponse après un court délai
                setTimeout(() => {
                    addChatMessage("Merci pour votre message. Un conseiller va vous répondre dans quelques instants.", 'support');
                }, 1000);
            }
        });
        
        // Permettre l'envoi avec Entrée
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });
    }
    
    function addChatMessage(text, type) {
        const now = new Date();
        const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        const messageHTML = `
            <div class="chat-message ${type}">
                <div class="chat-avatar">
                    <img src="../images/${type === 'user' ? 'user-avatar.jpg' : 'support-avatar.jpg'}" alt="${type === 'user' ? 'Vous' : 'Support'}">
                </div>
                <div class="chat-bubble">
                    <p>${text}</p>
                    <span class="chat-time">${time}</span>
                </div>
            </div>
        `;
        
        chatMessages.insertAdjacentHTML('beforeend', messageHTML);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Initialiser toutes les fonctionnalités lorsque le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    setupDocTabs();
    setupFaqCategories();
    setupFaqItems();
    setupLiveChat();
});
