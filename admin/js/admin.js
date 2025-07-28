// JavaScript pour l'interface d'administration CyberShield

// Variables globales
let currentPage = 1;
let itemsPerPage = 10;
let currentAdminData = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Gestion du toggle sidebar sur mobile
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const sidebar = document.querySelector('.admin-sidebar');
    
    if (toggleSidebarBtn && sidebar) {
        toggleSidebarBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Gestion de la déconnexion
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
    
    // Initialisation spécifique à chaque page
    initPageSpecific();
    
    // Vérification de l'authentification
    checkAuthentication();
});

// Vérification de l'authentification
function checkAuthentication() {
    // Si on est sur la page de login, pas besoin de vérifier
    if (window.location.pathname.includes('login.html')) {
        return;
    }
    
    // Vérifier si l'admin est connecté
    const adminToken = localStorage.getItem('adminToken');
    if (!adminToken) {
        // Rediriger vers la page de login
        window.location.href = 'login.html';
    }
}

// Initialisation spécifique à chaque page
function initPageSpecific() {
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('login.html')) {
        initLoginPage();
    } else if (currentPath.includes('index.html') || currentPath.endsWith('/admin/')) {
        initDashboardPage();
    } else if (currentPath.includes('users.html')) {
        initUsersPage();
    } else if (currentPath.includes('subscriptions.html')) {
        initSubscriptionsPage();
    } else if (currentPath.includes('scans.html')) {
        initScansPage();
    } else if (currentPath.includes('settings.html')) {
        initSettingsPage();
    }
}

// Initialisation de la page de login
function initLoginPage() {
    const loginForm = document.getElementById('admin-login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simulation d'authentification (à remplacer par un appel API réel)
            if (username === 'admin' && password === 'admin123') {
                // Stocker le token d'authentification
                localStorage.setItem('adminToken', 'simulated_admin_token');
                localStorage.setItem('adminName', 'Admin');
                
                // Rediriger vers le dashboard
                window.location.href = 'index.html';
            } else {
                // Afficher l'erreur
                const errorDiv = document.getElementById('login-error');
                errorDiv.classList.remove('d-none');
            }
        });
    }
}

// Initialisation de la page dashboard
function initDashboardPage() {
    // Charger les statistiques
    loadDashboardStats();
    
    // Charger l'activité récente
    loadRecentActivity();
    
    // Initialiser le graphique des abonnements
    initSubscriptionChart();
    
    // Gestionnaire pour le bouton d'export
    const exportBtn = document.getElementById('export-data-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            alert('Export des données en cours...');
            // Logique d'export à implémenter
        });
    }
}

// Chargement des statistiques du dashboard
function loadDashboardStats() {
    // Simuler le chargement des données (à remplacer par un appel API réel)
    setTimeout(() => {
        document.getElementById('total-users').textContent = '156';
        document.getElementById('active-subscriptions').textContent = '87';
        document.getElementById('total-scans').textContent = '342';
        document.getElementById('expiring-soon').textContent = '12';
    }, 500);
}

// Chargement de l'activité récente
function loadRecentActivity() {
    const activityTable = document.getElementById('recent-activity');
    if (!activityTable) return;
    
    // Simuler le chargement des données (à remplacer par un appel API réel)
    const activities = [
        { user: 'Jean Dupont', action: 'Nouvel abonnement Pro', date: '26/05/2025 14:30', status: 'success' },
        { user: 'Marie Martin', action: 'Scan terminé', date: '26/05/2025 13:15', status: 'success' },
        { user: 'Pierre Durand', action: 'Modification profil', date: '26/05/2025 12:45', status: 'success' },
        { user: 'Sophie Lefebvre', action: 'Scan échoué', date: '26/05/2025 11:20', status: 'danger' },
        { user: 'Lucas Bernard', action: 'Nouvel abonnement Entreprise', date: '26/05/2025 10:05', status: 'success' }
    ];
    
    let html = '';
    activities.forEach(activity => {
        html += `
        <tr>
            <td>${activity.user}</td>
            <td>${activity.action}</td>
            <td>${activity.date}</td>
            <td><span class="badge bg-${activity.status}">${activity.status === 'success' ? 'Réussi' : 'Échec'}</span></td>
        </tr>
        `;
    });
    
    activityTable.innerHTML = html;
}

// Initialisation du graphique des abonnements
function initSubscriptionChart() {
    const chartCanvas = document.getElementById('subscription-chart');
    if (!chartCanvas || typeof Chart === 'undefined') return;
    
    const ctx = chartCanvas.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pro', 'Entreprise', 'Expirés'],
            datasets: [{
                data: [65, 22, 13],
                backgroundColor: ['#3498db', '#2c3e50', '#e74c3c'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Initialisation de la page utilisateurs
function initUsersPage() {
    // Charger la liste des utilisateurs
    loadUsers();
    
    // Gestionnaire pour le bouton d'ajout d'utilisateur
    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            openUserEditModal();
        });
    }
    
    // Gestionnaire pour le bouton de sauvegarde dans le modal
    const saveUserBtn = document.getElementById('save-user-btn');
    if (saveUserBtn) {
        saveUserBtn.addEventListener('click', function() {
            saveUser();
        });
    }
    
    // Gestionnaire pour le bouton de suppression dans le modal
    const deleteUserBtn = document.getElementById('delete-user-btn');
    if (deleteUserBtn) {
        deleteUserBtn.addEventListener('click', function() {
            deleteUser();
        });
    }
    
    // Gestionnaire pour la recherche
    const searchInput = document.getElementById('search-users');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            loadUsers(this.value);
        });
    }
    
    // Gestionnaires pour les filtres
    const filterSubscription = document.getElementById('filter-subscription');
    const filterStatus = document.getElementById('filter-status');
    
    if (filterSubscription) {
        filterSubscription.addEventListener('change', function() {
            loadUsers(searchInput ? searchInput.value : '');
        });
    }
    
    if (filterStatus) {
        filterStatus.addEventListener('change', function() {
            loadUsers(searchInput ? searchInput.value : '');
        });
    }
}

