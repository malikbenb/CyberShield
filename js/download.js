// Fonction pour télécharger les scanners
window.downloadScanner = function(os, version) {
    // Définir les chemins des fichiers exécutables selon la version
    let scannerUrl = '';
    let fileName = '';
    
    if (version === 'pro') {
        // Version Pro - Connexion via Docker
        if (os === 'windows') {
            scannerUrl = '/api/download/pro/windows';
            fileName = 'CyberShieldPro_Windows.exe';
        } else if (os === 'macos') {
            scannerUrl = '/api/download/pro/macos';
            fileName = 'cybershield_pro_macos.sh';
        } else if (os === 'linux') {
            scannerUrl = '/api/download/pro/linux';
            fileName = 'cybershield_pro_linux.sh';
        }
    } else {
        // Version gratuite
        if (os === 'windows') {
            scannerUrl = '/scanners/windows/WindowsFreeScan.exe';
            fileName = 'WindowsFreeScan.exe';
        } else if (os === 'macos') {
            scannerUrl = '/scanners/macos/macos_scan_free.sh';
            fileName = 'macos_scan_free.sh';
        } else if (os === 'linux') {
            scannerUrl = '/scanners/linux/linux_scan_free.sh';
            fileName = 'linux_scan_free.sh';
        }
    }
    
    if (scannerUrl) {
        if (version === 'pro') {
            // Pour la version Pro, afficher des instructions supplémentaires
            showProInstructions(os);
        }
        
        // Créer un élément de lien pour le téléchargement
        const link = document.createElement('a');
        link.href = scannerUrl;
        link.download = fileName;
        
        // Ajouter temporairement le lien au document, cliquer dessus, puis le supprimer
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Afficher un message de confirmation
        const osName = os.charAt(0).toUpperCase() + os.slice(1);
        const versionName = version === 'free' ? 'gratuit' : 'pro';
        showNotification(`Téléchargement du scanner ${versionName} pour ${osName} démarré.`, 'success');
    }
}

// Fonction pour afficher les instructions spécifiques à la version Pro
function showProInstructions(os) {
    // Créer l'overlay du modal
    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'pro-instructions-overlay';
    
    // Créer le contenu du modal
    const modalContent = document.createElement('div');
    modalContent.className = 'pro-instructions-modal';
    
    // Créer l'en-tête du modal
    const modalHeader = document.createElement('div');
    modalHeader.className = 'pro-instructions-header';
    
    const modalTitle = document.createElement('h2');
    modalTitle.textContent = 'Instructions pour la Version Pro';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'pro-instructions-close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });
    
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    
    // Créer le corps du modal
    const modalBody = document.createElement('div');
    modalBody.className = 'pro-instructions-body';
    
    let instructions = '';
    if (os === 'windows') {
        instructions = `
            <p>Pour utiliser le scanner Pro avec Docker :</p>
            <ol>
                <li>Exécutez le fichier téléchargé avec des privilèges administrateur</li>
                <li>Le scanner se connectera automatiquement à notre serveur Docker</li>
                <li>Suivez les instructions à l'écran pour lancer votre scan</li>
            </ol>
            <p>En cas de problème de connexion, vérifiez que :</p>
            <ul>
                <li>Votre pare-feu autorise les connexions sortantes</li>
                <li>Vous disposez d'une connexion Internet stable</li>
            </ul>
        `;
    } else if (os === 'macos') {
        instructions = `
            <p>Pour utiliser le scanner Pro avec Docker :</p>
            <ol>
                <li>Ouvrez un terminal et rendez le script exécutable : <code>chmod +x cybershield_pro_macos.sh</code></li>
                <li>Exécutez le script avec sudo : <code>sudo ./cybershield_pro_macos.sh</code></li>
                <li>Le scanner se connectera automatiquement à notre serveur Docker</li>
                <li>Suivez les instructions à l'écran pour lancer votre scan</li>
            </ol>
            <p>En cas de problème de connexion, vérifiez que :</p>
            <ul>
                <li>Votre pare-feu autorise les connexions sortantes</li>
                <li>Vous disposez d'une connexion Internet stable</li>
            </ul>
        `;
    } else if (os === 'linux') {
        instructions = `
            <p>Pour utiliser le scanner Pro avec Docker :</p>
            <ol>
                <li>Ouvrez un terminal et rendez le script exécutable : <code>chmod +x cybershield_pro_linux.sh</code></li>
                <li>Exécutez le script avec sudo : <code>sudo ./cybershield_pro_linux.sh</code></li>
                <li>Le scanner se connectera automatiquement à notre serveur Docker</li>
                <li>Suivez les instructions à l'écran pour lancer votre scan</li>
            </ol>
            <p>En cas de problème de connexion, vérifiez que :</p>
            <ul>
                <li>Votre pare-feu autorise les connexions sortantes</li>
                <li>Vous disposez d'une connexion Internet stable</li>
            </ul>
        `;
    }
    
    modalBody.innerHTML = instructions;
    
    // Créer le pied de page du modal
    const modalFooter = document.createElement('div');
    modalFooter.className = 'pro-instructions-footer';
    
    const closeModalButton = document.createElement('button');
    closeModalButton.className = 'pro-instructions-button';
    closeModalButton.textContent = 'J\'ai compris';
    closeModalButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });
    
    modalFooter.appendChild(closeModalButton);
    
    // Assembler le modal
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    
    modalOverlay.appendChild(modalContent);
    
    // Ajouter le style CSS pour le modal
    const style = document.createElement('style');
    style.textContent = `
        .pro-instructions-overlay {
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
        
        .pro-instructions-modal {
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .pro-instructions-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background-color: #005a87;
            color: white;
        }
        
        .pro-instructions-header h2 {
            margin: 0;
            font-size: 20px;
        }
        
        .pro-instructions-close {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        
        .pro-instructions-body {
            padding: 20px;
            overflow-y: auto;
            flex-grow: 1;
            line-height: 1.6;
        }
        
        .pro-instructions-body p {
            margin-bottom: 15px;
        }
        
        .pro-instructions-body ol, .pro-instructions-body ul {
            margin-bottom: 15px;
            padding-left: 25px;
        }
        
        .pro-instructions-body li {
            margin-bottom: 8px;
        }
        
        .pro-instructions-body code {
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        
        .pro-instructions-footer {
            padding: 15px 20px;
            display: flex;
            justify-content: flex-end;
            border-top: 1px solid #eee;
        }
        
        .pro-instructions-button {
            background-color: #005a87;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .pro-instructions-button:hover {
            background-color: #004a70;
        }
    `;
    document.head.appendChild(style);
    
    // Ajouter le modal au document
    document.body.appendChild(modalOverlay);
}

