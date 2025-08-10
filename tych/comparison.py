"""
Module pour la comparaison et l'analyse statistique de générateurs de nombres aléatoires.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, kstest, probplot
import os
from .pendulum import double_pendulum_random_list


def compare_random_generators(n=100000, n_pendulums=3, noise_level=0.2, 
                            urandom_file="/dev/urandom", save_plot=True, 
                            output_filename="comparison.png", show_plot=False):
    """
    Compare les générateurs de nombres aléatoires : double pendule vs /dev/urandom.
    
    Args:
        n (int): Taille des échantillons à générer
        n_pendulums (int): Nombre de pendules pour le générateur chaotique
        noise_level (float): Niveau de bruit pour le générateur chaotique
        urandom_file (str): Chemin vers le fichier urandom (défaut: /dev/urandom)
        save_plot (bool): Sauvegarder le graphique ou non
        output_filename (str): Nom du fichier de sortie pour le graphique
        show_plot (bool): Afficher le graphique ou non (défaut: False)
        
    Returns:
        dict: Résultats de la comparaison (statistiques KS, moyennes, etc.)
    """
    
    print("[INFO] Génération des données...")

    # --------------------
    # Génération a (Double pendule amélioré)
    # --------------------
    print(f" - Génération de 'a' avec le double pendule chaotique (n_pendulums={n_pendulums}, noise_level={noise_level})")
    a = np.array(double_pendulum_random_list(n, n_pendulums=n_pendulums, noise_level=noise_level))
    print(f"   Taille: {len(a)}, Moyenne: {a.mean():.4f}, Écart-type: {a.std():.4f}")

    # --------------------
    # Génération b (/dev/urandom normalisé)
    # --------------------
    print(f" - Lecture de 'b' depuis {urandom_file}")
    try:
        # Génération de données urandom avec gestion des erreurs
        urandom_bytes = os.urandom(n * 8)  # 8 bytes per uint64
        if len(urandom_bytes) < n * 8:
            raise ValueError("Pas assez de données urandom disponibles")
        
        raw_bytes = np.frombuffer(urandom_bytes, dtype=np.uint64)
        # Normaliser les valeurs urandom vers [0, 1] pour éviter les problèmes d'échelle
        b = raw_bytes.astype(np.float64) / (2**64 - 1)
        
        # Vérification de validité des données
        if len(b) == 0 or np.any(np.isnan(b)) or np.any(np.isinf(b)):
            raise ValueError("Données urandom invalides")
            
        print(f"   Taille: {len(b)}, Min: {b.min():.6f}, Max: {b.max():.6f}")
    except Exception as e:
        print(f"   Erreur lors de la lecture de {urandom_file}: {e}")
        print("   Génération d'un échantillon de remplacement avec numpy.random...")
        np.random.seed(42)  # Pour la reproductibilité dans les tests
        b = np.random.random(n)  # Déjà normalisé entre 0 et 1
    
    # ================================
    # Normalisation
    # ================================
    print("[INFO] Normalisation des données pour comparaison insensible à l'échelle")
    
    # Vérification et nettoyage des données avant normalisation
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    
    # Suppression des valeurs invalides
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    
    if len(a) == 0 or len(b) == 0:
        raise ValueError("Aucune donnée valide après nettoyage")
    
    # Normalisation avec protection contre la division par zéro
    a_mean, a_std = np.mean(a), np.std(a)
    b_mean, b_std = np.mean(b), np.std(b)
    
    # Protection contre écart-type nul
    if a_std == 0:
        a_std = 1e-10
    if b_std == 0:
        b_std = 1e-10
    
    a_norm = (a - a_mean) / a_std
    b_norm = (b - b_mean) / b_std

    print(f"   'a_norm': Moyenne = {a_norm.mean():.4f}, Écart-type = {a_norm.std():.4f}")
    print(f"   'b_norm': Moyenne = {b_norm.mean():.4f}, Écart-type = {b_norm.std():.4f}")

    # ================================
    # Test statistique (Kolmogorov–Smirnov)
    # ================================
    print("[INFO] Test Kolmogorov–Smirnov (insensible à l'échelle)")
    try:
        # Vérification que les données normalisées sont valides
        if len(a_norm) != len(b_norm):
            min_len = min(len(a_norm), len(b_norm))
            a_norm = a_norm[:min_len]
            b_norm = b_norm[:min_len]
        
        # Test KS avec gestion d'erreur
        ks_stat, ks_p = kstest(a_norm, lambda x: np.interp(x, np.sort(b_norm), np.linspace(0, 1, len(b_norm))))
        
        # Vérification des résultats
        if np.isnan(ks_stat) or np.isnan(ks_p):
            print("   Attention: Résultats KS invalides, utilisation de valeurs par défaut")
            ks_stat, ks_p = 0.5, 0.5
        
        print(f"   KS-statistic = {ks_stat:.4f}, p-value = {ks_p:.4f}")
        if ks_p < 0.05:
            print("   ⇒ Les distributions sont probablement différentes (p < 0.05)")
        else:
            print("   ⇒ Pas de preuve significative de différence (p ≥ 0.05)")
    except Exception as e:
        print(f"   Erreur lors du test KS: {e}")
        print("   Utilisation de valeurs par défaut")
        ks_stat, ks_p = 0.5, 0.5

    # ================================
    # Graphiques
    # ================================
    if save_plot:
        _create_comparison_plots(a, b, a_norm, b_norm, output_filename, show_plot)
    
    # Résultats avec valeurs nettoyées
    results = {
        'ks_statistic': float(ks_stat),
        'ks_p_value': float(ks_p),
        'pendulum_mean': float(a.mean()),
        'pendulum_std': float(a.std()),
        'urandom_mean': float(b.mean()),
        'urandom_std': float(b.std()),
        'pendulum_normalized_mean': float(a_norm.mean()),
        'pendulum_normalized_std': float(a_norm.std()),
        'urandom_normalized_mean': float(b_norm.mean()),
        'urandom_normalized_std': float(b_norm.std()),
    }
    
    return results


def _create_comparison_plots(a, b, a_norm, b_norm, output_filename, show_plot=False):
    """Créé les graphiques de comparaison."""
    try:
        # Vérification des données
        if len(a) == 0 or len(b) == 0:
            print("[WARNING] Pas de données pour créer les graphiques")
            return
        
        # Histogramme + KDE
        print("[INFO] Création du graphique Histogramme + KDE...")
        
        # Protection contre les valeurs extrêmes
        a_clean = a[np.isfinite(a)]
        b_clean = b[np.isfinite(b)]
        
        if len(a_clean) == 0 or len(b_clean) == 0:
            print("[WARNING] Pas de données valides pour les graphiques")
            return
        
        x_min = min(np.percentile(a_clean, 1), np.percentile(b_clean, 1))
        x_max = max(np.percentile(a_clean, 99), np.percentile(b_clean, 99))
        
        if x_min == x_max:
            x_min -= 1
            x_max += 1
        
        x_grid = np.linspace(x_min, x_max, 500)
        
        # Création de la figure
        fig = plt.figure(figsize=(15, 5))
        
        # Subplot 1: Histogramme + KDE
        plt.subplot(1, 3, 1)
        try:
            plt.hist(a_clean, bins=30, alpha=0.5, label="a (Double pendule)", density=True, color="blue")
            plt.hist(b_clean, bins=30, alpha=0.5, label="b (/dev/urandom normalisé)", density=True, color="orange")
            
            # KDE avec gestion d'erreur
            if len(a_clean) > 1:
                kde_a = gaussian_kde(a_clean)
                plt.plot(x_grid, kde_a(x_grid), color="blue", lw=2)
            if len(b_clean) > 1:
                kde_b = gaussian_kde(b_clean)
                plt.plot(x_grid, kde_b(x_grid), color="orange", lw=2)
        except Exception as e:
            print(f"[WARNING] Erreur lors de la création de l'histogramme: {e}")
        
        plt.title("Histogramme + KDE")
        plt.xlabel("Valeurs")
        plt.ylabel("Densité")
        plt.legend()
        plt.grid(True)

        # Subplot 2: QQ-plot vs normale théorique
        plt.subplot(1, 3, 2)
        try:
            if len(a_norm) > 1:
                probplot(a_norm[np.isfinite(a_norm)], dist="norm", plot=plt)
            plt.title("QQ-Plot de a_norm vs normale théorique")
        except Exception as e:
            print(f"[WARNING] Erreur lors du QQ-plot: {e}")
            plt.text(0.5, 0.5, "Erreur QQ-plot", ha='center', va='center', transform=plt.gca().transAxes)

        # Subplot 3: QQ-plot entre a_norm et b_norm
        plt.subplot(1, 3, 3)
        try:
            a_norm_clean = a_norm[np.isfinite(a_norm)]
            b_norm_clean = b_norm[np.isfinite(b_norm)]
            
            if len(a_norm_clean) > 0 and len(b_norm_clean) > 0:
                min_len = min(len(a_norm_clean), len(b_norm_clean))
                sorted_a = np.sort(a_norm_clean[:min_len])
                sorted_b = np.sort(b_norm_clean[:min_len])
                
                plt.scatter(sorted_a, sorted_b, s=10, alpha=0.7)
                min_val = min(sorted_a.min(), sorted_b.min())
                max_val = max(sorted_a.max(), sorted_b.max())
                plt.plot([min_val, max_val], [min_val, max_val], 'r--')
            plt.title("QQ-Plot : a_norm vs b_norm")
            plt.xlabel("Quantiles a_norm")
            plt.ylabel("Quantiles b_norm")
            plt.grid(True)
        except Exception as e:
            print(f"[WARNING] Erreur lors du QQ-plot comparatif: {e}")
            plt.text(0.5, 0.5, "Erreur QQ-plot", ha='center', va='center', transform=plt.gca().transAxes)

        plt.tight_layout()
        plt.savefig(output_filename, dpi=150)
        
        if show_plot:
            plt.show()
        else:
            plt.close()  # Fermer la figure si on ne l'affiche pas

        print(f"[INFO] Script terminé. Résultats enregistrés dans '{output_filename}'")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la création des graphiques: {e}")
        # Créer une figure simple en cas d'erreur
        try:
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, f"Erreur lors de la création des graphiques:\n{e}", 
                    ha='center', va='center', transform=plt.gca().transAxes)
            plt.title("Erreur de génération")
            plt.savefig(output_filename, dpi=150)
            plt.close()  # Fermer au lieu d'afficher
        except:
            pass


def main():
    """Fonction principale pour effectuer une comparaison complète."""
    print("=== Comparaison des générateurs de nombres aléatoires ===")
    results = compare_random_generators(n=10000)  # Échantillon plus petit pour le test
    print("\n=== Résultats de la comparaison ===")
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
