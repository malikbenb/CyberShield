// Fichier: frontend/js/dashboard.js

const API_BASE_URL_DASHBOARD = "."; // Utiliser des chemins relatifs depuis les pages du dashboard

// Fonction utilitaire pour effectuer des appels fetch authentifiés (gère les cookies de session)
async function fetchWithAuth(url, options = {}) {
    // S'assurer que les informations d'identification (cookies) sont envoyées avec la requête
    options.credentials = options.credentials || 'include'; 
    
    const response = await fetch(url, options);

    if (response.status === 401) {
        // Non authentifié, rediriger vers la page de connexion
        console.warn("Non authentifié. Redirection vers la connexion...");
        window.location.href = 'login.html'; 
        // Retourner une promesse qui ne se résout jamais pour arrêter le traitement ultérieur
        return new Promise(() => {}); 
    }

    return response;
}

// Fonction pour récupérer et afficher les informations de l'utilisateur
async function displayUserInfo() {
    const userNameElement = document.getElementById('user-name');
    const userEmailElement = document.getElementById('user-email');
    const userAvatarElement = document.getElementById('user-avatar');

    if (!userNameElement || !userEmailElement || !userAvatarElement) {
        console.warn("Éléments d'information utilisateur non trouvés dans le DOM.");
        return;
    }

    try {
        const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/auth/status`);
        if (!response.ok) {
            // La redirection vers login.html est déjà gérée par fetchWithAuth en cas de 401
            // Gérer d'autres erreurs si nécessaire
            throw new Error(`Erreur lors de la récupération du statut: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.loggedIn && data.user) {
            userNameElement.textContent = `${data.user.firstName} ${data.user.lastName}`;
            userEmailElement.textContent = data.user.email;
            // Créer un avatar simple avec les initiales
            const initials = `${data.user.firstName.charAt(0)}${data.user.lastName.charAt(0)}`.toUpperCase();
            userAvatarElement.textContent = initials;
        } else {
             // Normalement géré par le 401, mais sécurité supplémentaire
            console.warn("Utilisateur non connecté selon l'API.");
            window.location.href = 'login.html';
        }
    } catch (error) {
        console.error("Erreur lors de l'affichage des informations utilisateur:", error);
        // Afficher un message d'erreur ou rediriger
        userNameElement.textContent = "Erreur";
        userEmailElement.textContent = "Impossible de charger les données";
        userAvatarElement.textContent = "!";
        // Potentiellement rediriger vers login après un délai si l'erreur persiste
        // setTimeout(() => { window.location.href = 'login.html'; }, 3000);
    }
}

