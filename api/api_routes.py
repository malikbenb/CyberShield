#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Routes API pour le téléchargement des scanners Pro
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

# Définir les chemins vers les scanners Pro
SCANNERS_DIR = Path("./client/scanners")

# Vérifier que les dossiers existent
SCANNERS_DIR.mkdir(exist_ok=True)
(SCANNERS_DIR / "windows").mkdir(exist_ok=True)
(SCANNERS_DIR / "linux").mkdir(exist_ok=True)
(SCANNERS_DIR / "macos").mkdir(exist_ok=True)

# Chemins des scanners Pro
PRO_SCANNERS = {
    "windows": SCANNERS_DIR / "windows" / "WindowsProScan.exe",
    "linux": SCANNERS_DIR / "linux" / "linux_scan_pro.sh",
    "macos": SCANNERS_DIR / "macos" / "macos_scan_pro.sh"
}

# Créer des fichiers de placeholder si les scanners n'existent pas
for os_type, scanner_path in PRO_SCANNERS.items():
    if not scanner_path.exists():
        with open(scanner_path, "w") as f:
            f.write(f"# Scanner Pro pour {os_type}\n")
            f.write("# Ce fichier est un placeholder pour le scanner Pro\n")
            f.write("echo 'Scanner Pro pour CyberShield Algeria'\n")
            f.write("echo 'Connexion au serveur Docker...'\n")
            f.write("echo 'Scan en cours...'\n")
            f.write("echo 'Scan terminé.'\n")
        
        # Rendre les scripts exécutables
        if os_type in ["linux", "macos"]:
            os.chmod(scanner_path, 0o755)

@router.get("/download/pro/{os_type}")
async def download_pro_scanner(os_type: str):
    """
    Télécharge le scanner Pro pour le système d'exploitation spécifié.
    """
    if os_type not in PRO_SCANNERS:
        raise HTTPException(status_code=404, detail=f"Scanner Pro pour {os_type} non disponible")
    
    scanner_path = PRO_SCANNERS[os_type]
    
    if not scanner_path.exists():
        raise HTTPException(status_code=404, detail=f"Scanner Pro pour {os_type} non trouvé")
    
    filename = scanner_path.name
    
    return FileResponse(
        path=scanner_path,
        filename=filename,
        media_type="application/octet-stream"
    )
