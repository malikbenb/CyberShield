// JavaScript pour la gestion des paiements simulés

// Variables globales pour stocker les informations de paiement
let paymentData = {
    plan: 'pro',
    duration: 1,
    amount: 40000,
    currency: 'DA',
    email: '',
    name: '',
    orderId: ''
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Déterminer quelle page est actuellement chargée
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('index.html') || currentPath.endsWith('/payment/')) {
        initPlanSelectionPage();
    } else if (currentPath.includes('select-duration.html')) {
        initDurationSelectionPage();
    } else if (currentPath.includes('payment-form.html')) {
        initPaymentFormPage();
    } else if (currentPath.includes('confirmation.html')) {
        initConfirmationPage();
    }
});

// Initialisation de la page de sélection de plan
function initPlanSelectionPage() {
    console.log('Initialisation de la page de sélection de plan');
    
    // Réinitialiser les données de paiement stockées
    sessionStorage.removeItem('paymentData');
    
    // Ajouter des gestionnaires d'événements pour les boutons de sélection de plan
    const planButtons = document.querySelectorAll('.plan-card .btn');
    planButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Si le lien contient déjà un paramètre plan, ne rien faire
            if (this.href.includes('?plan=')) return;
            
            // Déterminer le plan sélectionné
            const planCard = this.closest('.plan-card');
            const planTitle = planCard.querySelector('.plan-title').textContent.toLowerCase();
            
            // Stocker le plan sélectionné
            paymentData.plan = planTitle === 'pro' ? 'pro' : 'enterprise';
            
            // Mettre à jour l'URL avec le plan sélectionné
            if (this.href.includes('select-duration.html')) {
                e.preventDefault();
                window.location.href = `select-duration.html?plan=${paymentData.plan}`;
            }
        });
    });
}

// Initialisation de la page de sélection de durée
function initDurationSelectionPage() {
    console.log('Initialisation de la page de sélection de durée');
    
    // Récupérer le plan sélectionné depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const plan = urlParams.get('plan') || 'pro';
    
    // Mettre à jour les informations du plan
    paymentData.plan = plan;
    
    // Mettre à jour l'affichage du plan sélectionné
    const planNameElement = document.getElementById('selected-plan-name');
    if (planNameElement) {
        planNameElement.textContent = plan === 'pro' ? 'Plan Pro' : 'Plan Entreprise';
    }
    
    const planFeaturesElement = document.getElementById('selected-plan-features');
    if (planFeaturesElement) {
        planFeaturesElement.textContent = plan === 'pro' 
            ? '1 adresse IP, scan avancé, rapport détaillé' 
            : '20 adresses IP, scan avancé, rapport détaillé, support prioritaire';
    }
    
    // Mettre à jour les prix en fonction du plan
    updatePrices(plan);
    
    // Ajouter des gestionnaires d'événements pour les options de durée
    const durationOptions = document.querySelectorAll('.duration-card');
    durationOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Sélectionner le radio button dans cette carte
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
            
            // Mettre à jour la durée sélectionnée
            paymentData.duration = parseInt(radio.value);
            
            // Mettre à jour le montant en fonction de la durée
            updateAmount(plan, paymentData.duration);
        });
    });
    
    // Ajouter un gestionnaire d'événements pour le bouton de continuation
    const continueButton = document.getElementById('continue-to-payment');
    if (continueButton) {
        continueButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Récupérer la durée sélectionnée
            const selectedDuration = document.querySelector('input[name="duration"]:checked');
            if (selectedDuration) {
                paymentData.duration = parseInt(selectedDuration.value);
            }
            
            // Mettre à jour le montant
            updateAmount(plan, paymentData.duration);
            
            // Stocker les données de paiement
            sessionStorage.setItem('paymentData', JSON.stringify(paymentData));
            
            // Rediriger vers la page de paiement
            window.location.href = 'payment-form.html';
        });
    }
}

