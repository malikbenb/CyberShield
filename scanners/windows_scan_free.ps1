<#
.SYNOPSIS
    Windows Security Scanner - Diagnostic Tool
.DESCRIPTION
    Cet outil effectue une analyse de sécurité du système Windows et génère un rapport.
    Il ne modifie aucun paramètre système et fonctionne en lecture seule.
.NOTES
    Version: 2.4
    Auteur: CyberShield Algeria
#>

# Chargement des assemblies pour l'interface graphique
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 1. Configuration sécurisée
$ReportFolder = [Environment]::GetFolderPath("MyDocuments")
$ScanDate = Get-Date -Format "yyyyMMdd_HHmmss"
$HTMLReportPath = "$ReportFolder\SecurityScan_$ScanDate.html"

# 2. Interface graphique avec progression
$progressForm = New-Object System.Windows.Forms.Form
$progressForm.Text = "CyberShield Algeria - Analyse de Sécurité"
$progressForm.Width = 600
$progressForm.Height = 200
$progressForm.StartPosition = "CenterScreen"
$progressForm.FormBorderStyle = "FixedDialog"
$progressForm.MaximizeBox = $false
$progressForm.MinimizeBox = $false

$progressLabel = New-Object System.Windows.Forms.Label
$progressLabel.Location = New-Object System.Drawing.Point(20, 20)
$progressLabel.Width = 550
$progressLabel.Text = "Préparation de l'analyse..."
$progressForm.Controls.Add($progressLabel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20, 50)
$progressBar.Width = 550
$progressBar.Style = "Continuous"
$progressForm.Controls.Add($progressBar)

$detailsBox = New-Object System.Windows.Forms.RichTextBox
$detailsBox.Location = New-Object System.Drawing.Point(20, 80)
$detailsBox.Width = 550
$detailsBox.Height = 80
$detailsBox.ReadOnly = $true
$detailsBox.BackColor = [System.Drawing.Color]::White
$progressForm.Controls.Add($detailsBox)

$progressForm.Show() | Out-Null
$progressForm.Refresh()

function Update-Progress {
    param([int]$Percent, [string]$Message, [string]$Detail)
    $progressBar.Value = $Percent
    $progressLabel.Text = $Message
    $detailsBox.AppendText("$([DateTime]::Now.ToString('HH:mm:ss')) - $Detail`r`n")
    $detailsBox.ScrollToCaret()
    $progressForm.Refresh()
    Write-Host "$Message - $Detail"
}

# 3. Fonctions de scan améliorées
function Get-SystemHealth {
    Update-Progress -Percent 10 -Message "Vérification du système" -Detail "Collecte des informations système de base..."
    try {
        $OS = Get-CimInstance -ClassName Win32_OperatingSystem
        $CPU = Get-CimInstance -ClassName Win32_Processor
        $Firewall = Get-NetFirewallProfile | Where-Object { $_.Enabled }
        $Uptime = (Get-Date) - $OS.LastBootUpTime
        
        # Récupération des règles de pare-feu triées par date de modification
        $FirewallRules = Get-NetFirewallRule | 
                        ForEach-Object {
                            $rule = $_
                            $config = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule | Select-Object Protocol, LocalPort
                            [PSCustomObject]@{
                                DisplayName = $rule.DisplayName
                                Enabled = $rule.Enabled
                                Direction = $rule.Direction
                                Action = $rule.Action
                                Profile = $rule.Profile
                                Protocol = $config.Protocol
                                LocalPort = $config.LocalPort
                                CreationTime = $rule.CreationTime
                            }
                        } |
                        Sort-Object CreationTime -Descending

        $SystemInfo = [PSCustomObject]@{
            ComputerName = $env:COMPUTERNAME
            OSVersion = $OS.Caption
            Build = $OS.BuildNumber
            Architecture = $CPU.AddressWidth
            FirewallStatus = if ($Firewall) { "Actif" } else { "Inactif" }
            FirewallRules = $FirewallRules
            UptimeDays = $Uptime.Days
            IsEOL = $OS.Version -lt "10.0.18362"  # Windows 10 1903+
        }

        Update-Progress -Percent 15 -Message "Vérification du système" -Detail "Informations système collectées avec succès"
        return $SystemInfo
    } catch {
        Update-Progress -Percent 15 -Message "Vérification du système" -Detail "Erreur de lecture des informations système"
        Write-Warning "Erreur de lecture des informations système"
        return $null
    }
}