// Fonction de déconnexion
async function logout() {
    try {
        const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/auth/logout`, {
            method: 'POST',
        });
        
        if (response.ok) {
            console.log("Déconnexion réussie.");
            window.location.href = 'login.html'; // Rediriger vers la page de connexion
        } else {
            const data = await response.json();
            alert(`Erreur lors de la déconnexion: ${data.message || response.statusText}`);
        }
    } catch (error) {
        console.error("Erreur réseau lors de la déconnexion:", error);
        alert("Erreur réseau lors de la tentative de déconnexion.");
    }
}

// --- Initialisation et logique spécifique aux pages --- 

document.addEventListener('DOMContentLoaded', () => {
    // Vérifier l'authentification et afficher les infos utilisateur sur toutes les pages du dashboard
    displayUserInfo();

    // Ajouter l'événement de déconnexion au bouton
    const logoutButton = document.getElementById('logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', logout);
    }

    // --- Logique spécifique à chaque page --- 

    // Page: Tableau de Bord (index.html)
    if (document.body.contains(document.getElementById('recent-scans-table'))) {
        loadDashboardData();
        setupReportModal(); // Configurer le modal sur cette page aussi
    }

    // Page: Historique (history.html)
    if (document.body.contains(document.getElementById('full-history-table'))) {
        loadFullHistory();
        setupReportModal(); // Configurer le modal
    }

    // Page: Profil (profile.html)
    if (document.body.contains(document.getElementById('profile-form'))) {
        loadProfileData();
        setupProfileForms();
    }
    
    // Page: Téléchargements (download.html)
    if (document.body.contains(document.querySelector('.download-pro-btn'))) {
        setupDownloadButtons();
    }

});

// --- Fonctions pour les pages spécifiques --- 

// Fonction pour charger les données du tableau de bord (index.html)
async function loadDashboardData() {
    const totalScansElement = document.getElementById('total-scans');
    const averageScoreElement = document.getElementById('average-score');
    const lastScanDateElement = document.getElementById('last-scan-date');
    const recentScansTableBody = document.querySelector('#recent-scans-table tbody');

    if (!recentScansTableBody) return;

    try {
        const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/history`);
        if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
        
        const history = await response.json();

        // Mettre à jour les widgets
        totalScansElement.textContent = history.length;
        if (history.length > 0) {
            const completedScans = history.filter(scan => scan.status === 'completed' && scan.score !== null);
            if (completedScans.length > 0) {
                const totalScore = completedScans.reduce((sum, scan) => sum + scan.score, 0);
                averageScoreElement.textContent = (totalScore / completedScans.length).toFixed(1);
            } else {
                averageScoreElement.textContent = 'N/A';
            }
            // Trouver la date la plus récente
            const latestScan = history.reduce((latest, current) => 
                new Date(current.start_time) > new Date(latest.start_time) ? current : latest
            );
            lastScanDateElement.textContent = new Date(latestScan.start_time).toLocaleDateString('fr-FR');
        } else {
            averageScoreElement.textContent = 'N/A';
            lastScanDateElement.textContent = 'Jamais';
        }

        // Afficher les 5 scans les plus récents
        recentScansTableBody.innerHTML = ''; // Vider le contenu existant
        const recentScans = history.slice(0, 5);

        if (recentScans.length === 0) {
            recentScansTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Aucun scan récent trouvé.</td></tr>';
        } else {
            recentScans.forEach(scan => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(scan.start_time).toLocaleString('fr-FR')}</td>
                    <td>${scan.target_ip || 'N/A'}</td>
                    <td><span class="status status-${scan.status.toLowerCase()}">${scan.status}</span></td>
                    <td>${scan.score !== null ? scan.score : 'N/A'}</td>
                    <td>
                        ${scan.report_available ? 
                            `<button class="action-btn view-report-btn" data-scan-id="${scan.id}" title="Voir le rapport"><i class="fas fa-file-alt"></i></button>` : 
                            '<span title="Rapport non disponible">-</span>'
                        }
                    </td>
                `;
                recentScansTableBody.appendChild(row);
            });
            // Ajouter les écouteurs pour les boutons de rapport
            addReportButtonListeners(recentScansTableBody);
        }

    } catch (error) {
        console.error("Erreur lors du chargement des données du tableau de bord:", error);
        recentScansTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--cyber-alert);">Erreur lors du chargement de l\'historique.</td></tr>';
        // Mettre à jour les widgets pour indiquer l'erreur
        totalScansElement.textContent = 'Erreur';
        averageScoreElement.textContent = 'Erreur';
        lastScanDateElement.textContent = 'Erreur';
    }
}

// Fonction pour charger l'historique complet (history.html)
async function loadFullHistory() {
    const historyTableBody = document.querySelector('#full-history-table tbody');
    if (!historyTableBody) return;

    historyTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Chargement de l\'historique complet...</td></tr>';

    try {
        const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/history`);
        if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
        
        const history = await response.json();

        historyTableBody.innerHTML = ''; // Vider le contenu

        if (history.length === 0) {
            historyTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Aucun scan trouvé dans l\'historique.</td></tr>';
        } else {
            history.forEach(scan => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(scan.start_time).toLocaleString('fr-FR')}</td>
                    <td>${scan.end_time ? new Date(scan.end_time).toLocaleString('fr-FR') : 'En cours/Inconnu'}</td>
                    <td>${scan.target_ip || 'N/A'}</td>
                    <td><span class="status status-${scan.status.toLowerCase()}">${scan.status}</span></td>
                    <td>${scan.score !== null ? scan.score : 'N/A'}</td>
                    <td>
                         ${scan.report_available ? 
                            `<button class="action-btn view-report-btn" data-scan-id="${scan.id}" title="Voir le rapport"><i class="fas fa-file-alt"></i></button>` : 
                            '<span title="Rapport non disponible">-</span>'
                        }
                        <!-- Ajouter d'autres actions si nécessaire (ex: supprimer ?) -->
                    </td>
                `;
                historyTableBody.appendChild(row);
            });
            // Ajouter les écouteurs pour les boutons de rapport
            addReportButtonListeners(historyTableBody);
        }

    } catch (error) {
        console.error("Erreur lors du chargement de l'historique complet:", error);
        historyTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--cyber-alert);">Erreur lors du chargement de l\'historique.</td></tr>';
    }
}

// Fonction pour charger les données du profil (profile.html)
async function loadProfileData() {
    const firstNameInput = document.getElementById('profile-firstName');
    const lastNameInput = document.getElementById('profile-lastName');
    const emailInput = document.getElementById('profile-email');

    if (!firstNameInput || !lastNameInput || !emailInput) return;

    try {
        const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/profile`);
        if (!response.ok) throw new Error(`Erreur API: ${response.statusText}`);
        
        const profile = await response.json();
        firstNameInput.value = profile.firstName;
        lastNameInput.value = profile.lastName;
        emailInput.value = profile.email;

    } catch (error) {
        console.error("Erreur lors du chargement des données du profil:", error);
        displayMessage(document.getElementById('profile-error-message'), "Impossible de charger les informations du profil.");
    }
}

