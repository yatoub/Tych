"""
Tych - Un package pour la génération de nombres pseudo-aléatoires basée sur la physique chaotique

Ce package contient des modules pour :
- Génération de nombres aléatoires à partir de systèmes chaotiques (double pendule)
- Comparaison et analyse statistique de générateurs de nombres aléatoires
"""

__version__ = "0.1.1"
__author__ = "Yatoub"
__email__ = "votre.email@example.com"

try:
    from .pendulum import double_pendulum_random_list, simulate_trajectory
    _has_pendulum = True
except ImportError:
    _has_pendulum = False
    double_pendulum_random_list = None
    simulate_trajectory = None

try:
    from .comparison import compare_random_generators, compute_comparison
    _has_comparison = True
except ImportError:
    _has_comparison = False
    compare_random_generators = None
    compute_comparison = None

try:
    from .statistics import compute_quality_score, compute_lyapunov
    _has_statistics = True
except ImportError:
    _has_statistics = False
    compute_quality_score = None
    compute_lyapunov = None

__all__ = []

if _has_pendulum:
    __all__ += ["double_pendulum_random_list", "simulate_trajectory"]

if _has_comparison:
    __all__ += ["compare_random_generators", "compute_comparison"]

if _has_statistics:
    __all__ += ["compute_quality_score", "compute_lyapunov"]