function Get-NetworkDetails {
    Update-Progress -Percent 20 -Message "Analyse réseau" -Detail "Collecte des informations réseau locales..."
    try {
        # Obtenir spécifiquement l'interface Wi-Fi
        $WiFiInterface = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Wi-Fi*" -and $_.Status -eq "Up" }
        
        if ($WiFiInterface) {
            $WiFiConfig = Get-NetIPConfiguration -InterfaceAlias $WiFiInterface.Name
            $WiFiDNS = Get-DnsClientServerAddress -InterfaceAlias $WiFiInterface.Name -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses
            $IPv6Address = (Get-NetIPAddress -InterfaceAlias $WiFiInterface.Name -AddressFamily IPv6 | 
                          Where-Object { $_.PrefixOrigin -ne 'WellKnown' }).IPAddress
        }

        Update-Progress -Percent 25 -Message "Analyse réseau" -Detail "Obtention de l'adresse IP publique..."
        $PublicIP = try {
            (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 5)
        } catch {
            "N/A"
        }

        $NetworkInfo = [PSCustomObject]@{
            WiFiInterface = if ($WiFiInterface) {
                [PSCustomObject]@{
                    Name = $WiFiInterface.Name
                    Description = $WiFiInterface.InterfaceDescription
                    LocalIP = $WiFiConfig.IPv4Address.IPAddress
                    IPv6Address = $IPv6Address
                    Gateway = $WiFiConfig.IPv4DefaultGateway.NextHop
                    MAC = $WiFiInterface.MacAddress
                    DNSServers = $WiFiDNS -join ', '
                }
            } else {
                $null
            }
            PublicIP = $PublicIP
        }

        Update-Progress -Percent 30 -Message "Analyse réseau" -Detail "Informations réseau collectées avec succès"
        return $NetworkInfo
    } catch {
        Update-Progress -Percent 30 -Message "Analyse réseau" -Detail "Erreur de lecture de la configuration réseau"
        Write-Warning "Erreur de lecture de la configuration réseau"
        return $null
    }
}

function Test-EssentialPorts {
    Update-Progress -Percent 40 -Message "Test des ports" -Detail "Début du scan des ports critiques..."
    $PortsToCheck = @(
        [PSCustomObject]@{Port=21; Protocol="FTP"; Service="FTP Server"},
        [PSCustomObject]@{Port=22; Protocol="SSH"; Service="OpenSSH"},
        [PSCustomObject]@{Port=23; Protocol="Telnet"; Service="Telnet Server"},
        [PSCustomObject]@{Port=80; Protocol="HTTP"; Service="IIS/APACHE"},
        [PSCustomObject]@{Port=443; Protocol="HTTPS"; Service="IIS/APACHE"},
        [PSCustomObject]@{Port=3389; Protocol="RDP"; Service="Remote Desktop"},
        [PSCustomObject]@{Port=445; Protocol="SMB"; Service="File Sharing"}
    )
    
    $Results = @()
    $totalPorts = $PortsToCheck.Count
    $currentPort = 0

    foreach ($Port in $PortsToCheck) {
        $currentPort++
        $percentComplete = 40 + ($currentPort / $totalPorts * 50)
        
        Update-Progress -Percent $percentComplete -Message "Test des ports" -Detail "Test du port $($Port.Port) ($($Port.Protocol))..."
        
        try {
            $Test = Test-NetConnection -ComputerName localhost -Port $Port.Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
            $Results += [PSCustomObject]@{
                Port = $Port.Port
                Protocol = $Port.Protocol
                Service = $Port.Service
                Status = if ($Test.TcpTestSucceeded) { "Ouvert" } else { "Fermé" }
            }
        } catch {
            $Results += [PSCustomObject]@{
                Port = $Port.Port
                Protocol = $Port.Protocol
                Service = $Port.Service
                Status = "Erreur"
            }
        }
    }

    Update-Progress -Percent 90 -Message "Test des ports" -Detail "Scan des ports terminé"
    return $Results
}