// Chargement de la liste des utilisateurs
function loadUsers(searchTerm = '') {
    const tableBody = document.getElementById('users-table-body');
    if (!tableBody) return;
    
    // Récupérer les valeurs des filtres
    const subscriptionFilter = document.getElementById('filter-subscription').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    // Simuler le chargement des données (à remplacer par un appel API réel)
    const users = [
        { id: 1, name: 'Jean Dupont', email: 'jean.dupont@example.com', subscription: 'pro', expiration: '31/12/2025', scans: 8, status: 'active' },
        { id: 2, name: 'Marie Martin', email: 'marie.martin@example.com', subscription: 'enterprise', expiration: '15/08/2025', scans: 15, status: 'active' },
        { id: 3, name: 'Pierre Durand', email: 'pierre.durand@example.com', subscription: 'pro', expiration: '10/06/2025', scans: 2, status: 'active' },
        { id: 4, name: 'Sophie Lefebvre', email: 'sophie.lefebvre@example.com', subscription: 'none', expiration: '-', scans: 0, status: 'pending' },
        { id: 5, name: 'Lucas Bernard', email: 'lucas.bernard@example.com', subscription: 'pro', expiration: '05/05/2025', scans: 0, status: 'expired' }
    ];
    
    // Filtrer les utilisateurs
    let filteredUsers = users;
    
    if (searchTerm) {
        filteredUsers = filteredUsers.filter(user => 
            user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
            user.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }
    
    if (subscriptionFilter !== 'all') {
        filteredUsers = filteredUsers.filter(user => user.subscription === subscriptionFilter);
    }
    
    if (statusFilter !== 'all') {
        filteredUsers = filteredUsers.filter(user => user.status === statusFilter);
    }
    
    // Générer le HTML
    let html = '';
    filteredUsers.forEach(user => {
        const statusClass = user.status === 'active' ? 'success' : (user.status === 'expired' ? 'danger' : 'warning');
        const statusText = user.status === 'active' ? 'Actif' : (user.status === 'expired' ? 'Expiré' : 'En attente');
        
        html += `
        <tr>
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.subscription === 'none' ? '-' : (user.subscription === 'pro' ? 'Pro' : 'Entreprise')}</td>
            <td>${user.expiration}</td>
            <td>${user.scans}</td>
            <td><span class="badge bg-${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary edit-user-btn" data-user-id="${user.id}">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Mettre à jour le compteur d'entrées
    document.getElementById('showing-entries').textContent = `Affichage de 1 à ${filteredUsers.length} sur ${filteredUsers.length} entrées`;
    
    // Ajouter les gestionnaires d'événements pour les boutons d'édition
    const editButtons = document.querySelectorAll('.edit-user-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            openUserEditModal(userId);
        });
    });
}

// Ouverture du modal d'édition d'utilisateur
function openUserEditModal(userId = null) {
    // Réinitialiser le formulaire
    document.getElementById('user-edit-form').reset();
    
    if (userId) {
        // Simuler la récupération des données utilisateur (à remplacer par un appel API réel)
        const user = {
            id: userId,
            name: 'Jean Dupont',
            email: 'jean.dupont@example.com',
            subscription: 'pro',
            scans: 8,
            start_date: '2025-01-01',
            end_date: '2025-12-31',
            active: true
        };
        
        // Remplir le formulaire
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-user-name').value = user.name;
        document.getElementById('edit-user-email').value = user.email;
        document.getElementById('edit-subscription-type').value = user.subscription;
        document.getElementById('edit-scans-remaining').value = user.scans;
        document.getElementById('edit-subscription-start').value = user.start_date;
        document.getElementById('edit-subscription-end').value = user.end_date;
        document.getElementById('edit-user-active').checked = user.active;
        
        // Mettre à jour le titre du modal
        document.getElementById('userEditModalLabel').textContent = 'Modifier l\'utilisateur';
    } else {
        // Mettre à jour le titre du modal pour un nouvel utilisateur
        document.getElementById('userEditModalLabel').textContent = 'Ajouter un utilisateur';
    }
    
    // Ouvrir le modal
    const userEditModal = new bootstrap.Modal(document.getElementById('user-edit-modal'));
    userEditModal.show();
}

// Sauvegarde d'un utilisateur
function saveUser() {
    // Récupérer les données du formulaire
    const userId = document.getElementById('edit-user-id').value;
    const userName = document.getElementById('edit-user-name').value;
    const userEmail = document.getElementById('edit-user-email').value;
    const subscriptionType = document.getElementById('edit-subscription-type').value;
    const scansRemaining = document.getElementById('edit-scans-remaining').value;
    const subscriptionStart = document.getElementById('edit-subscription-start').value;
    const subscriptionEnd = document.getElementById('edit-subscription-end').value;
    const userActive = document.getElementById('edit-user-active').checked;
    
    // Validation basique
    if (!userName || !userEmail) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
    }
    
    // Simuler la sauvegarde (à remplacer par un appel API réel)
    console.log('Sauvegarde utilisateur:', {
        id: userId || 'nouveau',
        name: userName,
        email: userEmail,
        subscription: subscriptionType,
        scans: scansRemaining,
        start_date: subscriptionStart,
        end_date: subscriptionEnd,
        active: userActive
    });
    
    // Fermer le modal
    const userEditModal = bootstrap.Modal.getInstance(document.getElementById('user-edit-modal'));
    userEditModal.hide();
    
    // Recharger la liste des utilisateurs
    loadUsers();
    
    // Afficher un message de succès
    alert(userId ? 'Utilisateur modifié avec succès.' : 'Utilisateur ajouté avec succès.');
}

// Suppression d'un utilisateur
function deleteUser() {
    const userId = document.getElementById('edit-user-id').value;
    
    if (!userId) {
        alert('Impossible de supprimer un utilisateur qui n\'a pas encore été créé.');
        return;
    }
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action est irréversible.')) {
        return;
    }
    
    // Simuler la suppression (à remplacer par un appel API réel)
    console.log('Suppression utilisateur:', userId);
    
    // Fermer le modal
    const userEditModal = bootstrap.Modal.getInstance(document.getElementById('user-edit-modal'));
    userEditModal.hide();
    
    // Recharger la liste des utilisateurs
    loadUsers();
    
    // Afficher un message de succès
    alert('Utilisateur supprimé avec succès.');
}

// Initialisation de la page abonnements
function initSubscriptionsPage() {
    // Charger la liste des abonnements
    loadSubscriptions();
    
    // Gestionnaire pour le bouton d'ajout d'abonnement
    const addSubscriptionBtn = document.getElementById('add-subscription-btn');
    if (addSubscriptionBtn) {
        addSubscriptionBtn.addEventListener('click', function() {
            openSubscriptionEditModal();
        });
    }
    
    // Gestionnaire pour le bouton de sauvegarde dans le modal
    const saveSubscriptionBtn = document.getElementById('save-subscription-btn');
    if (saveSubscriptionBtn) {
        saveSubscriptionBtn.addEventListener('click', function() {
            saveSubscription();
        });
    }
    
    // Gestionnaire pour le bouton de suppression dans le modal
    const deleteSubscriptionBtn = document.getElementById('delete-subscription-btn');
    if (deleteSubscriptionBtn) {
        deleteSubscriptionBtn.addEventListener('click', function() {
            deleteSubscription();
        });
    }
    
    // Gestionnaire pour les boutons d'édition de plan
    const editPlanButtons = document.querySelectorAll('.edit-plan-btn');
    editPlanButtons.forEach(button => {
        button.addEventListener('click', function() {
            const planId = this.getAttribute('data-plan-id');
            openPlanEditModal(planId);
        });
    });
    
    // Gestionnaire pour le bouton d'ajout de plan
    const addPlanBtn = document.getElementById('add-plan-btn');
    if (addPlanBtn) {
        addPlanBtn.addEventListener('click', function() {
            openPlanEditModal();
        });
    }
    
    // Gestionnaire pour le bouton de sauvegarde de plan
    const savePlanBtn = document.getElementById('save-plan-btn');
    if (savePlanBtn) {
        savePlanBtn.addEventListener('click', function() {
            savePlan();
        });
    }
}

// Chargement de la liste des abonnements
function loadSubscriptions() {
    const tableBody = document.getElementById('subscriptions-table-body');
    if (!tableBody) return;
    
    // Simuler le chargement des données (à remplacer par un appel API réel)
    const subscriptions = [
        { id: 1, user: 'Jean Dupont', plan: 'pro', start_date: '01/01/2025', end_date: '31/12/2025', scans: 8, status: 'active' },
        { id: 2, user: 'Marie Martin', plan: 'enterprise', start_date: '15/02/2025', end_date: '15/08/2025', scans: 15, status: 'active' },
        { id: 3, user: 'Pierre Durand', plan: 'pro', start_date: '10/03/2025', end_date: '10/06/2025', scans: 2, status: 'active' },
        { id: 4, user: 'Lucas Bernard', plan: 'pro', start_date: '05/02/2025', end_date: '05/05/2025', scans: 0, status: 'expired' }
    ];
    
    // Générer le HTML
    let html = '';
    subscriptions.forEach(sub => {
        const statusClass = sub.status === 'active' ? 'success' : 'danger';
        const statusText = sub.status === 'active' ? 'Actif' : 'Expiré';
        
        html += `
        <tr>
            <td>${sub.id}</td>
            <td>${sub.user}</td>
            <td>${sub.plan === 'pro' ? 'Pro' : 'Entreprise'}</td>
            <td>${sub.start_date}</td>
            <td>${sub.end_date}</td>
            <td>${sub.scans}</td>
            <td><span class="badge bg-${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary edit-subscription-btn" data-subscription-id="${sub.id}">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Mettre à jour le compteur d'entrées
    document.getElementById('showing-subscriptions').textContent = `Affichage de 1 à ${subscriptions.length} sur ${subscriptions.length} entrées`;
    
    // Ajouter les gestionnaires d'événements pour les boutons d'édition
    const editButtons = document.querySelectorAll('.edit-subscription-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const subscriptionId = this.getAttribute('data-subscription-id');
            openSubscriptionEditModal(subscriptionId);
        });
    });
}

