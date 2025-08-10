"""
Point d'entrée principal pour le package Tych.
"""

import argparse
from tych import double_pendulum_random_list, compare_random_generators


def main():
    """Fonction principale avec interface en ligne de commande."""
    parser = argparse.ArgumentParser(description="Tych - Générateur de nombres aléatoires basé sur la physique chaotique")
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Sous-commande pour générer des nombres aléatoires
    gen_parser = subparsers.add_parser('generate', help='Générer des nombres aléatoires')
    gen_parser.add_argument('-n', '--count', type=int, default=1000, 
                           help='Nombre de valeurs à générer (défaut: 1000)')
    gen_parser.add_argument('-p', '--pendulums', type=int, default=3,
                           help='Nombre de pendules (défaut: 3)')
    gen_parser.add_argument('--noise', type=float, default=0.2,
                           help='Niveau de bruit (défaut: 0.2)')
    gen_parser.add_argument('-o', '--output', type=str,
                           help='Fichier de sortie (optionnel)')

    # Sous-commande pour comparer les générateurs
    comp_parser = subparsers.add_parser('compare', help='Comparer avec d\'autres générateurs')
    comp_parser.add_argument('-n', '--count', type=int, default=10000,
                            help='Taille de l\'échantillon (défaut: 10000)')
    comp_parser.add_argument('-p', '--pendulums', type=int, default=3,
                            help='Nombre de pendules (défaut: 3)')
    comp_parser.add_argument('--noise', type=float, default=0.2,
                            help='Niveau de bruit (défaut: 0.2)')
    comp_parser.add_argument('-o', '--output', type=str, default='comparison.png',
                            help='Fichier de sortie pour le graphique')
    comp_parser.add_argument('-s','--show', action='store_true',
                            help='Afficher le graphique (défaut: False)')

    args = parser.parse_args()
    
    if args.command == 'generate':
        print(f"Génération de {args.count} nombres aléatoires...")
        numbers = double_pendulum_random_list(
            n=args.count, 
            n_pendulums=args.pendulums, 
            noise_level=args.noise
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
            show_plot=args.show
        )
        print("\n=== Résultats de la comparaison ===")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"{key}: {value:.6f}")
            else:
                print(f"{key}: {value}")
    
    else:
        print("Bienvenue dans Tych!")
        print("Utilisez 'python main.py generate' pour générer des nombres aléatoires")
        print("Utilisez 'python main.py compare' pour comparer les générateurs")
        print("Utilisez 'python main.py -h' pour plus d'aide")


if __name__ == "__main__":
    main()