# 4. Génération du rapport HTML amélioré
function New-SecurityReport {
    param($SystemInfo, $NetworkInfo, $PortResults)

    # Déterminer les recommandations
    $Recommendations = @()
    
    # Recommandations pour les ports ouverts
    foreach ($Port in ($PortResults | Where-Object { $_.Status -eq "Ouvert" })) {
        $Recommendation = switch ($Port.Port) {
            21 { "Désactiver FTP ou implémenter FTPS (FTP over SSL). FTP est non sécurisé et transmet les données en clair." }
            22 { "Restreindre l'accès SSH aux adresses IP autorisées. Implémenter l'authentification par clé plutôt que par mot de passe." }
            23 { "Désactiver Telnet immédiatement. Telnet est complètement non sécurisé. Utiliser SSH à la place." }
            80 { "Rediriger le trafic HTTP vers HTTPS. Configurer HSTS (HTTP Strict Transport Security)." }
            443 { "Vérifier que le certificat SSL est valide et à jour. Configurer une politique SSL/TLS stricte." }
            3389 { "Ne pas exposer RDP directement sur Internet. Utiliser un VPN ou RDP GateWay. Changer le port par défaut." }
            445 { "Restreindre l'accès SMB. Désactiver SMBv1 si activé. Mettre à jour pour corriger les vulnérabilités comme EternalBlue." }
            default { "Port $($Port.Port) ouvert - Évaluer si ce port est nécessaire et restreindre l'accès si possible." }
        }
        $Recommendations += "<li><strong>Port $($Port.Port) ($($Port.Protocol)):</strong> $Recommendation</li>"
    }

    # Recommandations pour le système
    if ($SystemInfo.IsEOL) {
        $Recommendations += "<li><strong>Système d'exploitation:</strong> Votre version Windows ($($SystemInfo.OSVersion)) n'est plus supportée. Mettez à jour vers une version supportée. Si impossible, isolez le système du réseau et considérez les Extended Security Updates (ESU).</li>"
    }
    if ($SystemInfo.FirewallStatus -eq "Inactif") {
        $Recommendations += "<li><strong>Pare-feu:</strong> Activer le pare-feu Windows et configurer des règles appropriées.</li>"
    }
    if ($SystemInfo.UptimeDays -gt 30) {
        $Recommendations += "<li><strong>Mises à jour:</strong> Le système n'a pas redémarré depuis $($SystemInfo.UptimeDays) jours. Assurez-vous que les mises à jour de sécurité sont installées.</li>"
    }

    if ($Recommendations.Count -eq 0) {
        $Recommendations += "<li>Aucune vulnérabilité critique détectée. Maintenez de bonnes pratiques de sécurité.</li>"
    }

    # Générer la liste des règles de pare-feu
    $FirewallRulesHTML = ""
    if ($SystemInfo.FirewallRules) {
        $FirewallRulesHTML = "<table><tr><th>Règle</th><th>Statut</th><th>Direction</th><th>Action</th><th>Protocole</th><th>Port</th></tr>"
        foreach ($rule in $SystemInfo.FirewallRules) {
            $status = if ($rule.Enabled) { "Activé" } else { "Désactivé" }
            $FirewallRulesHTML += "<tr><td>$($rule.DisplayName)</td><td>$status</td><td>$($rule.Direction)</td><td>$($rule.Action)</td><td>$($rule.Protocol)</td><td>$($rule.LocalPort)</td></tr>"
        }
        $FirewallRulesHTML += "</table>"
    }

    $HTML = @"
<!DOCTYPE html>
<html>
<head>
    <title>Rapport de Sécurité - $ScanDate</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #0066cc; text-align: center; }
        h2 { color: #004080; border-bottom: 1px solid #004080; padding-bottom: 5px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #0066cc; color: white; }
        .high { background-color: #ffcccc; }
        .medium { background-color: #fff3cd; }
        .low { background-color: #d4edda; }
        .solution { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0; }
        .footer { margin-top: 30px; font-size: 0.8em; text-align: center; color: #666; }
    </style>
</head>
<body>
    <h1>CyberShield Algeria</h1>
    <h1 style="font-size: 1.5em;">Rapport de Sécurité Windows</h1>
    <p style="text-align: center;">Généré le: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>
    
    <h2>Informations Système</h2>
    <table>
        <tr><th>Nom de l'hôte</th><td>$($SystemInfo.ComputerName)</td></tr>
        <tr><th>OS</th><td>$($SystemInfo.OSVersion)</td></tr>
        <tr><th>Build</th><td>$($SystemInfo.Build)</td></tr>
        <tr><th>Architecture</th><td>$($SystemInfo.Architecture)-bit</td></tr>
        <tr><th>Pare-feu</th><td>$($SystemInfo.FirewallStatus)</td></tr>
        <tr><th>Uptime</th><td>$($SystemInfo.UptimeDays) jours</td></tr>
    </table>
    
    <h3>Règles de Pare-feu</h3>
    $FirewallRulesHTML
    
    <h2>Configuration Réseau</h2>
    <table>
        <tr><th>Interface</th><td>$($NetworkInfo.WiFiInterface.Name)</td></tr>
        <tr><th>Description</th><td>$($NetworkInfo.WiFiInterface.Description)</td></tr>
        <tr><th>IP Locale (IPv4)</th><td>$($NetworkInfo.WiFiInterface.LocalIP)</td></tr>
        <tr><th>IP Locale (IPv6)</th><td>$($NetworkInfo.WiFiInterface.IPv6Address)</td></tr>
        <tr><th>Passerelle</th><td>$($NetworkInfo.WiFiInterface.Gateway)</td></tr>
        <tr><th>Adresse MAC</th><td>$($NetworkInfo.WiFiInterface.MAC)</td></tr>
        <tr><th>Serveurs DNS</th><td>$($NetworkInfo.WiFiInterface.DNSServers)</td></tr>
        <tr><th>IP Publique</th><td>$($NetworkInfo.PublicIP)</td></tr>
    </table>
    
    <h2>État des Ports</h2>
    <table>
        <tr>
            <th>Port</th>
            <th>Protocol</th>
            <th>Service/Version</th>
            <th>État</th>
            <th>Sévérité</th>
        </tr>
"@

    foreach ($Port in $PortResults) {
        $severity = switch ($Port.Status) {
            "Ouvert" { "Élevé"; $class = "high" }
            "Filtré" { "Moyenne"; $class = "medium" }
            default { "Faible"; $class = "low" }
        }
        
        $HTML += "<tr class='$class'><td>$($Port.Port)</td><td>$($Port.Protocol)</td><td>$($Port.Service)</td><td>$($Port.Status)</td><td>$severity</td></tr>"
    }

    $HTML += @"
    </table>
    
    <h2>Recommandations de Sécurité</h2>
    <div class="solution">
        <ul>
            $($Recommendations -join "`n")
        </ul>
    </div>
    
    <div class="footer">
        Rapport généré par CyberShield Algeria - Windows Security Scanner<br>
        Outil de diagnostic - Ne modifie aucun paramètre système
    </div>
</body>
</html>
"@

    $HTML | Out-File -FilePath $HTMLReportPath -Encoding UTF8
    return $HTMLReportPath
}

# 5. Exécution principale
try {
    # Effectuer les scans
    $SystemInfo = Get-SystemHealth
    $NetworkInfo = Get-NetworkDetails
    $PortResults = Test-EssentialPorts

    # Générer le rapport
    Update-Progress -Percent 95 -Message "Génération du rapport" -Detail "Création du rapport HTML..."
    $ReportPath = New-SecurityReport -SystemInfo $SystemInfo -NetworkInfo $NetworkInfo -PortResults $PortResults

    # Afficher les résultats
    Update-Progress -Percent 100 -Message "Analyse terminée" -Detail "Rapport généré avec succès"
    Start-Sleep -Seconds 2

    # Fermer la fenêtre de progression
    $progressForm.Close()

    # Ouvrir le rapport dans le navigateur par défaut
    Start-Process $ReportPath

} catch {
    Update-Progress -Percent 100 -Message "Erreur" -Detail "Erreur lors de l'analyse: $_"
    Write-Warning "Erreur lors de l'analyse: $_"
    $progressForm.Close()
}