// Ouverture du modal d'édition d'abonnement
function openSubscriptionEditModal(subscriptionId = null) {
    // Réinitialiser le formulaire
    document.getElementById('subscription-edit-form').reset();
    
    // Simuler le chargement des utilisateurs pour le select
    const userSelect = document.getElementById('edit-subscription-user');
    userSelect.innerHTML = `
        <option value="1">Jean Dupont</option>
        <option value="2">Marie Martin</option>
        <option value="3">Pierre Durand</option>
        <option value="4">Sophie Lefebvre</option>
        <option value="5">Lucas Bernard</option>
    `;
    
    if (subscriptionId) {
        // Simuler la récupération des données d'abonnement (à remplacer par un appel API réel)
        const subscription = {
            id: subscriptionId,
            user_id: 1,
            plan: 'pro',
            duration: 12,
            scans: 8,
            start_date: '2025-01-01',
            end_date: '2025-12-31',
            active: true
        };
        
        // Remplir le formulaire
        document.getElementById('edit-subscription-id').value = subscription.id;
        document.getElementById('edit-subscription-user').value = subscription.user_id;
        document.getElementById('edit-subscription-plan').value = subscription.plan;
        document.getElementById('edit-subscription-duration').value = subscription.duration;
        document.getElementById('edit-subscription-scans').value = subscription.scans;
        document.getElementById('edit-subscription-start-date').value = subscription.start_date;
        document.getElementById('edit-subscription-end-date').value = subscription.end_date;
        document.getElementById('edit-subscription-active').checked = subscription.active;
        
        // Mettre à jour le titre du modal
        document.getElementById('subscriptionEditModalLabel').textContent = 'Modifier l\'abonnement';
    } else {
        // Mettre à jour le titre du modal pour un nouvel abonnement
        document.getElementById('subscriptionEditModalLabel').textContent = 'Ajouter un abonnement';
    }
    
    // Ouvrir le modal
    const subscriptionEditModal = new bootstrap.Modal(document.getElementById('subscription-edit-modal'));
    subscriptionEditModal.show();
}

