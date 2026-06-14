"""
Module pour la génération de nombres pseudo-aléatoires basée sur la dynamique chaotique
du double pendule.
"""

import numpy as np
import hashlib
from dataclasses import dataclass, field


@dataclass
class PendulumParams:
    m1: float = 1.0
    m2: float = 1.0
    l1: float = 1.0
    l2: float = 1.0
    g: float = 9.81
    dt: float = 0.0005
    damping: float = 0.999
    max_omega: float = 50.0
    max_acceleration: float = 1000.0
    min_denominator: float = 1e-6


def _derivatives(t1, t2, w1, w2, p: PendulumParams):
    """Calcule les dérivées du système avec protection contre les overflow."""
    delta = t2 - t1
    cos_delta = np.cos(delta)
    cos_delta_sq = cos_delta * cos_delta

    den1 = (p.m1 + p.m2) * p.l1 - p.m2 * p.l1 * cos_delta_sq
    if abs(den1) < p.min_denominator:
        den1 = np.sign(den1) * p.min_denominator

    den2 = (p.l2 / p.l1) * den1
    if abs(den2) < p.min_denominator:
        den2 = np.sign(den2) * p.min_denominator

    try:
        term1_a1 = p.m2 * p.l1 * w1 * w1 * np.sin(delta) * cos_delta
        term2_a1 = p.m2 * p.g * np.sin(t2) * cos_delta
        term3_a1 = p.m2 * p.l2 * w2 * w2 * np.sin(delta)
        term4_a1 = (p.m1 + p.m2) * p.g * np.sin(t1)
        a1 = (term1_a1 + term2_a1 + term3_a1 - term4_a1) / den1

        term1_a2 = -p.m2 * p.l2 * w2 * w2 * np.sin(delta) * cos_delta
        term2_a2 = (p.m1 + p.m2) * p.g * np.sin(t1) * cos_delta
        term3_a2 = (p.m1 + p.m2) * p.l1 * w1 * w1 * np.sin(delta)
        term4_a2 = (p.m1 + p.m2) * p.g * np.sin(t2)
        a2 = (term1_a2 + term2_a2 - term3_a2 - term4_a2) / den2

        a1 = np.clip(a1, -p.max_acceleration, p.max_acceleration)
        a2 = np.clip(a2, -p.max_acceleration, p.max_acceleration)

        if not (np.isfinite(a1) and np.isfinite(a2)):
            a1, a2 = 0.0, 0.0

    except (OverflowError, FloatingPointError):
        a1, a2 = 0.0, 0.0

    return [w1, w2, a1, a2]


def _runge_kutta_step(state, p: PendulumParams):
    """Intégrateur Runge-Kutta d'ordre 4."""
    theta1, theta2, omega1, omega2 = state
    dt = p.dt

    k1 = _derivatives(theta1, theta2, omega1, omega2, p)
    k2 = _derivatives(
        theta1 + 0.5 * dt * k1[0], theta2 + 0.5 * dt * k1[1],
        omega1 + 0.5 * dt * k1[2], omega2 + 0.5 * dt * k1[3], p
    )
    k3 = _derivatives(
        theta1 + 0.5 * dt * k2[0], theta2 + 0.5 * dt * k2[1],
        omega1 + 0.5 * dt * k2[2], omega2 + 0.5 * dt * k2[3], p
    )
    k4 = _derivatives(
        theta1 + dt * k3[0], theta2 + dt * k3[1],
        omega1 + dt * k3[2], omega2 + dt * k3[3], p
    )

    return [
        theta1 + (dt / 6.0) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]),
        theta2 + (dt / 6.0) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]),
        omega1 + (dt / 6.0) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]),
        omega2 + (dt / 6.0) * (k1[3] + 2 * k2[3] + 2 * k3[3] + k4[3]),
    ]


def _check_stability(state, p: PendulumParams):
    """Vérifie si l'état du pendule est stable."""
    theta1, theta2, omega1, omega2 = state
    if not all(np.isfinite([theta1, theta2, omega1, omega2])):
        return False
    if abs(omega1) > p.max_omega or abs(omega2) > p.max_omega:
        return False
    return True


