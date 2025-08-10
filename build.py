#!/usr/bin/env python3
"""
Script de build et de packaging pour Tych utilisant uv
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n🔧 {description}")
    print(f"Commande: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Succès")
        if result.stdout.strip():
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Erreur")
        if e.stderr.strip():
            print(f"Erreur: {e.stderr}")
        if e.stdout.strip():
            print(f"Sortie: {e.stdout}")
        return False
    except FileNotFoundError:
        print("❌ Commande non trouvée")
        return False

def get_uv_executable():
    """Trouve l'exécutable uv."""
    # Cherche d'abord dans l'environnement virtuel local
    possible_paths = [
        Path(".venv/Scripts/uv.exe"),         # Chemin relatif Windows
        Path(".venv/bin/uv"),                 # Chemin relatif Unix
        Path("../Scripts/uv.exe"),            # Chemin parent Windows
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path.absolute())
    
    # Cherche dans le PATH
    try:
        # Windows
        result = subprocess.run(["where", "uv"], capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')[0]
    except subprocess.CalledProcessError:
        try:
            # Unix
            result = subprocess.run(["which", "uv"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
    
    return None

def main():
    """Fonction principale de build."""
    print("🚀 Build et packaging de Tych avec uv")
    print("=" * 50)
    
    # Vérification de l'environnement
    print(f"📁 Répertoire: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Recherche d'uv
    uv_path = get_uv_executable()
    if not uv_path:
        print("❌ uv non trouvé. Installez-le avec: pip install uv")
        return False
    
    print(f"🔧 uv trouvé: {uv_path}")
    
    # Nettoyage des builds précédents
    if Path("dist").exists():
        print("\n🧹 Nettoyage des builds précédents...")
        try:
            import shutil
            shutil.rmtree("dist")
            print("✅ Dossier dist supprimé")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # Synchronisation des dépendances
    success = run_command([uv_path, "sync"], "Synchronisation des dépendances")
    if not success:
        return False
    
    # Build du package
    success = run_command([uv_path, "build"], "Construction du package")
    if not success:
        return False
    
    # Vérification des fichiers créés
    dist_path = Path("dist")
    if dist_path.exists():
        files = list(dist_path.glob("*"))
        print(f"\n📦 Fichiers créés dans dist/:")
        for file in files:
            if file.name != ".gitignore":
                size = file.stat().st_size
                print(f"  - {file.name} ({size:,} bytes)")
    
    # Installation en mode développement
    success = run_command([uv_path, "pip", "install", "-e", "."], 
                         "Installation en mode développement")
    
    # Test rapide
    print("\n🧪 Test rapide du package...")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "from tych import double_pendulum_random_list; print('✅ Import OK'); "
            "nums = double_pendulum_random_list(5); print(f'✅ Génération OK: {nums}')"
        ], capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Test échoué: {e.stderr}")
    
    print("\n🎉 Build terminé avec succès!")
    print("\nCommandes utiles:")
    print(f"  - Installer: {uv_path} pip install dist/tych-0.1.0-py3-none-any.whl")
    print(f"  - Publier: {uv_path} publish dist/*")
    print(f"  - Rebuild: python {__file__}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