// Mise à jour des prix en fonction du plan
function updatePrices(plan) {
    const basePrice = plan === 'pro' ? 40000 : 100000;
    
    // Prix mensuel
    const monthlyPriceElement = document.getElementById('monthly-price');
    if (monthlyPriceElement) {
        monthlyPriceElement.textContent = `${basePrice.toLocaleString()} DA`;
    }
    
    // Prix trimestriel (10% de réduction)
    const quarterlyPrice = Math.round(basePrice * 3 * 0.9);
    const quarterlyPriceElement = document.getElementById('quarterly-price');
    if (quarterlyPriceElement) {
        quarterlyPriceElement.textContent = `${quarterlyPrice.toLocaleString()} DA`;
    }
    
    // Prix annuel (20% de réduction)
    const annualPrice = Math.round(basePrice * 12 * 0.8);
    const annualPriceElement = document.getElementById('annual-price');
    if (annualPriceElement) {
        annualPriceElement.textContent = `${annualPrice.toLocaleString()} DA`;
    }
}

// Mise à jour du montant en fonction du plan et de la durée
function updateAmount(plan, duration) {
    const basePrice = plan === 'pro' ? 40000 : 100000;
    
    if (duration === 3) {
        // Trimestriel (10% de réduction)
        paymentData.amount = Math.round(basePrice * 3 * 0.9);
    } else if (duration === 12) {
        // Annuel (20% de réduction)
        paymentData.amount = Math.round(basePrice * 12 * 0.8);
    } else {
        // Mensuel
        paymentData.amount = basePrice;
    }
}

// Initialisation de la page de formulaire de paiement
function initPaymentFormPage() {
    console.log('Initialisation de la page de formulaire de paiement');
    
    // Récupérer les données de paiement stockées
    const storedData = sessionStorage.getItem('paymentData');
    if (storedData) {
        paymentData = JSON.parse(storedData);
    } else {
        // Rediriger vers la page de sélection de plan si aucune donnée n'est disponible
        window.location.href = 'index.html';
        return;
    }
    
    // Mettre à jour le récapitulatif
    updatePaymentSummary();
    
    // Ajouter un gestionnaire d'événements pour le formulaire de paiement
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Récupérer les informations du formulaire
            paymentData.name = document.getElementById('full-name').value;
            paymentData.email = document.getElementById('email').value;
            paymentData.card_number = document.getElementById('card-number').value.replace(/\D/g, '');
            paymentData.expiry_date = document.getElementById('expiry-date').value;
            paymentData.cvv = document.getElementById('cvv').value;
            paymentData.address = document.getElementById('address').value;
            paymentData.city = document.getElementById('city').value;
            paymentData.postal_code = document.getElementById('postal-code').value;
            
            // Valider le formulaire
            if (!validatePaymentForm()) {
                return;
            }
            
            // Simuler le traitement du paiement
            processPayment();
        });
    }
    
    // Formater automatiquement le numéro de carte
    const cardNumberInput = document.getElementById('card-number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 16) {
                value = value.substr(0, 16);
            }
            
            // Formater avec des espaces tous les 4 chiffres
            let formattedValue = '';
            for (let i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formattedValue += ' ';
                }
                formattedValue += value[i];
            }
            
            this.value = formattedValue;
        });
    }
    
    // Formater automatiquement la date d'expiration
    const expiryDateInput = document.getElementById('expiry-date');
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) {
                value = value.substr(0, 4);
            }
            
            // Formater avec un slash après les 2 premiers chiffres
            if (value.length > 2) {
                this.value = value.substr(0, 2) + '/' + value.substr(2);
            } else {
                this.value = value;
            }
        });
    }
    
    // Limiter le CVV à 3 ou 4 chiffres
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) {
                value = value.substr(0, 4);
            }
            this.value = value;
        });
    }
}