def _reset_pendulum():
    """Réinitialise un pendule avec des conditions stables."""
    return [
        np.random.uniform(-np.pi / 2, np.pi / 2),
        np.random.uniform(-np.pi / 2, np.pi / 2),
        np.random.uniform(-2, 2),
        np.random.uniform(-2, 2),
    ]


def _step_state(state, p: PendulumParams):
    """Avance l'état d'un pas RK4 avec amortissement et normalisation."""
    state = _runge_kutta_step(state, p)
    state[2] *= p.damping
    state[3] *= p.damping
    state[0] = ((state[0] + np.pi) % (2 * np.pi)) - np.pi
    state[1] = ((state[1] + np.pi) % (2 * np.pi)) - np.pi
    state[2] = np.clip(state[2], -p.max_omega, p.max_omega)
    state[3] = np.clip(state[3], -p.max_omega, p.max_omega)
    return state


def double_pendulum_random_list(n=1000, n_pendulums=3, noise_level=0.01,
                                m1=1.0, m2=1.0, l1=1.0, l2=1.0,
                                g=9.81, damping=0.999):
    """
    Génère une liste de nombres pseudo-aléatoires basée sur la dynamique chaotique
    d'un système de doubles pendules stabilisé.

    Args:
        n (int): Nombre de valeurs à générer
        n_pendulums (int): Nombre de pendules à simuler simultanément
        noise_level (float): Niveau de bruit à ajouter pour améliorer la randomisation
        m1, m2 (float): Masses des deux bobs (kg)
        l1, l2 (float): Longueurs des tiges (m)
        g (float): Accélération gravitationnelle (m/s²)
        damping (float): Coefficient d'amortissement (0.990–1.000)

    Returns:
        list: Liste de nombres pseudo-aléatoires entre 0 et 1
    """
    p = PendulumParams(m1=m1, m2=m2, l1=l1, l2=l2, g=g, damping=damping)
    result = []

    states = []
    for _ in range(n_pendulums):
        theta1 = np.random.uniform(-np.pi, np.pi)
        theta2 = np.random.uniform(-np.pi, np.pi)
        omega1 = np.random.uniform(-5, 5)
        omega2 = np.random.uniform(-5, 5)
        states.append([theta1, theta2, omega1, omega2])

    for _ in range(n):
        mix = 0

        for idx in range(n_pendulums):
            if not _check_stability(states[idx], p):
                states[idx] = _reset_pendulum()
                continue

            states[idx] = _step_state(states[idx], p)

            if not _check_stability(states[idx], p):
                states[idx] = _reset_pendulum()
                continue

            t1, t2, w1, w2 = states[idx]
            mix += np.sin(t1) + np.cos(t2) + 0.1 * np.sin(w1) + 0.1 * np.cos(w2)

        noise = np.random.normal(0, noise_level)
        mix += noise

        if not np.isfinite(mix):
            mix = np.random.uniform(-1, 1)

        mix = np.clip(mix, -1000, 1000)

        mix_bytes = str(float(mix)).encode("utf-8")
        hash_val = hashlib.sha256(mix_bytes).hexdigest()

        try:
            val = int(hash_val[:8], 16) / 0xFFFFFFFF
            val = abs(val) % 1.0
        except (ValueError, OverflowError):
            val = np.random.random()

        result.append(val)

    result = np.array(result)
    finite_mask = np.isfinite(result)
    if not np.all(finite_mask):
        result[~finite_mask] = np.random.random(np.sum(~finite_mask))

    result = np.clip(result, 0.0, 1.0)
    np.random.shuffle(result)
    return result.tolist()


