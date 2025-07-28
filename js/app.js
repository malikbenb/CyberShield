document.addEventListener("DOMContentLoaded", () => {
    // Animation du terminal
    const terminal = document.getElementById("terminal-output");
    if (terminal) {
        const commands = [
            { text: "Initializing CyberShield Scanner...", delay: 500 },
            { text: "Checking system requirements...", delay: 500 },
            { text: "Loading vulnerability database...", delay: 500 },
            { text: "Establishing secure connection...", delay: 500 },
            { text: "Ready to scan >>>", delay: 500, class: "ready" }
        ];

        function typeWriter(text, element, speed, callback) {
            let i = 0;
            function typing() {
                if (i < text.length) {
                    element.innerHTML += text.charAt(i);
                    i++;
                    setTimeout(typing, speed);
                } else if (callback) {
                    callback();
                }
            }
            typing();
        }

        function runTerminalAnimation() {
        // Nettoyer le terminal
        terminal.innerHTML = "";
    
        // Nouveau : calculer la durée totale d'écriture de chaque ligne
        const typingSpeed = 30; // ms par caractère
    
        let totalDelay = 0;
    
        commands.forEach((cmd, index) => {
        // Calculer le temps nécessaire pour écrire cette ligne
        const lineDuration = cmd.text.length * typingSpeed;
        
        // Créer la ligne après le délai accumulé
        setTimeout(() => {
            const line = document.createElement("div");
            line.className = `terminal-line ${cmd.class || ""}`;
            terminal.appendChild(line);
            
            // Afficher le texte caractère par caractère
            typeWriter(cmd.text, line, typingSpeed, () => {
                if (index === commands.length - 1) {
                    line.innerHTML += " <span class=\"blink\">_</span>";
                    setTimeout(runTerminalAnimation, 3000); // Redémarrer après 3s
                    }
                });
            }, totalDelay);
        
        // Ajouter à notre délai total :
        // - le temps d'écriture de la ligne actuelle
        // - le délai supplémentaire spécifié dans cmd.delay
            totalDelay += lineDuration + cmd.delay;
        });
    }

        // Démarrer l'animation du terminal si l'élément existe
        runTerminalAnimation();
    }

    // Utiliser la fonction de téléchargement définie dans download.js
    // Cette fonction est vide car nous utilisons celle de download.js
    function downloadScannerApp(os, version) {
        // Appeler la fonction globale downloadScanner définie dans download.js
        if (typeof window.downloadScanner === 'function') {
            window.downloadScanner(os, version);
        } else {
            console.log("Utilisation de la fonction de téléchargement locale");
            // Fonction de secours si downloadScanner n'est pas disponible
            let scannerUrl = "";
            let fileName = "";

            // Définir les chemins corrects pour la version gratuite
            if (version === "free") {
                if (os === "windows") {
                    scannerUrl = "/scanners/windows/WindowsFreeScan.exe"; // Chemin absolu
                    fileName = "CyberShield_Windows_FreeScan.exe";
                } else if (os === "linux") {
                    scannerUrl = "/scanners/linux/linux_scan_free.sh";
                    fileName = "CyberShield_Linux_FreeScan.sh";
                } else if (os === "macos") {
                    scannerUrl = "/scanners/macos/macos_scan_free.sh";
                    fileName = "CyberShield_MacOS_FreeScan.sh";
                }
            } else {
                // Gérer le cas Pro (pour l'instant, afficher une alerte)
                alert("L'offre Pro nécessite une connexion. Le tableau de bord sera bientôt disponible.");
                return; // Ne pas continuer si c'est la version Pro
            }

            if (scannerUrl) {
                // Créer un lien temporaire pour le téléchargement
                const link = document.createElement("a");
                link.href = scannerUrl;
                link.download = fileName; // Nom du fichier suggéré au téléchargement
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                console.log(`Téléchargement lancé pour : ${fileName}`);
            } else {
                console.error("URL du scanner non trouvée pour", os, version);
                alert("Erreur : Fichier de scan non trouvé.");
            }
        }
    }

    // Gestion du téléchargement via les boutons
    document.querySelectorAll(".download-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const os = btn.dataset.os;
            const version = btn.dataset.version;
            const originalText = btn.innerHTML;

            if (version === "pro") {
                // Pour la version Pro, rediriger vers la page de connexion
                window.location.href = "dashboard/login.html?redirect=pro&os=" + os;
                return;
            }

            // Afficher le modal de consentement pour la version gratuite
            // La fonction showConsentModal est définie dans consent-modal.js
            // Elle prend downloadScannerApp en callback
            if (typeof showConsentModal === "function") {
                 // Indiquer visuellement le chargement avant d'afficher le modal
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Préparation...';
                // Simuler un petit délai pour l'effet visuel si nécessaire
                setTimeout(() => {
                    showConsentModal(os, version, downloadScannerApp);
                    btn.innerHTML = originalText; // Restaurer le texte après l'ouverture du modal
                }, 300);
            } else {
                console.error("La fonction showConsentModal n'est pas définie.");
                alert("Erreur lors de l'initialisation du processus de téléchargement.");
                btn.innerHTML = originalText;
            }
        });
    });

    // Gestion du scroll fluide pour les liens d'ancre internes
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // S'assurer que la page s'ouvre toujours en haut (comportement par défaut, mais on peut forcer)
    // window.scrollTo({ top: 0, behavior: 'auto' });

    // Gérer le scroll vers l'ancre si présente dans l'URL au chargement
    if (window.location.hash) {
        const hash = window.location.hash;
        // Utiliser un léger délai pour s'assurer que tout est chargé
        setTimeout(() => {
            const targetElement = document.querySelector(hash);
            if (targetElement) {
                // Utiliser scrollIntoView avec le padding déjà géré par CSS
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
    }
});