// Sauvegarde d'un abonnement
function saveSubscription() {
    // Récupérer les données du formulaire
    const subscriptionId = document.getElementById('edit-subscription-id').value;
    const userId = document.getElementById('edit-subscription-user').value;
    const plan = document.getElementById('edit-subscription-plan').value;
    const duration = document.getElementById('edit-subscription-duration').value;
    const scans = document.getElementById('edit-subscription-scans').value;
    const startDate = document.getElementById('edit-subscription-start-date').value;
    const endDate = document.getElementById('edit-subscription-end-date').value;
    const active = document.getElementById('edit-subscription-active').checked;
    
    // Validation basique
    if (!userId || !plan || !startDate || !endDate) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
    }
    
    // Simuler la sauvegarde (à remplacer par un appel API réel)
    console.log('Sauvegarde abonnement:', {
        id: subscriptionId || 'nouveau',
        user_id: userId,
        plan: plan,
        duration: duration,
        scans: scans,
        start_date: startDate,
        end_date: endDate,
        active: active
    });
    
    // Fermer le modal
    const subscriptionEditModal = bootstrap.Modal.getInstance(document.getElementById('subscription-edit-modal'));
    subscriptionEditModal.hide();
    
    // Recharger la liste des abonnements
    loadSubscriptions();
    
    // Afficher un message de succès
    alert(subscriptionId ? 'Abonnement modifié avec succès.' : 'Abonnement ajouté avec succès.');
}

// Suppression d'un abonnement
function deleteSubscription() {
    const subscriptionId = document.getElementById('edit-subscription-id').value;
    
    if (!subscriptionId) {
        alert('Impossible de supprimer un abonnement qui n\'a pas encore été créé.');
        return;
    }
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet abonnement ? Cette action est irréversible.')) {
        return;
    }
    
    // Simuler la suppression (à remplacer par un appel API réel)
    console.log('Suppression abonnement:', subscriptionId);
    
    // Fermer le modal
    const subscriptionEditModal = bootstrap.Modal.getInstance(document.getElementById('subscription-edit-modal'));
    subscriptionEditModal.hide();
    
    // Recharger la liste des abonnements
    loadSubscriptions();
    
    // Afficher un message de succès
    alert('Abonnement supprimé avec succès.');
}

// Ouverture du modal d'édition de plan
function openPlanEditModal(planId = null) {
    // Réinitialiser le formulaire
    document.getElementById('plan-edit-form').reset();
    
    if (planId) {
        // Simuler la récupération des données du plan (à remplacer par un appel API réel)
        const plan = {
            id: planId,
            name: planId === 'pro' ? 'Pro' : 'Entreprise',
            price_monthly: planId === 'pro' ? 40000 : 100000,
            price_quarterly: planId === 'pro' ? 108000 : 270000,
            price_yearly: planId === 'pro' ? 384000 : 960000,
            max_ips: planId === 'pro' ? 1 : 20,
            features: planId === 'pro' ? 
                "1 adresse IP\nRapport détaillé\nScore de vulnérabilité\nSolutions recommandées" : 
                "20 adresses IP\nRapport détaillé\nScore de vulnérabilité\nSolutions recommandées\nSupport prioritaire"
        };
        
        // Remplir le formulaire
        document.getElementById('edit-plan-id').value = plan.id;
        document.getElementById('edit-plan-name').value = plan.name;
        document.getElementById('edit-plan-price-monthly').value = plan.price_monthly;
        document.getElementById('edit-plan-price-quarterly').value = plan.price_quarterly;
        document.getElementById('edit-plan-price-yearly').value = plan.price_yearly;
        document.getElementById('edit-plan-max-ips').value = plan.max_ips;
        document.getElementById('edit-plan-features').value = plan.features;
        
        // Mettre à jour le titre du modal
        document.getElementById('planEditModalLabel').textContent = 'Modifier le plan';
    } else {
        // Mettre à jour le titre du modal pour un nouveau plan
        document.getElementById('planEditModalLabel').textContent = 'Ajouter un plan';
    }
    
    // Ouvrir le modal
    const planEditModal = new bootstrap.Modal(document.getElementById('plan-edit-modal'));
    planEditModal.show();
}