// Fonction pour configurer les formulaires de profil (profile.html)
function setupProfileForms() {
    const profileForm = document.getElementById('profile-form');
    const passwordForm = document.getElementById('password-form');
    const profileErrorMsg = document.getElementById('profile-error-message');
    const profileSuccessMsg = document.getElementById('profile-success-message');
    const passwordErrorMsg = document.getElementById('password-error-message');
    const passwordSuccessMsg = document.getElementById('password-success-message');

    // Fonction générique pour afficher les messages
    function displayFormMessage(element, message, isError = true) {
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            element.className = isError ? 'error-message' : 'success-message';
            // Masquer après quelques secondes
            setTimeout(() => { element.style.display = 'none'; }, 4000);
        } else {
            console.error("Élément de message de formulaire non trouvé");
        }
    }

    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const firstName = document.getElementById('profile-firstName').value;
            const lastName = document.getElementById('profile-lastName').value;
            const email = document.getElementById('profile-email').value;

            try {
                const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/profile`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ firstName, lastName, email })
                });
                const data = await response.json();
                if (response.ok) {
                    displayFormMessage(profileSuccessMsg, data.message || "Profil mis à jour.", false);
                    displayUserInfo(); // Mettre à jour la sidebar
                } else {
                    displayFormMessage(profileErrorMsg, data.message || "Erreur lors de la mise à jour.");
                }
            } catch (error) {
                console.error("Erreur réseau lors de la mise à jour du profil:", error);
                displayFormMessage(profileErrorMsg, "Erreur réseau.");
            }
        });
    }

    if (passwordForm) {
        passwordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;

            if (newPassword !== confirmNewPassword) {
                displayFormMessage(passwordErrorMsg, "Les nouveaux mots de passe ne correspondent pas.");
                return;
            }
            if (newPassword.length < 6) { // Ajouter une validation de base
                 displayFormMessage(passwordErrorMsg, "Le mot de passe doit contenir au moins 6 caractères.");
                return;
            }

            try {
                const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/profile`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    // Envoyer uniquement le mot de passe pour le changement
                    body: JSON.stringify({ password: newPassword })
                });
                const data = await response.json();
                 if (response.ok) {
                    displayFormMessage(passwordSuccessMsg, data.message || "Mot de passe mis à jour.", false);
                    passwordForm.reset(); // Vider les champs
                } else {
                    displayFormMessage(passwordErrorMsg, data.message || "Erreur lors de la mise à jour.");
                }
            } catch (error) {
                 console.error("Erreur réseau lors du changement de mot de passe:", error);
                displayFormMessage(passwordErrorMsg, "Erreur réseau.");
            }
        });
    }
}

// --- Fonctions pour le Modal de Rapport --- 

let reportModal = null;
let closeModalButton = null;
let reportModalBody = null;

