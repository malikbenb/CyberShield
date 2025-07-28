// Fichier: frontend/js/auth.js

const API_BASE_URL = '/api'; // Assurez-vous que cela correspond à la configuration du proxy ou de l'API

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const errorMessageDiv = document.getElementById('error-message');
    const successMessageDiv = document.getElementById('success-message');

    // Fonction pour afficher les messages d'erreur
    function displayMessage(element, message, isError = true) {
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            element.className = isError ? 'error-message' : 'success-message';
            // Masquer l'autre type de message
            const otherElement = isError ? successMessageDiv : errorMessageDiv;
            if (otherElement) otherElement.style.display = 'none';
        } else {
            console.error("Élément de message non trouvé");
        }
    }

    // Fonction pour gérer la redirection après connexion/inscription
    function handleRedirectAfterAuth() {
        const redirectType = sessionStorage.getItem('redirect_after_login');
        const scannerOs = sessionStorage.getItem('scanner_os');
        
        if (redirectType === 'pro' && scannerOs) {
            // Rediriger vers la page d'abonnement avec les paramètres
            window.location.href = 'subscription.html?os=' + scannerOs;
        } else {
            // Redirection par défaut vers le tableau de bord
            window.location.href = 'index.html';
        }
    }

    // Gestion du formulaire de connexion
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (errorMessageDiv) errorMessageDiv.style.display = 'none'; // Cacher les anciens messages

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    // Connexion réussie, gérer la redirection
                    handleRedirectAfterAuth();
                } else {
                    displayMessage(errorMessageDiv, data.message || 'Erreur de connexion.');
                }
            } catch (error) {
                console.error('Erreur lors de la connexion:', error);
                displayMessage(errorMessageDiv, 'Une erreur réseau est survenue.');
            }
        });
    }

    // Gestion du formulaire d'inscription
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (errorMessageDiv) errorMessageDiv.style.display = 'none';
            if (successMessageDiv) successMessageDiv.style.display = 'none';

            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (password !== confirmPassword) {
                displayMessage(errorMessageDiv, 'Les mots de passe ne correspondent pas.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ first_name: firstName, last_name: lastName, email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    // Inscription réussie, l'API connecte automatiquement l'utilisateur
                    // Afficher un message de succès et rediriger
                    displayMessage(successMessageDiv, 'Inscription réussie ! Redirection...', false);
                    setTimeout(() => {
                        handleRedirectAfterAuth();
                    }, 1500); // Délai pour lire le message
                } else {
                    displayMessage(errorMessageDiv, data.message || 'Erreur lors de l\'inscription.');
                }
            } catch (error) {
                console.error('Erreur lors de l\'inscription:', error);
                displayMessage(errorMessageDiv, 'Une erreur réseau est survenue.');
            }
        });
    }

    // Récupérer les paramètres de l'URL pour la page d'inscription
    if (registerForm) {
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect');
        const os = urlParams.get('os');
        
        // Si l'utilisateur vient pour télécharger le scanner Pro
        if (redirect === 'pro' && os) {
            // Stocker les paramètres dans sessionStorage pour les récupérer après inscription
            sessionStorage.setItem('redirect_after_login', 'pro');
            sessionStorage.setItem('scanner_os', os);
            
            // Afficher un message spécifique si l'élément existe
            const proMessage = document.getElementById('pro-message');
            if (proMessage) {
                proMessage.style.display = 'block';
            }
        }
    }
});

