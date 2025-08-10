# Tych

Tych est un package Python pour la génération de nombres pseudo-aléatoires basée sur la dynamique chaotique du double pendule. Ce générateur exploite la sensibilité aux conditions initiales des systèmes chaotiques pour produire des séquences de nombres apparemment aléatoires.

## Fonctionnalités

- **Générateur basé sur le chaos physique** : Utilise la dynamique du double pendule pour générer des nombres pseudo-aléatoires
- **Comparaison statistique** : Outils pour comparer la qualité de différents générateurs de nombres aléatoires
- **Interface en ligne de commande** : Utilisation facile via des commandes CLI
- **Analyses graphiques** : Génération automatique de graphiques pour l'analyse statistique

## Installation

### Prérequis

- **Python** >= 3.8 (recommandé 3.9+)
- **numpy** >= 1.24.0
- **matplotlib** >= 3.10.5 (pour les graphiques de comparaison)
- **scipy** >= 1.16.1 (pour les tests statistiques)

### Installation du package

1. **Naviguez vers le dossier du projet :**
   ```bash
   # Unix/Linux/macOS
   cd /path/to/Tych
   
   # Windows
   cd C:\path\to\Tych
   ```

2. **Créez et activez un environnement virtuel (recommandé) :**
   ```bash
   # Création de l'environnement virtuel
   python -m venv .venv
   
   # Activation - Unix/Linux/macOS
   source .venv/bin/activate
   
   # Activation - Windows PowerShell
   .venv\Scripts\Activate.ps1
   
   # Activation - Windows Command Prompt
   .venv\Scripts\activate.bat
   ```

3. **Installez le package en mode développement :**
   ```bash
   pip install -e .
   ```

   Ou installation des dépendances uniquement :
   ```bash
   pip install matplotlib scipy numpy
   ```

## Utilisation

### 1. Interface en ligne de commande

```bash
# Aide générale
python main.py -h

# Générer 100 nombres aléatoires
python main.py generate -n 100

# Sauvegarder dans un fichier
python main.py generate -n 1000 -o mes_nombres.txt

# Comparer avec d'autres générateurs
python main.py compare -n 5000

# Paramètres avancés
python main.py generate -n 1000 --pendulums 5 --noise 0.3
```

### 2. Utilisation en Python

```python
# Import du package
from tych import double_pendulum_random_list

# Génération simple
nombres = double_pendulum_random_list(n=100)
print(f"Généré {len(nombres)} nombres")
print(f"Échantillon: {nombres[:5]}")

# Avec paramètres personnalisés
nombres_custom = double_pendulum_random_list(
    n=500,           # Nombre de valeurs
    n_pendulums=5,   # Nombre de pendules
    noise_level=0.3  # Niveau de bruit
)

# Comparaison des générateurs
from tych import compare_random_generators
results = compare_random_generators(n=10000)
print(f"KS statistic: {results['ks_statistic']}")
```

## Modules

### `tych.pendulum`
Contient le générateur principal basé sur le double pendule chaotique.

**Fonction principale :**
- `double_pendulum_random_list(n, n_pendulums, noise_level)` : Génère une liste de nombres pseudo-aléatoires

**Paramètres du générateur :**
- **n** : Nombre de valeurs à générer
- **n_pendulums** : Plus il y a de pendules, plus le chaos est complexe (défaut: 3)
- **noise_level** : Bruit ajouté pour casser les corrélations (défaut: 0.01)

### `tych.comparison`
Outils pour comparer et analyser statistiquement différents générateurs.

**Fonction principale :**
- `compare_random_generators()` : Compare le générateur Tych avec `/dev/urandom`

**Analyses incluses :**
- Test de Kolmogorov-Smirnov
- Histogrammes et estimations de densité par noyau (KDE)
- QQ-plots pour l'analyse de distribution

## Algorithme

Le générateur Tych utilise :

1. **Simulation physique** : Équations du mouvement du double pendule
2. **Systèmes multiples** : Plusieurs pendules simulés en parallèle
3. **Mélange chaotique** : Combinaison des variables d'état (angles et vitesses)
4. **Hachage cryptographique** : SHA-256 pour casser les corrélations résiduelles
5. **Permutation finale** : Mélange aléatoire des résultats

## Qualité de l'aléatoire

Le générateur a été testé pour :
- Distribution uniforme des valeurs
- Absence de corrélations périodiques
- Comparaison statistique avec des générateurs standards

## Développement

```bash
# Installation en mode développement
pip install -e ".[dev]"

# Tests
pytest

# Formatage du code
black tych/

# Vérification du style
flake8 tych/
```

## Commandes utiles

```bash
# Vérifier l'installation
python -c "from tych import double_pendulum_random_list; print('Installation OK')"

# Test rapide du générateur
python -c "from tych.pendulum import double_pendulum_random_list; print('Échantillon:', double_pendulum_random_list(5))"

# Générer et analyser
python main.py generate -n 10000 -o analyse.txt
python main.py compare -n 10000 -o comparaison.png

# Vérifier la version Python
python --version

# Lister les packages installés
pip list | grep tych  # Unix/Linux/macOS
pip list | findstr tych  # Windows
```

## Notes par système d'exploitation

### 🐧 **Linux/Ubuntu/Debian**
```bash
# Installation des dépendances système (si nécessaire)
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Utilisation
python3 main.py generate -n 100
```

### 🍎 **macOS**
```bash
# Avec Homebrew (recommandé)
brew install python

# Ou utiliser python3 explicitement
python3 main.py generate -n 100
```

### 🪟 **Windows**
```powershell
# PowerShell
python main.py generate -n 100

# Ou avec py launcher
py main.py generate -n 100
```

## Résolution de problèmes

### Problèmes d'import
```bash
# Vérifier le PYTHONPATH
python -c "import sys; print(sys.path)"

# Réinstaller en mode développement
pip uninstall tych
pip install -e .
```

### Problèmes de dépendances
```bash
# Installer les dépendances manuellement
pip install numpy matplotlib scipy

# Mise à jour des packages
pip install --upgrade numpy matplotlib scipy
```

### Problèmes de permissions (Unix/Linux)
```bash
# Utiliser --user pour l'installation locale
pip install --user -e .

# Ou modifier les permissions du dossier
sudo chown -R $USER:$USER .
```

## Structure du projet

```
Tych/
├── tych/                    # Package principal
│   ├── __init__.py         # Point d'entrée du package
│   ├── pendulum.py         # Générateur basé sur le double pendule
│   ├── comparison.py       # Outils de comparaison statistique
│   └── cli.py             # Interface en ligne de commande
├── main.py                # Script principal
├── example.py             # Exemple d'utilisation
├── pyproject.toml         # Configuration du package
├── README.md              # Documentation
└── uv.lock               # Verrouillage des dépendances
```

## Licence

MIT - Voir le fichier LICENSE pour plus de détails.

## Avertissement

Ce générateur est conçu à des fins éducatives et de recherche. Pour des applications cryptographiques critiques, utilisez des générateurs certifiés comme ceux fournis par votre système d'exploitation.

---
