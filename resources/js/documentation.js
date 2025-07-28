// JavaScript spécifique pour la page documentation
document.addEventListener('DOMContentLoaded', () => {
    // Sélectionner tous les liens de navigation dans la sidebar
    const navLinks = document.querySelectorAll('.doc-nav a');
    
    // Sélectionner toutes les sections de documentation
    const docSections = document.querySelectorAll('.doc-section');
    
    // Fonction pour afficher une section spécifique et masquer les autres
    function showSection(sectionId) {
        // Masquer toutes les sections
        docSections.forEach(section => {
            section.style.display = 'none';
        });
        
        // Afficher la section demandée
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
        
        // Mettre à jour les classes actives dans la navigation
        navLinks.forEach(link => {
            if (link.getAttribute('href') === '#' + sectionId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    // Ajouter des écouteurs d'événements à tous les liens de navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('href').substring(1); // Enlever le # du href
            showSection(sectionId);
            
            // Faire défiler vers le haut de la section principale
            document.querySelector('.doc-main').scrollTop = 0;
            
            // Mettre à jour l'URL avec le hash sans recharger la page
            history.pushState(null, null, link.getAttribute('href'));
        });
    });
    
    // Vérifier si un hash est présent dans l'URL au chargement
    if (window.location.hash) {
        const sectionId = window.location.hash.substring(1);
        showSection(sectionId);
    } else {
        // Par défaut, afficher la première section
        const firstSectionId = docSections[0].id;
        showSection(firstSectionId);
    }
    
    // Gérer les changements d'URL (navigation avec les boutons précédent/suivant du navigateur)
    window.addEventListener('popstate', () => {
        if (window.location.hash) {
            const sectionId = window.location.hash.substring(1);
            showSection(sectionId);
        } else {
            // Si pas de hash, afficher la première section
            const firstSectionId = docSections[0].id;
            showSection(firstSectionId);
        }
    });
});