// Mise à jour du récapitulatif de paiement
function updatePaymentSummary() {
    // Plan
    const summaryPlanElement = document.getElementById('summary-plan');
    if (summaryPlanElement) {
        summaryPlanElement.textContent = paymentData.plan === 'pro' ? 'Pro' : 'Entreprise';
    }
    
    // Durée
    const summaryDurationElement = document.getElementById('summary-duration');
    if (summaryDurationElement) {
        if (paymentData.duration === 1) {
            summaryDurationElement.textContent = '1 mois';
        } else if (paymentData.duration === 3) {
            summaryDurationElement.textContent = '3 mois';
        } else if (paymentData.duration === 12) {
            summaryDurationElement.textContent = '1 an';
        }
    }
    
    // Prix unitaire
    const summaryUnitPriceElement = document.getElementById('summary-unit-price');
    if (summaryUnitPriceElement) {
        const basePrice = paymentData.plan === 'pro' ? 40000 : 100000;
        summaryUnitPriceElement.textContent = `${basePrice.toLocaleString()} DA/mois`;
    }
    
    // Total
    const summaryTotalElement = document.getElementById('summary-total');
    if (summaryTotalElement) {
        summaryTotalElement.textContent = `${paymentData.amount.toLocaleString()} DA`;
    }
    
    // Mettre à jour les fonctionnalités en fonction du plan
    const orderFeaturesList = document.querySelector('.order-features ul');
    if (orderFeaturesList && paymentData.plan === 'enterprise') {
        orderFeaturesList.innerHTML = `
            <li><i class="fas fa-check text-success me-2"></i>Scan avancé</li>
            <li><i class="fas fa-check text-success me-2"></i><strong>20 adresses IP</strong></li>
            <li><i class="fas fa-check text-success me-2"></i>Rapport détaillé</li>
            <li><i class="fas fa-check text-success me-2"></i>Score de vulnérabilité</li>
            <li><i class="fas fa-check text-success me-2"></i>Solutions recommandées</li>
            <li><i class="fas fa-check text-success me-2"></i>Historique des scans</li>
            <li><i class="fas fa-check text-success me-2"></i>Support prioritaire</li>
        `;
    }
}

// Validation du formulaire de paiement
function validatePaymentForm() {
    // Nom complet
    const fullName = document.getElementById('full-name').value.trim();
    if (fullName.length < 3) {
        alert('Veuillez saisir un nom complet valide.');
        return false;
    }
    
    // Email
    const email = document.getElementById('email').value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Veuillez saisir une adresse email valide.');
        return false;
    }
    
    // Numéro de carte
    const cardNumber = document.getElementById('card-number').value.replace(/\D/g, '');
    if (cardNumber.length < 16) {
        alert('Veuillez saisir un numéro de carte valide.');
        return false;
    }
    
    // Date d'expiration
    const expiryDate = document.getElementById('expiry-date').value;
    const expiryRegex = /^(0[1-9]|1[0-2])\/([0-9]{2})$/;
    if (!expiryRegex.test(expiryDate)) {
        alert('Veuillez saisir une date d\'expiration valide (MM/AA).');
        return false;
    }
    
    // CVV
    const cvv = document.getElementById('cvv').value;
    if (cvv.length < 3) {
        alert('Veuillez saisir un code CVV valide.');
        return false;
    }
    
    // Adresse
    const address = document.getElementById('address').value.trim();
    if (address.length < 5) {
        alert('Veuillez saisir une adresse valide.');
        return false;
    }
    
    // Ville
    const city = document.getElementById('city').value.trim();
    if (city.length < 2) {
        alert('Veuillez saisir une ville valide.');
        return false;
    }
    
    // Code postal
    const postalCode = document.getElementById('postal-code').value.trim();
    if (postalCode.length < 4) {
        alert('Veuillez saisir un code postal valide.');
        return false;
    }
    
    // Conditions générales
    const termsCheckbox = document.getElementById('terms-checkbox');
    if (!termsCheckbox.checked) {
        alert('Vous devez accepter les conditions générales et la politique de confidentialité.');
        return false;
    }
    
    return true;
}