def simulate_trajectory(steps=2000, n_pendulums=1, seed=None,
                        m1=1.0, m2=1.0, l1=1.0, l2=1.0,
                        g=9.81, damping=0.999):
    """
    Simule les trajectoires du double pendule pour visualisation.

    Utilise le même intégrateur RK4 que le générateur, avec un sous-échantillonnage
    pour garder le payload raisonnable (toutes les 5 étapes).

    Args:
        steps (int): Nombre de pas à enregistrer (après sous-échantillonnage)
        n_pendulums (int): Nombre de pendules à simuler
        seed (int | None): Graine aléatoire pour la reproductibilité
        m1, m2 (float): Masses des deux bobs (kg)
        l1, l2 (float): Longueurs des tiges (m)
        g (float): Accélération gravitationnelle (m/s²)
        damping (float): Coefficient d'amortissement

    Returns:
        dict: {
            "dt": float (pas de temps effectif entre frames),
            "params": {l1, l2, m1, m2},
            "pendulums": list[list[[theta1, theta2]]]  # shape (n_pendulums, steps)
        }
    """
    if seed is not None:
        np.random.seed(seed)

    p = PendulumParams(m1=m1, m2=m2, l1=l1, l2=l2, g=g, damping=damping)
    subsample = 5
    total_inner = steps * subsample

    states = []
    for _ in range(n_pendulums):
        states.append([
            np.random.uniform(-np.pi, np.pi),
            np.random.uniform(-np.pi, np.pi),
            np.random.uniform(-3, 3),
            np.random.uniform(-3, 3),
        ])

    trajectories = [[[] for _ in range(n_pendulums)] for _ in range(total_inner)]
    recorded = [[] for _ in range(n_pendulums)]

    for step in range(total_inner):
        for idx in range(n_pendulums):
            if not _check_stability(states[idx], p):
                states[idx] = _reset_pendulum()
            else:
                states[idx] = _step_state(states[idx], p)
                if not _check_stability(states[idx], p):
                    states[idx] = _reset_pendulum()

            if step % subsample == 0:
                recorded[idx].append([states[idx][0], states[idx][1]])

    return {
        "dt": p.dt * subsample,
        "params": {"l1": p.l1, "l2": p.l2, "m1": p.m1, "m2": p.m2},
        "pendulums": recorded,
    }


def main():
    """Fonction principale pour tester le générateur avec diagnostics."""
    n = 1000
    n_pendulums = 3
    noise_level = 0.2

    print("=== Test du générateur de double pendule stabilisé ===")
    print(f"Paramètres:")
    print(f"  - Nombre de valeurs: {n}")
    print(f"  - Nombre de pendules: {n_pendulums}")
    print(f"  - Niveau de bruit: {noise_level}")
    print(f"  - Pas de temps: 0.0005")
    print(f"  - Amortissement: 0.999")
    print(f"  - Intégrateur: Runge-Kutta 4")
    print()

    print("Génération en cours...")
    try:
        with np.errstate(over="raise", invalid="raise"):
            random_list = double_pendulum_random_list(n, n_pendulums=n_pendulums, noise_level=noise_level)

        print("✅ Génération terminée sans overflow!")

        mean_val = np.mean(random_list)
        std_val = np.std(random_list)
        min_val = np.min(random_list)
        max_val = np.max(random_list)

        print(f"\n=== Statistiques ===")
        print(f"Premier échantillon (10 valeurs): {random_list[:10]}")
        print(f"Moyenne: {mean_val:.6f}")
        print(f"Écart-type: {std_val:.6f}")
        print(f"Min: {min_val:.6f}")
        print(f"Max: {max_val:.6f}")
        print(f"Toutes les valeurs dans [0,1]: {np.all((np.array(random_list) >= 0) & (np.array(random_list) <= 1))}")
        print(f"Valeurs finies: {np.all(np.isfinite(random_list))}")

        bins = np.linspace(0, 1, 11)
        hist, _ = np.histogram(random_list, bins)
        print(f"\n=== Distribution (histogramme) ===")
        for i, count in enumerate(hist):
            print(f"[{bins[i]:.1f}-{bins[i+1]:.1f}]: {count:4d} ({count/n*100:.1f}%)")

        uniformity_test = np.abs(mean_val - 0.5) < 0.1
        variance_test = 0.05 < std_val < 0.4

        print(f"\n=== Tests de qualité ===")
        print(f"Test d'uniformité (moyenne ≈ 0.5): {'✅' if uniformity_test else '❌'}")
        print(f"Test de variance (0.05 < σ < 0.4): {'✅' if variance_test else '❌'}")

        if uniformity_test and variance_test:
            print("🎉 Le générateur semble fonctionner correctement!")
        else:
            print("⚠️  Le générateur pourrait nécessiter des ajustements.")

    except (OverflowError, FloatingPointError) as e:
        print(f"❌ Erreur d'overflow détectée: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
