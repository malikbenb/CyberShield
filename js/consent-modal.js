// Fonction pour créer et afficher le modal de consentement
function showConsentModal(os, version, callback) {
    // Vérifier si un modal existe déjà et le supprimer si c'est le cas
    const existingModal = document.querySelector('.consent-modal-overlay');
    if (existingModal) {
        existingModal.remove();
    }

    // Créer l'overlay du modal
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'consent-modal-overlay';
    
    // Créer le contenu du modal
    const modalContent = document.createElement('div');
    modalContent.className = 'consent-modal';
    
    // Créer l'en-tête du modal
    const modalHeader = document.createElement('div');
    modalHeader.className = 'consent-modal-header';
    
    const modalTitle = document.createElement('h2');
    modalTitle.textContent = 'Réglementations en Cybersécurité - Algérie';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'consent-modal-close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });
    
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    
    // Créer le corps du modal avec le contenu direct (sans iframe)
    const modalBody = document.createElement('div');
    modalBody.className = 'consent-modal-body';
    
    // Contenu du modal directement intégré
    modalBody.innerHTML = `
        <div class="regulations-content">
            <div class="warning-section">
                <h3><i class="fas fa-exclamation-triangle"></i> Avis Important</h3>
                <p>En téléchargeant ce scanner de vulnérabilités, vous acceptez d'en assumer l'entière responsabilité légale conformément aux lois algériennes en vigueur.</p>
            </div>
            
            <div class="legal-section">
                <h3><i class="fas fa-gavel"></i> Cadre Légal Algérien</h3>
                <p>Votre utilisation de cet outil est encadrée par :</p>
                <ul>
                    <li><strong>Loi n° 09-04 du 5 août 2009</strong> - Relative à la prévention et à la lutte contre les infractions liées aux technologies de l'information</li>
                    <li><strong>Loi n° 18-07 du 10 juin 2018</strong> - Protection des données personnelles</li>
                    <li><strong>Décret présidentiel n° 20-05 du 20 Janvier 2020</strong> - Création de l'ANSSI</li>
                </ul>
                <p>Le non-respect de ces lois peut entraîner des amendes de <strong>50 000 DA à 2 000 000 DA</strong> et des peines d'emprisonnement de <strong>6 mois à 3 ans</strong>.</p>
            </div>
            
            <div class="responsibility-section">
                <h3><i class="fas fa-user-shield"></i> Votre Responsabilité</h3>
                <p>En tant qu'utilisateur, vous vous engagez formellement à :</p>
                <ul>
                    <li>N'utiliser cet outil que sur des systèmes dont vous êtes propriétaire ou pour lesquels vous disposez d'une autorisation explicite</li>
                    <li>Ne pas exploiter les vulnérabilités découvertes à des fins malveillantes</li>
                    <li>Ne pas scanner des infrastructures gouvernementales, militaires ou d'importance vitale sans habilitation</li>
                    <li>Respecter la confidentialité des informations obtenues</li>
                    <li>Signaler de manière responsable toute vulnérabilité découverte</li>
                </ul>
            </div>
            
            <div class="security-section">
                <h3><i class="fas fa-shield-alt"></i> Bonnes Pratiques</h3>
                <p>Pour une utilisation sécurisée et conforme :</p>
                <ul>
                    <li>Documentez toutes vos actions et conservez les preuves d'autorisation</li>
                    <li>Limitez la portée de vos scans aux systèmes explicitement autorisés</li>
                    <li>Suivez les recommandations de l'ANSSI pour la sécurisation des systèmes</li>
                    <li>Tenez-vous informé des évolutions législatives en matière de cybersécurité</li>
                </ul>
            </div>
            
            <div class="disclaimer-section">
                <h3><i class="fas fa-info-circle"></i> Avis de Non-Responsabilité</h3>
                <p>CyberShield Algeria ne pourra être tenue responsable des conséquences d'une utilisation inappropriée ou illégale de cet outil. Vous assumez l'entière responsabilité juridique et éthique de vos actions.</p>
            </div>
        </div>
    `;
    
    // Ajouter le style CSS directement dans le modal
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .consent-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        }
        
        .consent-modal {
            max-width: 700px;
            max-height: 80vh;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
            position: relative;
            margin: auto;
        }
        
        .consent-modal-header {
            background-color: #005a87;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .consent-modal-header h2 {
            margin: 0;
            font-size: 22px;
            font-weight: 600;
        }
        
        .consent-modal-close {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        
        .consent-modal-body {
            padding: 0;
            overflow-y: auto;
            max-height: calc(80vh - 130px);
        }
        
        .regulations-content {
            padding: 20px;
        }
        
        .regulations-content h3 {
            color: #005a87;
            margin-top: 20px;
            margin-bottom: 15px;
            font-size: 18px;
            display: flex;
            align-items: center;
        }
        
        .regulations-content h3 i {
            margin-right: 10px;
            color: #005a87;
        }
        
        .regulations-content p {
            margin-bottom: 15px;
            line-height: 1.6;
            color: #333;
            font-size: 15px;
        }
        
        .regulations-content ul {
            margin-bottom: 15px;
            padding-left: 20px;
        }
        
        .regulations-content li {
            margin-bottom: 8px;
            line-height: 1.5;
            color: #333;
            font-size: 15px;
        }
        
        .regulations-content strong {
            color: #005a87;
            font-weight: 600;
        }
        
        .warning-section {
            background-color: #fff8e6;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        
        .warning-section h3 {
            color: #856404;
            margin-top: 0;
        }
        
        .warning-section h3 i {
            color: #856404;
        }
        
        .legal-section {
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border-left: 5px solid #005a87;
        }
        
        .responsibility-section {
            background-color: #e8f4f8;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border-left: 5px solid #17a2b8;
        }
        
        .security-section {
            background-color: #f0f9ff;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border-left: 5px solid #0d6efd;
        }
        
        .disclaimer-section {
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 5px solid #6c757d;
        }
        
        .consent-modal-footer {
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }
        
        .consent-checkbox-container {
            display: flex;
            align-items: center;
        }
        
        .consent-checkbox {
            margin-right: 10px;
            width: 18px;
            height: 18px;
        }
        
        .consent-checkbox-label {
            font-size: 15px;
            color: #333;
        }
        
        .consent-decline {
            background-color: #f8f9fa;
            color: #6c757d;
            border: 1px solid #6c757d;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 15px;
            transition: all 0.2s;
        }
        
        .consent-decline:hover {
            background-color: #e9ecef;
        }
        
        .consent-agree {
            background-color: #005a87;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 15px;
            transition: all 0.2s;
        }
        
        .consent-agree:hover:not(:disabled) {
            background-color: #004a70;
        }
        
        .consent-agree:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
            opacity: 0.7;
        }
        
        @media (max-width: 768px) {
            .consent-modal {
                width: 95%;
                max-height: 85vh;
            }
            
            .consent-modal-footer {
                flex-direction: column;
                gap: 15px;
            }
            
            .consent-checkbox-container {
                width: 100%;
                margin-bottom: 10px;
            }
            
            .consent-decline, .consent-agree {
                width: 100%;
            }
        }
    `;
    
    document.head.appendChild(styleElement);
    
    // Créer le pied de page du modal avec les boutons
    const modalFooter = document.createElement('div');
    modalFooter.className = 'consent-modal-footer';
    
    const checkboxContainer = document.createElement('div');
    checkboxContainer.className = 'consent-checkbox-container';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'consent-checkbox';
    checkbox.id = 'consent-checkbox';
    
    const checkboxLabel = document.createElement('label');
    checkboxLabel.htmlFor = 'consent-checkbox';
    checkboxLabel.className = 'consent-checkbox-label';
    checkboxLabel.textContent = 'J\'ai lu et j\'accepte les conditions d\'utilisation';
    
    checkboxContainer.appendChild(checkbox);
    checkboxContainer.appendChild(checkboxLabel);
    
    const declineButton = document.createElement('button');
    declineButton.className = 'consent-decline';
    declineButton.textContent = 'Refuser';
    declineButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });
    
    const agreeButton = document.createElement('button');
    agreeButton.className = 'consent-agree';
    agreeButton.textContent = 'J\'accepte les conditions';
    agreeButton.disabled = true;
    
    // Activer le bouton d'acceptation uniquement lorsque la case est cochée
    checkbox.addEventListener('change', () => {
        agreeButton.disabled = !checkbox.checked;
    });
    
    // Lorsque l'utilisateur accepte, fermer le modal et exécuter le callback
    agreeButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
        if (callback) callback(os, version);
    });
    
    modalFooter.appendChild(checkboxContainer);
    modalFooter.appendChild(declineButton);
    modalFooter.appendChild(agreeButton);
    
    // Assembler le modal
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    
    modalOverlay.appendChild(modalContent);
    
    // Ajouter le modal au document
    document.body.appendChild(modalOverlay);
}