// Traitement du paiement
function processPayment() {
    // Afficher le modal de traitement
    const processingModal = new bootstrap.Modal(document.getElementById('paymentProcessingModal'));
    processingModal.show();
    
    // Simuler une progression
    const progressBar = document.getElementById('payment-progress');
    const processingMessage = document.getElementById('processing-message');
    let progress = 0;
    
    const progressInterval = setInterval(() => {
        progress += 5;
        progressBar.style.width = `${progress}%`;
        
        if (progress === 30) {
            processingMessage.textContent = 'Vérification des informations...';
        } else if (progress === 60) {
            processingMessage.textContent = 'Traitement du paiement...';
        } else if (progress === 90) {
            processingMessage.textContent = 'Finalisation...';
        }
        
        if (progress >= 100) {
            clearInterval(progressInterval);
            
            // Générer un ID de commande
            const timestamp = new Date().getTime().toString().slice(-6);
            paymentData.orderId = `CS-${timestamp}`;
            
            // Stocker les données de paiement
            sessionStorage.setItem('paymentData', JSON.stringify(paymentData));
            
            // Simuler un appel API pour créer l'abonnement
            simulateApiCall()
                .then(() => {
                    // Rediriger vers la page de confirmation
                    window.location.href = 'confirmation.html';
                })
                .catch(error => {
                    console.error('Erreur lors de la création de l\'abonnement:', error);
                    alert('Une erreur est survenue lors du traitement du paiement. Veuillez réessayer.');
                    processingModal.hide();
                });
        }
    }, 100);
}

// Simulation d'un appel API pour créer l'abonnement
function simulateApiCall() {
    return fetch("/api/payments/process", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            plan: paymentData.plan,
            duration: paymentData.duration,
            amount: paymentData.amount,
            currency: paymentData.currency,
            email: paymentData.email,
            name: paymentData.name,
            card_number: paymentData.card_number,
            expiry_date: paymentData.expiry_date,
            cvv: paymentData.cvv,
            address: paymentData.address,
            city: paymentData.city,
            postal_code: paymentData.postal_code
        }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || 'Erreur réseau');
            });
        }
        return response.json();
    });
}

// Initialisation de la page de confirmation
function initConfirmationPage() {
    console.log('Initialisation de la page de confirmation');
    
    // Récupérer les données de paiement stockées
    const storedData = sessionStorage.getItem('paymentData');
    if (storedData) {
        paymentData = JSON.parse(storedData);
    } else {
        // Rediriger vers la page de sélection de plan si aucune donnée n'est disponible
        window.location.href = 'index.html';
        return;
    }
    
    // Mettre à jour les informations de confirmation
    updateConfirmationDetails();
}

// Mise à jour des détails de confirmation
function updateConfirmationDetails() {
    // Email
    const confirmationEmailElement = document.getElementById('confirmation-email');
    if (confirmationEmailElement) {
        confirmationEmailElement.textContent = paymentData.email;
    }
    
    // Numéro de commande
    const orderNumberElement = document.getElementById('order-number');
    if (orderNumberElement) {
        orderNumberElement.textContent = paymentData.orderId;
    }
    
    // Date
    const orderDateElement = document.getElementById('order-date');
    if (orderDateElement) {
        const today = new Date();
        const day = String(today.getDate()).padStart(2, '0');
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const year = today.getFullYear();
        orderDateElement.textContent = `${day}/${month}/${year}`;
    }
    
    // Plan et durée
    const orderPlanElement = document.getElementById('order-plan');
    if (orderPlanElement) {
        const planName = paymentData.plan === 'pro' ? 'Pro' : 'Entreprise';
        let durationText = '';
        
        if (paymentData.duration === 1) {
            durationText = '1 mois';
        } else if (paymentData.duration === 3) {
            durationText = '3 mois';
        } else if (paymentData.duration === 12) {
            durationText = '1 an';
        }
        
        orderPlanElement.textContent = `${planName} - ${durationText}`;
    }
    
    // Montant
    const orderAmountElement = document.getElementById('order-amount');
    if (orderAmountElement) {
        orderAmountElement.textContent = `${paymentData.amount.toLocaleString()} ${paymentData.currency}`;
    }
}