// Sauvegarde d'un plan
function savePlan() {
    // Récupérer les données du formulaire
    const planId = document.getElementById('edit-plan-id').value;
    const name = document.getElementById('edit-plan-name').value;
    const priceMonthly = document.getElementById('edit-plan-price-monthly').value;
    const priceQuarterly = document.getElementById('edit-plan-price-quarterly').value;
    const priceYearly = document.getElementById('edit-plan-price-yearly').value;
    const maxIps = document.getElementById('edit-plan-max-ips').value;
    const features = document.getElementById('edit-plan-features').value;
    
    // Validation basique
    if (!name || !priceMonthly || !priceQuarterly || !priceYearly || !maxIps || !features) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
    }
    
    // Simuler la sauvegarde (à remplacer par un appel API réel)
    console.log('Sauvegarde plan:', {
        id: planId || 'nouveau',
        name: name,
        price_monthly: priceMonthly,
        price_quarterly: priceQuarterly,
        price_yearly: priceYearly,
        max_ips: maxIps,
        features: features
    });
    
    // Fermer le modal
    const planEditModal = bootstrap.Modal.getInstance(document.getElementById('plan-edit-modal'));
    planEditModal.hide();
    
    // Afficher un message de succès
    alert(planId ? 'Plan modifié avec succès.' : 'Plan ajouté avec succès.');
    
    // Recharger la page pour voir les changements
    // Dans une implémentation réelle, on mettrait à jour le DOM directement
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// Initialisation de la page scans
function initScansPage() {
    // Charger les statistiques des scans
    loadScanStats();
    
    // Charger la liste des scans
    loadScans();
    
    // Gestionnaire pour le bouton d'actualisation
    const refreshScansBtn = document.getElementById('refresh-scans-btn');
    if (refreshScansBtn) {
        refreshScansBtn.addEventListener('click', function() {
            loadScanStats();
            loadScans();
        });
    }
    
    // Gestionnaire pour la recherche
    const searchInput = document.getElementById('search-scans');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            loadScans(this.value);
        });
    }
    
    // Gestionnaires pour les filtres
    const filterType = document.getElementById('filter-scan-type');
    const filterStatus = document.getElementById('filter-scan-status');
    
    if (filterType) {
        filterType.addEventListener('change', function() {
            loadScans(searchInput ? searchInput.value : '');
        });
    }
    
    if (filterStatus) {
        filterStatus.addEventListener('change', function() {
            loadScans(searchInput ? searchInput.value : '');
        });
    }
}

// Chargement des statistiques des scans
function loadScanStats() {
    // Simuler le chargement des données (à remplacer par un appel API réel)
    setTimeout(() => {
        document.getElementById('total-scans-count').textContent = '342';
        document.getElementById('completed-scans').textContent = '315';
        document.getElementById('pending-scans').textContent = '18';
        document.getElementById('failed-scans').textContent = '9';
    }, 500);
}

