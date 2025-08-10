"""
Interface en ligne de commande pour Tych.
"""

import sys
import os

# Ajouter le dossier parent au path pour permettre l'import du main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main

if __name__ == "__main__":
    main()
