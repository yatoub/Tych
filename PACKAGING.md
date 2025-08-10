# Guide de packaging avec uv pour Tych

## Configuration du projet

Le projet Tych est maintenant configuré pour utiliser **uv** comme gestionnaire de packages et outil de build. Voici les principales configurations :

### `pyproject.toml`

- **Build system** : `hatchling` (compatible uv)
- **Dépendances** : numpy, matplotlib, scipy
- **Version Python** : >=3.9 (plus compatible)
- **Configuration uv** : Section `[tool.uv]` pour les dépendances de développement

## Commandes de packaging

### 🔧 **Installation d'uv**
```bash
pip install uv
```

### 📦 **Build du package**
```bash
# Build complet (source + wheel)
uv build

# Build avec isolation désactivée (si problèmes)
uv build --no-build-isolation

# Build uniquement wheel
uv build --wheel

# Build uniquement source distribution
uv build --sdist
```

### 🔄 **Gestion des dépendances**
```bash
# Synchroniser les dépendances
uv sync

# Installer en mode développement
uv pip install -e .

# Ajouter une dépendance
uv add numpy

# Ajouter une dépendance de développement
uv add --dev pytest
```

### 🧪 **Tests et vérification**
```bash
# Test rapide d'import
python -c "from tych import double_pendulum_random_list; print('OK')"

# Test d'installation du wheel
python test_install.py

# Lancer les exemples
python main.py generate -n 10
```

### 🚀 **Publication**
```bash
# Publication sur TestPyPI (pour tests)
uv publish --repository testpypi dist/*

# Publication sur PyPI (production)
uv publish dist/*
```

## Scripts utiles

### `build.py`
Script Python automatisé pour :
- Détecter uv automatiquement
- Nettoyer les builds précédents  
- Synchroniser les dépendances
- Construire le package
- Tester l'installation

Usage : `python build.py`

### `test_install.py`
Script de test d'installation dans un environnement isolé :
- Crée un venv temporaire
- Installe le wheel
- Teste les imports et la génération

Usage : `python test_install.py`

### `Makefile`
Commandes make pour automatiser les tâches courantes :
```bash
make help          # Aide
make build         # Build complet
make test          # Tests rapides
make clean         # Nettoyage
make dev-install   # Installation développement
make publish-test  # Publication TestPyPI
```

## Structure des fichiers générés

```
dist/
├── tych-0.1.0-py3-none-any.whl    # Wheel (installation rapide)
└── tych-0.1.0.tar.gz              # Source distribution
```

### Wheel (`.whl`)
- Format binaire optimisé pour l'installation
- Installation rapide avec `pip install tych-0.1.0-py3-none-any.whl`
- Taille : ~10KB

### Source distribution (`.tar.gz`)
- Code source complet avec métadonnées
- Installation avec compilation si nécessaire
- Taille : ~40KB

## Avantages d'uv

### ⚡ **Performance**
- Build et installation ultra-rapides
- Résolution de dépendances optimisée
- Cache intelligent

### 🔒 **Fiabilité**
- Lock files précis (`uv.lock`)
- Reproductibilité garantie
- Gestion des conflits de dépendances

### 🛠️ **Simplicité**
- Commandes unifiées (`uv build`, `uv publish`, etc.)
- Configuration centralisée dans `pyproject.toml`
- Compatible avec l'écosystème Python standard

## Workflow de développement

1. **Développement** : `uv sync` + `uv pip install -e .`
2. **Test** : `python test_install.py`
3. **Build** : `uv build` ou `python build.py`
4. **Test publication** : `uv publish --repository testpypi dist/*`
5. **Publication** : `uv publish dist/*`

## Configuration CI/CD

Exemple pour GitHub Actions :
```yaml
 - name: Install uv
   run: pip install uv

 - name: Test package
  run: uv run pytest

 - name: Build package
   run: uv build
```

---

