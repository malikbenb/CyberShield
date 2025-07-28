<#
.SYNOPSIS
    Compile le script en exécutable
#>

param(
    [string]$inputFile = "windows_scan_free.ps1",
    [string]$outputFile = "WindowsFreeScan.exe"
)

# Vérifier PS2EXE
if (-not (Get-Module ps2exe -ListAvailable)) {
    try {
        Install-Module ps2exe -Force -Scope CurrentUser
    } catch {
        Write-Host "Erreur: Impossible d'installer PS2EXE" -ForegroundColor Red
        exit 1
    }
}

# Paramètres de compilation
$params = @{
    inputFile = $inputFile
    outputFile = $outputFile
    title = "CyberShield Algeria Scanner"
    description = "Outil de scan de sécurité"
    iconFile = "Logo.ico"  # Optionnel
    noConsole = $true
    requireAdmin = $true
}

try {
    Invoke-PS2EXE @params
    Write-Host "Compilation réussie: $outputFile" -ForegroundColor Green
} catch {
    Write-Host "Erreur de compilation: $_" -ForegroundColor Red
    exit 1
}