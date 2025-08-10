#!/usr/bin/env python3
"""
Script standalone pour exécuter les tests du projet Tych.

Ce script permet de lancer les tests sans avoir besoin d'installer pytest
séparément ou de configurer un environnement de développement complexe.

Usage:
    python run_tests.py                    # Tous les tests
    python run_tests.py -v                 # Mode verbose
    python run_tests.py -k test_pendulum   # Tests spécifiques
    python run_tests.py --unit             # Tests unitaires uniquement
    python run_tests.py --integration      # Tests d'intégration uniquement
    python run_tests.py --fast             # Tests rapides (sans slow)
    python run_tests.py --coverage         # Avec couverture de code
    python run_tests.py --help             # Aide
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def get_project_root():
    """Retourne le répertoire racine du projet."""
    return Path(__file__).parent.absolute()


def check_dependencies():
    """Vérifie que les dépendances nécessaires sont installées."""
    required_packages = ['pytest', 'numpy', 'matplotlib', 'scipy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Dépendances manquantes: {', '.join(missing_packages)}")
        print("Installez-les avec:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def run_tests(args):
    """Exécute les tests avec les arguments spécifiés."""
    project_root = get_project_root()
    tests_dir = project_root / "tests"
    
    # Construction de la commande pytest
    cmd = [sys.executable, "-m", "pytest"]
    
    # Ajouter le répertoire des tests
    cmd.append(str(tests_dir))
    
    # Options de base
    cmd.extend(["-v", "--tb=short", "--strict-markers", "--strict-config"])
    
    # Filtres par type de test
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Filtres par nom de test
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    # Options de verbosité
    if args.verbose:
        cmd.append("-vv")
    elif args.quiet:
        cmd.append("-q")
    
    # Couverture de code
    if args.coverage:
        try:
            __import__('pytest_cov')
            cmd.extend([
                "--cov=tych",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=80"
            ])
        except ImportError:
            print("⚠️  pytest-cov non installé, couverture désactivée")
    
    # Parallélisation si pytest-xdist est disponible
    if args.parallel:
        try:
            __import__('pytest_xdist')
            cmd.extend(["-n", str(args.parallel)])
        except ImportError:
            print("⚠️  pytest-xdist non installé, parallélisation désactivée")
    
    # Arrêt au premier échec
    if args.fail_fast:
        cmd.append("-x")
    
    # Options supplémentaires
    if args.pytest_args:
        cmd.extend(args.pytest_args)
    
    print(f"🚀 Exécution des tests...")
    print(f"📁 Répertoire: {tests_dir}")
    print(f"🔧 Commande: {' '.join(cmd)}")
    print("-" * 50)
    
    # Exécution
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrompus par l'utilisateur")
        return 1
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests: {e}")
        return 1


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Exécuteur de tests standalone pour Tych",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python run_tests.py                    # Tous les tests
  python run_tests.py -v                 # Mode verbose
  python run_tests.py -k pendulum        # Tests contenant "pendulum"
  python run_tests.py --unit             # Tests unitaires seulement
  python run_tests.py --fast             # Tests rapides (sans slow)
  python run_tests.py --coverage         # Avec couverture de code
  python run_tests.py --parallel 4       # Tests en parallèle (4 workers)
  python run_tests.py -x                 # Arrêt au premier échec
        """
    )
    
    # Filtres de tests
    test_group = parser.add_argument_group("Filtres de tests")
    test_group.add_argument(
        "--unit", 
        action="store_true",
        help="Exécuter uniquement les tests unitaires"
    )
    test_group.add_argument(
        "--integration", 
        action="store_true",
        help="Exécuter uniquement les tests d'intégration"
    )
    test_group.add_argument(
        "--fast", 
        action="store_true",
        help="Exécuter uniquement les tests rapides (exclut les tests marqués 'slow')"
    )
    test_group.add_argument(
        "-k", "--keyword",
        help="Exécuter uniquement les tests correspondant au mot-clé"
    )
    
    # Options d'affichage
    display_group = parser.add_argument_group("Options d'affichage")
    display_group.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Mode verbose (plus de détails)"
    )
    display_group.add_argument(
        "-q", "--quiet", 
        action="store_true",
        help="Mode silencieux (moins de sortie)"
    )
    
    # Options de performance
    perf_group = parser.add_argument_group("Options de performance")
    perf_group.add_argument(
        "--parallel", 
        type=int, 
        metavar="N",
        help="Nombre de workers pour l'exécution en parallèle"
    )
    perf_group.add_argument(
        "-x", "--fail-fast", 
        action="store_true",
        help="Arrêter à la première erreur"
    )
    
    # Options de couverture
    coverage_group = parser.add_argument_group("Options de couverture")
    coverage_group.add_argument(
        "--coverage", 
        action="store_true",
        help="Générer un rapport de couverture de code"
    )
    
    # Options avancées
    advanced_group = parser.add_argument_group("Options avancées")
    advanced_group.add_argument(
        "--pytest-args", 
        nargs=argparse.REMAINDER,
        help="Arguments supplémentaires à passer à pytest"
    )
    advanced_group.add_argument(
        "--check-deps", 
        action="store_true",
        help="Vérifier les dépendances et quitter"
    )
    
    args = parser.parse_args()
    
    # Vérification des dépendances
    if args.check_deps:
        if check_dependencies():
            print("✅ Toutes les dépendances sont installées")
            return 0
        else:
            return 1
    
    # Vérification des dépendances avant l'exécution
    if not check_dependencies():
        return 1
    
    # Validation des arguments
    if args.unit and args.integration:
        print("❌ Erreur: --unit et --integration sont mutuellement exclusifs")
        return 1
    
    if args.verbose and args.quiet:
        print("❌ Erreur: --verbose et --quiet sont mutuellement exclusifs")
        return 1
    
    # Information sur l'environnement
    print("🔬 Tych Test Runner")
    print(f"🐍 Python: {sys.version}")
    print(f"📍 Répertoire: {get_project_root()}")
    
    # Exécution des tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