// Ajouter des écouteurs d'événements aux boutons de téléchargement
document.addEventListener('DOMContentLoaded', function() {
    const downloadButtons = document.querySelectorAll('.download-btn');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const os = this.getAttribute('data-os');
            const version = this.getAttribute('data-version');
            
            // Afficher le modal de consentement avant le téléchargement
            showConsentModal(os, version, downloadScanner);
        });
    });
});

// Fonction pour afficher des notifications
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Ajouter l'icône appropriée
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    if (type === 'error') icon = 'times-circle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <button class="close-notification"><i class="fas fa-times"></i></button>
    `;
    
    // Ajouter au DOM
    const notificationsContainer = document.querySelector('.notifications-container') || createNotificationsContainer();
    notificationsContainer.appendChild(notification);
    
    // Ajouter l'écouteur pour fermer la notification
    notification.querySelector('.close-notification').addEventListener('click', function() {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-fermeture après 5 secondes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// Créer le conteneur de notifications s'il n'existe pas
function createNotificationsContainer() {
    const container = document.createElement('div');
    container.className = 'notifications-container';
    document.body.appendChild(container);
    
    // Ajouter le style CSS pour les notifications
    const style = document.createElement('style');
    style.textContent = `
        .notifications-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
        }
        
        .notification {
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            border-left: 4px solid #0af;
            padding: 15px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slide-in 0.3s ease-out forwards;
            backdrop-filter: blur(5px);
        }
        
        .notification.success {
            border-left-color: #0f0;
        }
        
        .notification.warning {
            border-left-color: #ff0;
        }
        
        .notification.error {
            border-left-color: #f00;
        }
        
        .notification i {
            margin-right: 10px;
            font-size: 18px;
        }
        
        .notification .close-notification {
            margin-left: auto;
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        
        .notification .close-notification:hover {
            opacity: 1;
        }
        
        .notification.fade-out {
            animation: fade-out 0.3s ease-out forwards;
        }
        
        @keyframes slide-in {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes fade-out {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    return container;
}
