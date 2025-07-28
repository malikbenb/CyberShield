// JavaScript spécifique pour la page blog
document.addEventListener('DOMContentLoaded', () => {
    // Sélectionner tous les articles du blog
    const blogArticles = document.querySelectorAll('.blog-article');
    
    // Ajouter une classe pour l'animation progressive d'apparition
    function animateArticles() {
        blogArticles.forEach((article, index) => {
            setTimeout(() => {
                article.classList.add('visible');
            }, 100 * index);
        });
    }
    
    // Initialiser l'animation
    animateArticles();
    
    // Filtrage des articles par catégorie
    const categoryButtons = document.querySelectorAll('.blog-category-btn');
    if (categoryButtons.length > 0) {
        categoryButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Retirer la classe active de tous les boutons
                categoryButtons.forEach(btn => btn.classList.remove('active'));
                
                // Ajouter la classe active au bouton cliqué
                button.classList.add('active');
                
                // Récupérer la catégorie sélectionnée
                const category = button.getAttribute('data-category');
                
                // Filtrer les articles
                blogArticles.forEach(article => {
                    if (category === 'all' || article.getAttribute('data-category') === category) {
                        article.style.display = 'block';
                        setTimeout(() => {
                            article.classList.add('visible');
                        }, 50);
                    } else {
                        article.classList.remove('visible');
                        setTimeout(() => {
                            article.style.display = 'none';
                        }, 300); // Attendre la fin de l'animation de disparition
                    }
                });
            });
        });
    }
    
    // Empêcher le clignotement du texte en préchargeant les images
    function preloadImages() {
        const images = document.querySelectorAll('.blog-article img');
        images.forEach(img => {
            const src = img.getAttribute('src');
            if (src) {
                const preloadImg = new Image();
                preloadImg.src = src;
            }
        });
    }
    
    // Précharger les images
    preloadImages();
});
