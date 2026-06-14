# Tych

Générateur de nombres pseudo-aléatoires basé sur la dynamique chaotique du double pendule.

Tych exploite la sensibilité extrême aux conditions initiales des systèmes hamiltoniens non-linéaires pour produire des séquences de nombres uniformément distribués dans [0, 1], avec un exposant de Lyapunov positif qui garantit la divergence exponentielle des trajectoires.

---

## Installation

```bash
# Dépendances de base (génération + statistiques)
pip install tych

# Avec l'interface web
pip install 'tych[web]'
```

Prérequis : Python ≥ 3.9, numpy, scipy.

---

## Utilisation rapide

### Python

```python
from tych import double_pendulum_random_list

# Génération simple — retourne une liste de float dans [0, 1]
nombres = double_pendulum_random_list(n=1000)

# Paramètres physiques personnalisés
nombres = double_pendulum_random_list(
    n=5000,
    n_pendulums=5,   # pendules couplés — plus = plus de chaos
    noise_level=0.3, # bruit gaussien ajouté à l'état
    m1=1.2, m2=0.8,  # masses (kg)
    l1=1.0, l2=1.5,  # longueurs de tige (m)
    g=9.81,          # gravité (m/s²)
    damping=0.999,   # coefficient d'amortissement
)
```

### Évaluation de la qualité

```python
from tych import compute_quality_score

score = compute_quality_score(nombres)
print(score["global"])          # score global [0–100]
print(score["uniformite"])      # KS + χ² — distribution uniforme
print(score["independance"])    # ACF + runs test — absence de corrélations
print(score["entropie"])        # Shannon + ApEn — imprévisibilité
print(score["moments"])         # moyenne (cible 0.5) et σ (cible 1/√12)
```

### Exposant de Lyapunov

```python
from tych import compute_lyapunov

lya = compute_lyapunov(m1=1.0, m2=1.0, l1=1.0, l2=1.0, g=9.81, damping=0.999)
# λ > 0 → chaos déterministe confirmé
print(f"λ = {lya:.4f} bits/step")
```

### CLI

```bash
# Générer des nombres
python main.py generate -n 1000
python main.py generate -n 5000 --pendulums 5 --noise 0.3 -o sortie.txt

# Interface web interactive
python main.py serve
python main.py serve --port 8080 --reload
```

---

## Interface web

```bash
python main.py serve
# → http://127.0.0.1:8000
```

L'interface propose trois onglets :

**Génération** — anime les pendules en temps réel et affiche la distribution des nombres produits.

**Évaluation** — soumet une séquence à quatre tests statistiques indépendants et retourne un score /100 avec un radar chart, un histogramme, l'autocorrélation (ACF) et le spectre de puissance (FFT).

**Exploration** — fait varier un paramètre physique (bruit, nombre de pendules, masses, longueurs, gravité, amortissement) sur une plage et trace la courbe score vs paramètre pour trouver la configuration optimale.

---

## Algorithme

1. **Intégration RK4** — équations du mouvement du double pendule (θ₁, θ₂, ω₁, ω₂)
2. **Pendules couplés** — `n_pendulums` systèmes simulés avec des conditions initiales distinctes
3. **Extraction** — les angles θ₂ de chaque pendule sont normalisés modulo 2π dans [0, 1]
4. **Bruit gaussien** — perturbation de l'état à chaque pas pour briser les corrélations résiduelles
5. **Hachage SHA-256** — les sorties sont passées par SHA-256 pour garantir l'uniformité finale
6. **Permutation** — mélange aléatoire de l'ensemble des valeurs produites

---

## Métriques de qualité (`tych.statistics`)

| Catégorie | Tests | Poids |
|-----------|-------|-------|
| Uniformité | Kolmogorov-Smirnov, χ² | 30 % |
| Indépendance | ACF (lags 1–20), Wald-Wolfowitz runs test | 30 % |
| Entropie | Shannon (H/H_max), Approximate Entropy (ApEn) | 25 % |
| Moments | Moyenne (cible 0,500), σ (cible 1/√12 ≈ 0,2887) | 15 % |

---

## API REST (interface web)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/generate` | Génère n nombres, retourne histogramme + stats |
| POST | `/api/quality` | Score qualité complet (ACF, spectre, entropie…) |
| POST | `/api/lab/sweep` | Courbe score vs paramètre physique |
| POST | `/api/trajectory` | Trajectoires pour l'animation canvas |
| POST | `/api/compare` | Comparaison avec /dev/urandom (KS, KDE, QQ-plot) |

---

## Structure du projet

```
tych/
├── __init__.py         # API publique
├── pendulum.py         # Générateur RK4 + simulation de trajectoires
├── comparison.py       # Comparaison avec /dev/urandom (KS, KDE, QQ)
├── statistics.py       # Métriques avancées : ACF, runs, entropie, Lyapunov
├── cli.py              # Point d'entrée de la commande `tych`
└── web/
    ├── app.py          # API FastAPI
    └── static/
        ├── index.html
        ├── css/mocha.css
        └── js/
            ├── app.js
            ├── charts.js
            └── pendulum.js
main.py                 # CLI via `python main.py`
pyproject.toml
```

---

## Docker

```bash
# Build
docker build -t tych .

# Lancer l'interface web sur http://localhost:8000
docker run -p 8000:8000 tych

# Port personnalisé
docker run -p 9000:8000 tych
```

L'image est basée sur `python:3.12-slim`, installe l'extra `[web]` (FastAPI + uvicorn) et expose le port 8000. Le serveur écoute sur `0.0.0.0` pour être accessible depuis l'hôte.

---

## Développement

```bash
# Installer avec toutes les dépendances
pip install -e '.[web,dev]'

# Tests
pytest

# Interface web avec rechargement automatique
python main.py serve --reload
```

---

## Avertissement

Tych est conçu à des fins éducatives et de recherche. Ne pas utiliser pour des applications cryptographiques critiques — préférer les générateurs certifiés du système d'exploitation (`os.urandom`, `secrets`).

---

## Licence

MIT