// Chargement de la liste des scans
function loadScans(searchTerm = '') {
    const tableBody = document.getElementById('scans-table-body');
    if (!tableBody) return;
    
    // Récupérer les valeurs des filtres
    const typeFilter = document.getElementById('filter-scan-type').value;
    const statusFilter = document.getElementById('filter-scan-status').value;
    
    // Simuler le chargement des données (à remplacer par un appel API réel)
    const scans = [
        { id: 1, user: 'Jean Dupont', type: 'pro', ip: '192.168.1.10', start_date: '26/05/2025 10:15', end_date: '26/05/2025 10:45', score: 7.5, status: 'completed' },
        { id: 2, user: 'Marie Martin', type: 'enterprise', ip: '10.0.0.5', start_date: '26/05/2025 11:30', end_date: '26/05/2025 12:15', score: 3.2, status: 'completed' },
        { id: 3, user: 'Pierre Durand', type: 'pro', ip: '172.16.0.1', start_date: '26/05/2025 13:00', end_date: '-', score: '-', status: 'pending' },
        { id: 4, user: 'Sophie Lefebvre', type: 'pro', ip: '192.168.0.5', start_date: '26/05/2025 09:45', end_date: '26/05/2025 10:00', score: '-', status: 'failed' },
        { id: 5, user: 'Lucas Bernard', type: 'enterprise', ip: '10.1.1.1', start_date: '25/05/2025 16:30', end_date: '25/05/2025 17:15', score: 8.9, status: 'completed' }
    ];
    
    // Filtrer les scans
    let filteredScans = scans;
    
    if (searchTerm) {
        filteredScans = filteredScans.filter(scan => 
            scan.user.toLowerCase().includes(searchTerm.toLowerCase()) || 
            scan.ip.includes(searchTerm)
        );
    }
    
    if (typeFilter !== 'all') {
        filteredScans = filteredScans.filter(scan => scan.type === typeFilter);
    }
    
    if (statusFilter !== 'all') {
        filteredScans = filteredScans.filter(scan => scan.status === statusFilter);
    }
    
    // Générer le HTML
    let html = '';
    filteredScans.forEach(scan => {
        let statusClass, statusText;
        
        switch(scan.status) {
            case 'completed':
                statusClass = 'success';
                statusText = 'Terminé';
                break;
            case 'pending':
                statusClass = 'warning';
                statusText = 'En cours';
                break;
            case 'failed':
                statusClass = 'danger';
                statusText = 'Échoué';
                break;
        }
        
        html += `
        <tr>
            <td>${scan.id}</td>
            <td>${scan.user}</td>
            <td>${scan.type === 'pro' ? 'Pro' : 'Entreprise'}</td>
            <td>${scan.ip}</td>
            <td>${scan.start_date}</td>
            <td>${scan.end_date}</td>
            <td>${scan.score !== '-' ? `<span class="badge bg-${getSeverityClass(scan.score)}">${scan.score}</span>` : '-'}</td>
            <td><span class="badge bg-${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary view-scan-btn" data-scan-id="${scan.id}">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Mettre à jour le compteur d'entrées
    document.getElementById('showing-scans').textContent = `Affichage de 1 à ${filteredScans.length} sur ${filteredScans.length} entrées`;
    
    // Ajouter les gestionnaires d'événements pour les boutons de visualisation
    const viewButtons = document.querySelectorAll('.view-scan-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const scanId = this.getAttribute('data-scan-id');
            openScanDetailsModal(scanId);
        });
    });
}

// Déterminer la classe de sévérité en fonction du score
function getSeverityClass(score) {
    score = parseFloat(score);
    if (score >= 9.0) return 'danger';
    if (score >= 7.0) return 'warning';
    if (score >= 4.0) return 'primary';
    return 'success';
}

// Ouverture du modal de détails de scan
function openScanDetailsModal(scanId) {
    // Simuler la récupération des données du scan (à remplacer par un appel API réel)
    const scan = {
        id: scanId,
        user: 'Jean Dupont',
        type: 'pro',
        ip: '192.168.1.10',
        start_date: '26/05/2025 10:15',
        end_date: '26/05/2025 10:45',
        duration: '30 minutes',
        score: 7.5,
        status: 'completed',
        vulnerabilities: {
            critical: 1,
            high: 2,
            medium: 3,
            low: 5
        },
        cve_findings: [
            { cve: 'CVE-2021-44228', description: 'Log4j Remote Code Execution', cvss: 10.0, severity: 'Critical', solution: 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228' },
            { cve: 'CVE-2020-1472', description: 'Netlogon Elevation of Privilege', cvss: 8.1, severity: 'High', solution: 'https://nvd.nist.gov/vuln/detail/CVE-2020-1472' },
            { cve: 'CVE-2019-0708', description: 'RDP Remote Code Execution', cvss: 9.8, severity: 'Critical', solution: 'https://nvd.nist.gov/vuln/detail/CVE-2019-0708' }
        ],
        ports: [
            { port: 22, protocol: 'tcp', service: 'SSH', version: 'OpenSSH 8.2p1', state: 'open' },
            { port: 80, protocol: 'tcp', service: 'HTTP', version: 'Apache 2.4.41', state: 'open' },
            { port: 443, protocol: 'tcp', service: 'HTTPS', version: 'Apache 2.4.41', state: 'open' },
            { port: 3306, protocol: 'tcp', service: 'MySQL', version: '8.0.27', state: 'open' }
        ],
        raw_report: JSON.stringify({
            scan_id: scanId,
            target: '192.168.1.10',
            timestamp: '2025-05-26T10:15:00Z',
            tools: ['nmap', 'nikto', 'gobuster'],
            findings: {
                vulnerabilities: [
                    { cve: 'CVE-2021-44228', description: 'Log4j Remote Code Execution', cvss: 10.0 },
                    { cve: 'CVE-2020-1472', description: 'Netlogon Elevation of Privilege', cvss: 8.1 },
                    { cve: 'CVE-2019-0708', description: 'RDP Remote Code Execution', cvss: 9.8 }
                ],
                ports: [
                    { port: 22, protocol: 'tcp', service: 'SSH', version: 'OpenSSH 8.2p1', state: 'open' },
                    { port: 80, protocol: 'tcp', service: 'HTTP', version: 'Apache 2.4.41', state: 'open' },
                    { port: 443, protocol: 'tcp', service: 'HTTPS', version: 'Apache 2.4.41', state: 'open' },
                    { port: 3306, protocol: 'tcp', service: 'MySQL', version: '8.0.27', state: 'open' }
                ]
            }
        }, null, 2)
    };
    
    // Remplir les informations générales
    document.getElementById('scan-detail-id').textContent = scan.id;
    document.getElementById('scan-detail-user').textContent = scan.user;
    document.getElementById('scan-detail-type').textContent = scan.type === 'pro' ? 'Pro' : 'Entreprise';
    document.getElementById('scan-detail-ip').textContent = scan.ip;
    document.getElementById('scan-detail-start').textContent = scan.start_date;
    document.getElementById('scan-detail-end').textContent = scan.end_date;
    document.getElementById('scan-detail-duration').textContent = scan.duration;
    document.getElementById('scan-detail-status').innerHTML = `<span class="badge bg-success">Terminé</span>`;
    
    // Remplir les résultats
    document.getElementById('scan-detail-score').textContent = scan.score;
    document.getElementById('scan-detail-critical').textContent = scan.vulnerabilities.critical;
    document.getElementById('scan-detail-high').textContent = scan.vulnerabilities.high;
    document.getElementById('scan-detail-medium').textContent = scan.vulnerabilities.medium;
    document.getElementById('scan-detail-low').textContent = scan.vulnerabilities.low;
    
    // Remplir le tableau des vulnérabilités
    let vulnHtml = '';
    scan.cve_findings.forEach(vuln => {
        const severityClass = vuln.severity === 'Critical' ? 'danger' : 
                             (vuln.severity === 'High' ? 'warning' : 
                             (vuln.severity === 'Medium' ? 'primary' : 'success'));
        
        vulnHtml += `
        <tr>
            <td><a href="https://nvd.nist.gov/vuln/detail/${vuln.cve}" target="_blank">${vuln.cve}</a></td>
            <td>${vuln.description}</td>
            <td><span class="badge bg-${severityClass}">${vuln.cvss}</span></td>
            <td>${vuln.severity}</td>
            <td><a href="${vuln.solution}" target="_blank" class="btn btn-sm btn-outline-primary">Voir solution</a></td>
        </tr>
        `;
    });
    document.getElementById('vulnerabilities-table').innerHTML = vulnHtml;
    
    // Remplir le tableau des ports
    let portsHtml = '';
    scan.ports.forEach(port => {
        portsHtml += `
        <tr>
            <td>${port.port}</td>
            <td>${port.protocol}</td>
            <td>${port.service}</td>
            <td>${port.version}</td>
            <td><span class="badge bg-success">${port.state}</span></td>
        </tr>
        `;
    });
    document.getElementById('ports-table').innerHTML = portsHtml;
    
    // Remplir le rapport brut
    document.getElementById('raw-report').textContent = scan.raw_report;
    
    // Initialiser le graphique de score
    initScoreChart(scan.score);
    
    // Gestionnaire pour le bouton de téléchargement
    const downloadBtn = document.getElementById('download-report-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            // Simuler le téléchargement
            alert('Téléchargement du rapport en cours...');
        });
    }
    
    // Ouvrir le modal
    const scanDetailsModal = new bootstrap.Modal(document.getElementById('scan-details-modal'));
    scanDetailsModal.show();
}

// Initialisation du graphique de score
function initScoreChart(score) {
    const chartCanvas = document.getElementById('scan-score-chart');
    if (!chartCanvas || typeof Chart === 'undefined') return;
    
    // Déterminer la couleur en fonction du score
    let color;
    if (score >= 9.0) color = '#e74c3c'; // danger
    else if (score >= 7.0) color = '#f39c12'; // warning
    else if (score >= 4.0) color = '#3498db'; // primary
    else color = '#2ecc71'; // success
    
    // Détruire le graphique existant s'il y en a un
    if (window.scoreChart) {
        window.scoreChart.destroy();
    }
    
    const ctx = chartCanvas.getContext('2d');
    window.scoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 10 - score],
                backgroundColor: [color, '#ecf0f1'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
}

// Initialisation de la page paramètres
function initSettingsPage() {
    // Gestionnaires pour les formulaires
    const forms = [
        'general-settings-form',
        'security-settings-form',
        'scan-settings-form',
        'alerts-settings-form'
    ];
    
    forms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                saveSettings(formId);
            });
        }
    });
    
    // Gestionnaire pour le bouton de configuration Grafana
    const setupGrafanaBtn = document.getElementById('setup-grafana-btn');
    if (setupGrafanaBtn) {
        setupGrafanaBtn.addEventListener('click', function() {
            setupGrafana();
        });
    }
    
    // Gestionnaire pour le bouton de redémarrage Prometheus
    const restartPrometheusBtn = document.getElementById('restart-prometheus-btn');
    if (restartPrometheusBtn) {
        restartPrometheusBtn.addEventListener('click', function() {
            restartPrometheus();
        });
    }
    
    // Gestionnaire pour le bouton d'ajout d'admin
    const addAdminBtn = document.getElementById('add-admin-btn');
    if (addAdminBtn) {
        addAdminBtn.addEventListener('click', function() {
            openAdminEditModal();
        });
    }
    
    // Gestionnaire pour les boutons d'édition d'admin
    const editAdminButtons = document.querySelectorAll('.edit-admin-btn');
    editAdminButtons.forEach(button => {
        button.addEventListener('click', function() {
            const adminId = this.getAttribute('data-admin-id');
            openAdminEditModal(adminId);
        });
    });
    
    // Gestionnaire pour le bouton de sauvegarde d'admin
    const saveAdminBtn = document.getElementById('save-admin-btn');
    if (saveAdminBtn) {
        saveAdminBtn.addEventListener('click', function() {
            saveAdmin();
        });
    }
    
    // Gestionnaire pour le bouton de suppression d'admin
    const deleteAdminBtn = document.getElementById('delete-admin-btn');
    if (deleteAdminBtn) {
        deleteAdminBtn.addEventListener('click', function() {
            deleteAdmin();
        });
    }
    
    // Gestionnaire pour le bouton de génération de clé API
    const generateApiKeyBtn = document.getElementById('generate-api-key');
    if (generateApiKeyBtn) {
        generateApiKeyBtn.addEventListener('click', function() {
            generateApiKey();
        });
    }
    
    // Gestionnaire pour le bouton d'affichage de clé API
    const showApiKeyBtn = document.getElementById('show-api-key');
    if (showApiKeyBtn) {
        showApiKeyBtn.addEventListener('click', function() {
            toggleApiKeyVisibility();
        });
    }
}

// Sauvegarde des paramètres
function saveSettings(formId) {
    // Simuler la sauvegarde (à remplacer par un appel API réel)
    console.log(`Sauvegarde des paramètres du formulaire ${formId}`);
    
    // Récupérer tous les champs du formulaire
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    // Ajouter les valeurs des checkboxes (qui ne sont pas incluses dans formData si non cochées)
    form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        data[checkbox.id] = checkbox.checked;
    });
    
    console.log('Données à sauvegarder:', data);
    
    // Afficher un message de succès
    alert('Paramètres enregistrés avec succès.');
}

// Configuration de Grafana
function setupGrafana() {
    // Simuler la configuration (à remplacer par un appel API réel)
    alert('Configuration de Grafana en cours...');
    
    // Dans une implémentation réelle, on lancerait un processus de configuration
    // puis on mettrait à jour l'interface une fois terminé
    setTimeout(() => {
        alert('Grafana a été configuré avec succès. Veuillez actualiser la page pour voir les changements.');
    }, 2000);
}

// Redémarrage de Prometheus
function restartPrometheus() {
    // Simuler le redémarrage (à remplacer par un appel API réel)
    alert('Redémarrage de Prometheus en cours...');
    
    // Dans une implémentation réelle, on lancerait un processus de redémarrage
    // puis on mettrait à jour l'interface une fois terminé
    setTimeout(() => {
        alert('Prometheus a été redémarré avec succès.');
    }, 2000);
}

// Ouverture du modal d'édition d'admin
function openAdminEditModal(adminId = null) {
    // Réinitialiser le formulaire
    document.getElementById('admin-edit-form').reset();
    
    if (adminId) {
        // Simuler la récupération des données admin (à remplacer par un appel API réel)
        const admin = {
            id: adminId,
            name: 'Admin Principal',
            email: 'admin@cybershield-algeria.com',
            role: 'super-admin',
            active: true
        };
        
        // Remplir le formulaire
        document.getElementById('edit-admin-id').value = admin.id;
        document.getElementById('edit-admin-name').value = admin.name;
        document.getElementById('edit-admin-email').value = admin.email;
        document.getElementById('edit-admin-role').value = admin.role;
        document.getElementById('edit-admin-active').checked = admin.active;
        
        // Mettre à jour le titre du modal
        document.getElementById('adminEditModalLabel').textContent = 'Modifier l\'administrateur';
    } else {
        // Mettre à jour le titre du modal pour un nouvel admin
        document.getElementById('adminEditModalLabel').textContent = 'Ajouter un administrateur';
    }
    
    // Ouvrir le modal
    const adminEditModal = new bootstrap.Modal(document.getElementById('admin-edit-modal'));
    adminEditModal.show();
}

// Sauvegarde d'un admin
function saveAdmin() {
    // Récupérer les données du formulaire
    const adminId = document.getElementById('edit-admin-id').value;
    const name = document.getElementById('edit-admin-name').value;
    const email = document.getElementById('edit-admin-email').value;
    const role = document.getElementById('edit-admin-role').value;
    const password = document.getElementById('edit-admin-password').value;
    const active = document.getElementById('edit-admin-active').checked;
    
    // Validation basique
    if (!name || !email) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
    }
    
    // Simuler la sauvegarde (à remplacer par un appel API réel)
    console.log('Sauvegarde admin:', {
        id: adminId || 'nouveau',
        name: name,
        email: email,
        role: role,
        password: password ? '(modifié)' : '(inchangé)',
        active: active
    });
    
    // Fermer le modal
    const adminEditModal = bootstrap.Modal.getInstance(document.getElementById('admin-edit-modal'));
    adminEditModal.hide();
    
    // Afficher un message de succès
    alert(adminId ? 'Administrateur modifié avec succès.' : 'Administrateur ajouté avec succès.');
    
    // Recharger la page pour voir les changements
    // Dans une implémentation réelle, on mettrait à jour le DOM directement
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// Suppression d'un admin
function deleteAdmin() {
    const adminId = document.getElementById('edit-admin-id').value;
    
    if (!adminId) {
        alert('Impossible de supprimer un administrateur qui n\'a pas encore été créé.');
        return;
    }
    
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet administrateur ? Cette action est irréversible.')) {
        return;
    }
    
    // Simuler la suppression (à remplacer par un appel API réel)
    console.log('Suppression admin:', adminId);
    
    // Fermer le modal
    const adminEditModal = bootstrap.Modal.getInstance(document.getElementById('admin-edit-modal'));
    adminEditModal.hide();
    
    // Afficher un message de succès
    alert('Administrateur supprimé avec succès.');
    
    // Recharger la page pour voir les changements
    // Dans une implémentation réelle, on mettrait à jour le DOM directement
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// Génération d'une nouvelle clé API
function generateApiKey() {
    // Simuler la génération (à remplacer par un appel API réel)
    const newKey = Array(32).fill(0).map(() => Math.random().toString(36).charAt(2)).join('');
    
    // Afficher la nouvelle clé
    const apiKeyInput = document.getElementById('admin-api-key');
    apiKeyInput.value = newKey;
    apiKeyInput.type = 'text';
    
    // Changer l'icône du bouton d'affichage
    const showApiKeyBtn = document.getElementById('show-api-key');
    showApiKeyBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    
    // Afficher un message de succès
    alert('Nouvelle clé API générée avec succès.');
}

// Basculer la visibilité de la clé API
function toggleApiKeyVisibility() {
    const apiKeyInput = document.getElementById('admin-api-key');
    const showApiKeyBtn = document.getElementById('show-api-key');
    
    if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        showApiKeyBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        apiKeyInput.type = 'password';
        showApiKeyBtn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Déconnexion
function logout() {
    // Supprimer les données d'authentification
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminName');
    
    // Rediriger vers la page de login
    window.location.href = 'login.html';
}
