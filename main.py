"""
Point d'entrée principal pour le package Tych.
"""

import argparse
from tych import double_pendulum_random_list, compare_random_generators


def main():
    """Fonction principale avec interface en ligne de commande."""
    parser = argparse.ArgumentParser(description="Tych - Générateur de nombres aléatoires basé sur la physique chaotique")

    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')

    # Sous-commande : générer des nombres aléatoires
    gen_parser = subparsers.add_parser('generate', help='Générer des nombres aléatoires')
    gen_parser.add_argument('-n', '--count', type=int, default=1000,
                            help='Nombre de valeurs à générer (défaut: 1000)')
    gen_parser.add_argument('-p', '--pendulums', type=int, default=3,
                            help='Nombre de pendules (défaut: 3)')
    gen_parser.add_argument('--noise', type=float, default=0.2,
                            help='Niveau de bruit (défaut: 0.2)')
    gen_parser.add_argument('-o', '--output', type=str,
                            help='Fichier de sortie (optionnel)')

    # Sous-commande : comparer les générateurs
    comp_parser = subparsers.add_parser('compare', help="Comparer avec d'autres générateurs")
    comp_parser.add_argument('-n', '--count', type=int, default=10000,
                             help="Taille de l'échantillon (défaut: 10000)")
    comp_parser.add_argument('-p', '--pendulums', type=int, default=3,
                             help='Nombre de pendules (défaut: 3)')
    comp_parser.add_argument('--noise', type=float, default=0.2,
                             help='Niveau de bruit (défaut: 0.2)')
    comp_parser.add_argument('-o', '--output', type=str, default='comparison.png',
                             help='Fichier de sortie pour le graphique')
    comp_parser.add_argument('-s', '--show', action='store_true',
                             help='Afficher le graphique (défaut: False)')

    # Sous-commande : interface web
    serve_parser = subparsers.add_parser('serve', help="Lancer l'interface web")
    serve_parser.add_argument('--host', type=str, default='127.0.0.1',
                              help='Hôte (défaut: 127.0.0.1)')
    serve_parser.add_argument('--port', type=int, default=8000,
                              help='Port (défaut: 8000)')
    serve_parser.add_argument('--reload', action='store_true',
                              help='Rechargement automatique (développement)')

    args = parser.parse_args()

    if args.command == 'generate':
        print(f"Génération de {args.count} nombres aléatoires...")
        numbers = double_pendulum_random_list(
            n=args.count,
            n_pendulums=args.pendulums,
            noise_level=args.noise,
        )
        if args.output:
            with open(args.output, 'w') as f:
                for num in numbers:
                    f.write(f"{num}\n")
            print(f"Résultats sauvegardés dans {args.output}")
        else:
            print(f"Premiers 10 nombres: {numbers[:10]}")
            print(f"Moyenne: {sum(numbers)/len(numbers):.4f}")

    elif args.command == 'compare':
        print("Comparaison des générateurs de nombres aléatoires...")
        results = compare_random_generators(
            n=args.count,
            n_pendulums=args.pendulums,
            noise_level=args.noise,
            output_filename=args.output,
            show_plot=args.show,
        )
        print("\n=== Résultats de la comparaison ===")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"{key}: {value:.6f}")
            else:
                print(f"{key}: {value}")

    elif args.command == 'serve':
        try:
            import uvicorn
        except ImportError:
            print("❌ uvicorn n'est pas installé.")
            print("   Installez l'extra web : pip install 'tych[web]'")
            raise SystemExit(1)
        try:
            from tych.web.app import app  # noqa: F401
        except ImportError as e:
            print(f"❌ Impossible de charger l'interface web : {e}")
            print("   Installez l'extra web : pip install 'tych[web]'")
            raise SystemExit(1)

        print(f"🚀 Tych — interface web sur http://{args.host}:{args.port}")
        uvicorn.run(
            "tych.web.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )

    else:
        print("Bienvenue dans Tych!")
        print("  python main.py generate   — générer des nombres aléatoires")
        print("  python main.py compare    — comparer les générateurs")
        print("  python main.py serve      — lancer l'interface web")
        print("  python main.py -h         — aide complète")


if __name__ == "__main__":
    main()
