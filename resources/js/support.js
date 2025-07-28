// JavaScript spécifique pour la page support
document.addEventListener('DOMContentLoaded', () => {
    // Gestion des onglets de support
    const supportTabs = document.querySelectorAll('.support-tab');
    const supportPanes = document.querySelectorAll('.support-pane');
    
    if (supportTabs.length > 0) {
        // Fonction pour activer un onglet et son contenu
        function activateTab(tabId) {
            // Désactiver tous les onglets et contenus
            supportTabs.forEach(tab => tab.classList.remove('active'));
            supportPanes.forEach(pane => pane.classList.remove('active'));
            
            // Activer l'onglet sélectionné et son contenu
            const selectedTab = document.querySelector(`.support-tab[data-tab="${tabId}"]`);
            const selectedPane = document.getElementById(`${tabId}-pane`);
            
            if (selectedTab && selectedPane) {
                selectedTab.classList.add('active');
                selectedPane.classList.add('active');
            }
        }
        
        // Ajouter les écouteurs d'événements aux onglets
        supportTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.getAttribute('data-tab');
                activateTab(tabId);
                
                // Mettre à jour l'URL avec le hash sans recharger la page
                history.pushState(null, null, `#${tabId}`);
            });
        });
        
        // Vérifier si un hash est présent dans l'URL au chargement
        if (window.location.hash) {
            const tabId = window.location.hash.substring(1);
            activateTab(tabId);
        } else {
            // Activer le premier onglet par défaut
            const firstTabId = supportTabs[0].getAttribute('data-tab');
            activateTab(firstTabId);
        }
        
        // Gérer les changements d'URL (navigation avec les boutons précédent/suivant du navigateur)
        window.addEventListener('popstate', () => {
            if (window.location.hash) {
                const tabId = window.location.hash.substring(1);
                activateTab(tabId);
            } else {
                // Si pas de hash, activer le premier onglet
                const firstTabId = supportTabs[0].getAttribute('data-tab');
                activateTab(firstTabId);
            }
        });
    }
    
    // Gestion des questions/réponses FAQ
    const faqItems = document.querySelectorAll('.support-faq-item');
    
    if (faqItems.length > 0) {
        faqItems.forEach(item => {
            const question = item.querySelector('.support-faq-question');
            
            question.addEventListener('click', () => {
                // Fermer toutes les autres questions
                faqItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('active')) {
                        otherItem.classList.remove('active');
                    }
                });
                
                // Basculer l'état de la question actuelle
                item.classList.toggle('active');
            });
        });
    }
    
    // Gestion du formulaire de contact
    const contactForm = document.getElementById('support-contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Simuler l'envoi du formulaire
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Envoi en cours...';
            
            // Simuler un délai de traitement
            setTimeout(() => {
                // Afficher un message de succès
                const formContainer = contactForm.parentElement;
                formContainer.innerHTML = `
                    <div class="success-message">
                        <i class="fas fa-check-circle"></i>
                        <h3>Message envoyé avec succès !</h3>
                        <p>Merci de nous avoir contactés. Notre équipe vous répondra dans les plus brefs délais.</p>
                        <button class="btn cyber-btn" onclick="location.reload()">Envoyer un autre message</button>
                    </div>
                `;
            }, 1500);
        });
    }
    
    // Gestion de la recherche dans la base de connaissances
    const knowledgeSearch = document.getElementById('knowledge-search');
    const knowledgeItems = document.querySelectorAll('.knowledge-item');
    
    if (knowledgeSearch && knowledgeItems.length > 0) {
        knowledgeSearch.addEventListener('input', () => {
            const searchTerm = knowledgeSearch.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                // Afficher tous les éléments si la recherche est vide
                knowledgeItems.forEach(item => {
                    item.style.display = 'block';
                });
            } else {
                // Filtrer les éléments en fonction du terme de recherche
                knowledgeItems.forEach(item => {
                    const title = item.querySelector('h3').textContent.toLowerCase();
                    const content = item.querySelector('p').textContent.toLowerCase();
                    
                    if (title.includes(searchTerm) || content.includes(searchTerm)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            }
        });
    }
});