function setupReportModal() {
    reportModal = document.getElementById('report-modal');
    closeModalButton = document.getElementById('close-report-modal');
    reportModalBody = document.getElementById('report-modal-body');

    if (!reportModal || !closeModalButton || !reportModalBody) {
        console.warn("Éléments du modal de rapport non trouvés.");
        return;
    }

    closeModalButton.onclick = () => {
        reportModal.style.display = 'none';
    };

    // Fermer si on clique en dehors du contenu
    window.onclick = (event) => {
        if (event.target == reportModal) {
            reportModal.style.display = 'none';
        }
    };
}

function addReportButtonListeners(container) {
    container.querySelectorAll('.view-report-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const scanId = button.dataset.scanId;
            if (!reportModal || !reportModalBody) {
                console.error("Modal non initialisé.");
                return;
            }
            
            reportModalBody.innerHTML = '<p>Chargement du rapport...</p>';
            reportModal.style.display = 'block';
            document.getElementById('report-modal-title').textContent = `Rapport du Scan #${scanId}`;

            try {
                const response = await fetchWithAuth(`${API_BASE_URL_DASHBOARD}/api/dashboard/report/${scanId}`);
                if (!response.ok) {
                     const errorData = await response.json();
                    throw new Error(errorData.message || `Erreur API: ${response.statusText}`);
                }
                const reportData = await response.json();
                
                // Afficher le contenu du rapport (supposé être du texte ou JSON formaté)
                // Pour du JSON, on pourrait le formater joliment
                let reportContentHtml = '';
                if (reportData.format === 'json') {
                    try {
                        const contentObj = JSON.parse(reportData.content);
                        // Formater le JSON pour l'affichage
                        reportContentHtml = `<pre>${JSON.stringify(contentObj, null, 2)}</pre>`; 
                    } catch (parseError) {
                        console.error("Erreur de parsing JSON du rapport:", parseError);
                        // Afficher le contenu brut si le parsing échoue
                        reportContentHtml = `<pre>${reportData.content}</pre>`;
                    }
                } else {
                    // Afficher comme texte préformaté par défaut
                    reportContentHtml = `<pre>${reportData.content}</pre>`;
                }
                reportModalBody.innerHTML = reportContentHtml;

            } catch (error) {
                console.error(`Erreur lors du chargement du rapport ${scanId}:`, error);
                reportModalBody.innerHTML = `<p style="color: var(--cyber-alert);">Impossible de charger le rapport : ${error.message}</p>`;
            }
        });
    });
}

// --- Fonction pour les boutons de téléchargement Pro --- 

function setupDownloadButtons() {
    document.querySelectorAll('.download-pro-btn').forEach(button => {
        button.addEventListener('click', () => {
            const os = button.dataset.os;
            // TODO: Implémenter la logique de téléchargement pour les scanners Pro.
            // Cela pourrait impliquer:
            // 1. Avoir des liens directs vers des fichiers statiques (si les scanners sont pré-compilés et identiques pour tous les utilisateurs Pro).
            // 2. Avoir une route API (/api/dashboard/download/pro/{os}) qui renvoie le fichier approprié après vérification de l'authentification.
            
            // Pour l'instant, afficher une alerte
            alert(`Le téléchargement du scanner Pro pour ${os} n'est pas encore implémenté dans cette démo.`);
            
            // Exemple avec lien statique (si les fichiers existent dans client/scanners/ par exemple)
            /*
            let downloadUrl = '';
            let fileName = '';
            if (os === 'windows') {
                downloadUrl = '../client/scanners/windows/WindowsProScan.exe'; // Ajuster le chemin
                fileName = 'CyberShield_Windows_ProScan.exe';
            } else if (os === 'linux') {
                downloadUrl = '../client/scanners/linux/linux_scan_pro.sh'; // Ajuster le chemin
                fileName = 'CyberShield_Linux_ProScan.sh';
            } else if (os === 'macos') {
                downloadUrl = '../client/scanners/macos/macos_scan_pro.sh'; // Ajuster le chemin
                fileName = 'CyberShield_MacOS_ProScan.sh';
            }

            if (downloadUrl) {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                alert('Fichier non trouvé pour ce système.');
            }
            */
        });
    });
}

