"""
Tych - Un package pour la génération de nombres pseudo-aléatoires basée sur la physique chaotique

Ce package contient des modules pour :
- Génération de nombres aléatoires à partir de systèmes chaotiques (double pendule)
- Comparaison et analyse statistique de générateurs de nombres aléatoires
"""

__version__ = "0.1.0"
__author__ = "Yatoub"
__email__ = "votre.email@example.com"

# Import conditionnel pour éviter les erreurs si les dépendances ne sont pas installées
try:
    from .pendulum import double_pendulum_random_list
    _has_pendulum = True
except ImportError:
    _has_pendulum = False
    double_pendulum_random_list = None

try:
    from .comparison import compare_random_generators
    _has_comparison = True
except ImportError:
    _has_comparison = False
    compare_random_generators = None

# Liste des exports publics
__all__ = []

if _has_pendulum:
    __all__.append("double_pendulum_random_list")

if _has_comparison:
    __all__.append("compare_random_generators")
