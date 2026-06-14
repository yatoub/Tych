"""
Module pour la comparaison et l'analyse statistique de générateurs de nombres aléatoires.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, kstest, probplot
import os
from .pendulum import double_pendulum_random_list


def compute_comparison(n=100000, n_pendulums=3, noise_level=0.2,
                       m1=1.0, m2=1.0, l1=1.0, l2=1.0, g=9.81, damping=0.999):
    """
    Effectue la génération, normalisation et test KS, et retourne les données brutes
    nécessaires à la fois pour le rendu matplotlib et pour les charts JS.

    Args:
        n (int): Taille des échantillons
        n_pendulums (int): Nombre de pendules
        noise_level (float): Niveau de bruit

    Returns:
        dict: Statistiques KS, moyennes/écarts-types, et séries pour visualisation :
              histogram_a, histogram_b, kde_a, kde_b (x/y grids),
              qq_a (quantiles vs normale), qq_ab (quantiles a vs b).
    """
    print("[INFO] Génération des données...")

    print(f" - Génération de 'a' avec le double pendule chaotique (n_pendulums={n_pendulums}, noise_level={noise_level})")
    a = np.array(double_pendulum_random_list(n, n_pendulums=n_pendulums, noise_level=noise_level,
                                              m1=m1, m2=m2, l1=l1, l2=l2, g=g, damping=damping))
    print(f"   Taille: {len(a)}, Moyenne: {a.mean():.4f}, Écart-type: {a.std():.4f}")

    print(" - Lecture de 'b' depuis /dev/urandom")
    try:
        urandom_bytes = os.urandom(n * 8)
        if len(urandom_bytes) < n * 8:
            raise ValueError("Pas assez de données urandom disponibles")
        raw_bytes = np.frombuffer(urandom_bytes, dtype=np.uint64)
        b = raw_bytes.astype(np.float64) / (2 ** 64 - 1)
        if len(b) == 0 or np.any(np.isnan(b)) or np.any(np.isinf(b)):
            raise ValueError("Données urandom invalides")
        print(f"   Taille: {len(b)}, Min: {b.min():.6f}, Max: {b.max():.6f}")
    except Exception as e:
        print(f"   Erreur: {e} — fallback numpy.random")
        np.random.seed(42)
        b = np.random.random(n)

    print("[INFO] Normalisation des données...")
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]

    if len(a) == 0 or len(b) == 0:
        raise ValueError("Aucune donnée valide après nettoyage")

    a_mean, a_std = np.mean(a), np.std(a)
    b_mean, b_std = np.mean(b), np.std(b)
    if a_std == 0:
        a_std = 1e-10
    if b_std == 0:
        b_std = 1e-10

    a_norm = (a - a_mean) / a_std
    b_norm = (b - b_mean) / b_std

    print("[INFO] Test Kolmogorov–Smirnov...")
    try:
        if len(a_norm) != len(b_norm):
            min_len = min(len(a_norm), len(b_norm))
            a_norm = a_norm[:min_len]
            b_norm = b_norm[:min_len]

        ks_stat, ks_p = kstest(
            a_norm,
            lambda x: np.interp(x, np.sort(b_norm), np.linspace(0, 1, len(b_norm)))
        )
        if np.isnan(ks_stat) or np.isnan(ks_p):
            ks_stat, ks_p = 0.5, 0.5
        print(f"   KS-statistic = {ks_stat:.4f}, p-value = {ks_p:.4f}")
    except Exception as e:
        print(f"   Erreur KS: {e} — valeurs par défaut")
        ks_stat, ks_p = 0.5, 0.5

    # --- Séries pour charts JS ---

    # Histogrammes (30 bins sur [0,1] pour les données brutes)
    bins = np.linspace(0, 1, 31)
    counts_a, bin_edges_a = np.histogram(np.clip(a, 0, 1), bins=bins, density=True)
    counts_b, bin_edges_b = np.histogram(np.clip(b, 0, 1), bins=bins, density=True)
    bin_centers = ((bin_edges_a[:-1] + bin_edges_a[1:]) / 2).tolist()

    # KDE sur [0,1]
    x_grid = np.linspace(0, 1, 200)
    try:
        kde_a_y = gaussian_kde(np.clip(a, 0, 1))(x_grid).tolist()
    except Exception:
        kde_a_y = [0.0] * 200
    try:
        kde_b_y = gaussian_kde(np.clip(b, 0, 1))(x_grid).tolist()
    except Exception:
        kde_b_y = [0.0] * 200

    # QQ-plot de a_norm vs normale théorique
    try:
        (osm, osr), _ = probplot(a_norm[np.isfinite(a_norm)], dist="norm")
        qq_a = {"theoretical": osm.tolist(), "sample": osr.tolist()}
    except Exception:
        qq_a = {"theoretical": [], "sample": []}

    # QQ-plot a_norm vs b_norm
    try:
        a_nc = np.sort(a_norm[np.isfinite(a_norm)])
        b_nc = np.sort(b_norm[np.isfinite(b_norm)])
        min_len = min(len(a_nc), len(b_nc))
        qq_ab = {"a": a_nc[:min_len].tolist(), "b": b_nc[:min_len].tolist()}
    except Exception:
        qq_ab = {"a": [], "b": []}

    return {
        # Stats KS
        "ks_statistic": float(ks_stat),
        "ks_p_value": float(ks_p),
        # Stats descriptives
        "pendulum_mean": float(a.mean()),
        "pendulum_std": float(a.std()),
        "urandom_mean": float(b.mean()),
        "urandom_std": float(b.std()),
        "pendulum_normalized_mean": float(a_norm.mean()),
        "pendulum_normalized_std": float(a_norm.std()),
        "urandom_normalized_mean": float(b_norm.mean()),
        "urandom_normalized_std": float(b_norm.std()),
        # Séries pour charts JS
        "histogram": {
            "bin_centers": bin_centers,
            "pendulum": counts_a.tolist(),
            "urandom": counts_b.tolist(),
        },
        "kde": {
            "x": x_grid.tolist(),
            "pendulum": kde_a_y,
            "urandom": kde_b_y,
        },
        "qq_normal": qq_a,
        "qq_compare": qq_ab,
        # Données brutes pour matplotlib (passées en interne)
        "_a": a,
        "_b": b,
        "_a_norm": a_norm,
        "_b_norm": b_norm,
    }


def compare_random_generators(n=100000, n_pendulums=3, noise_level=0.2,
                               urandom_file="/dev/urandom", save_plot=True,
                               output_filename="comparison.png", show_plot=False):
    """
    Compare les générateurs de nombres aléatoires : double pendule vs /dev/urandom.

    Args:
        n (int): Taille des échantillons à générer
        n_pendulums (int): Nombre de pendules pour le générateur chaotique
        noise_level (float): Niveau de bruit pour le générateur chaotique
        urandom_file (str): Non utilisé (conservé pour compatibilité)
        save_plot (bool): Sauvegarder le graphique ou non
        output_filename (str): Nom du fichier de sortie pour le graphique
        show_plot (bool): Afficher le graphique ou non (défaut: False)

    Returns:
        dict: Résultats de la comparaison (statistiques KS, moyennes, etc.)
    """
    data = compute_comparison(n=n, n_pendulums=n_pendulums, noise_level=noise_level)

    a = data.pop("_a")
    b = data.pop("_b")
    a_norm = data.pop("_a_norm")
    b_norm = data.pop("_b_norm")

    if save_plot:
        _create_comparison_plots(a, b, a_norm, b_norm, output_filename, show_plot)

    # Retourner uniquement les clés historiquement présentes pour la compatibilité
    return {k: v for k, v in data.items() if not k.startswith("_") and k not in (
        "histogram", "kde", "qq_normal", "qq_compare"
    )}


def _create_comparison_plots(a, b, a_norm, b_norm, output_filename, show_plot=False):
    """Créé les graphiques de comparaison."""
    try:
        if len(a) == 0 or len(b) == 0:
            print("[WARNING] Pas de données pour créer les graphiques")
            return

        print("[INFO] Création du graphique Histogramme + KDE...")

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
        fig = plt.figure(figsize=(15, 5))

        plt.subplot(1, 3, 1)
        try:
            plt.hist(a_clean, bins=30, alpha=0.5, label="a (Double pendule)", density=True, color="blue")
            plt.hist(b_clean, bins=30, alpha=0.5, label="b (/dev/urandom normalisé)", density=True, color="orange")
            if len(a_clean) > 1:
                kde_a = gaussian_kde(a_clean)
                plt.plot(x_grid, kde_a(x_grid), color="blue", lw=2)
            if len(b_clean) > 1:
                kde_b = gaussian_kde(b_clean)
                plt.plot(x_grid, kde_b(x_grid), color="orange", lw=2)
        except Exception as e:
            print(f"[WARNING] Erreur histogramme: {e}")

        plt.title("Histogramme + KDE")
        plt.xlabel("Valeurs")
        plt.ylabel("Densité")
        plt.legend()
        plt.grid(True)

        plt.subplot(1, 3, 2)
        try:
            if len(a_norm) > 1:
                probplot(a_norm[np.isfinite(a_norm)], dist="norm", plot=plt)
            plt.title("QQ-Plot de a_norm vs normale théorique")
        except Exception as e:
            print(f"[WARNING] Erreur QQ-plot: {e}")
            plt.text(0.5, 0.5, "Erreur QQ-plot", ha="center", va="center", transform=plt.gca().transAxes)

        plt.subplot(1, 3, 3)
        try:
            a_norm_clean = a_norm[np.isfinite(a_norm)]
            b_norm_clean = b_norm[np.isfinite(b_norm)]
            if len(a_norm_clean) > 0 and len(b_norm_clean) > 0:
                min_len = min(len(a_norm_clean), len(b_norm_clean))
                sorted_a = np.sort(a_norm_clean[:min_len])
                sorted_b = np.sort(b_norm_clean[:min_len])
                plt.scatter(sorted_a, sorted_b, s=10, alpha=0.7)
                min_v = min(sorted_a.min(), sorted_b.min())
                max_v = max(sorted_a.max(), sorted_b.max())
                plt.plot([min_v, max_v], [min_v, max_v], "r--")
            plt.title("QQ-Plot : a_norm vs b_norm")
            plt.xlabel("Quantiles a_norm")
            plt.ylabel("Quantiles b_norm")
            plt.grid(True)
        except Exception as e:
            print(f"[WARNING] Erreur QQ-plot comparatif: {e}")
            plt.text(0.5, 0.5, "Erreur QQ-plot", ha="center", va="center", transform=plt.gca().transAxes)

        plt.tight_layout()
        plt.savefig(output_filename, dpi=150)

        if show_plot:
            plt.show()
        else:
            plt.close()

        print(f"[INFO] Résultats enregistrés dans '{output_filename}'")

    except Exception as e:
        print(f"[ERROR] Erreur lors de la création des graphiques: {e}")
        try:
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, f"Erreur:\n{e}", ha="center", va="center", transform=plt.gca().transAxes)
            plt.title("Erreur de génération")
            plt.savefig(output_filename, dpi=150)
            plt.close()
        except Exception:
            pass


def main():
    """Fonction principale pour effectuer une comparaison complète."""
    print("=== Comparaison des générateurs de nombres aléatoires ===")
    results = compare_random_generators(n=10000)
    print("\n=== Résultats de la comparaison ===")
    for key, value in results.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
