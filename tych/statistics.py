"""
Métriques avancées pour évaluer la qualité de l'aléatoire produit par Tych.
"""

from __future__ import annotations

import numpy as np
from typing import Any


# ---------------------------------------------------------------------------
# Autocorrélation
# ---------------------------------------------------------------------------

def _acf(x: np.ndarray, n_lags: int = 20) -> np.ndarray:
    """Calcule la fonction d'autocorrélation pour les lags 1..n_lags."""
    n = len(x)
    x = x - x.mean()
    var = np.dot(x, x) / n
    if var == 0:
        return np.zeros(n_lags)
    result = np.empty(n_lags)
    for k in range(1, n_lags + 1):
        result[k - 1] = np.dot(x[:n - k], x[k:]) / (n * var)
    return result


def _acf_score(acf_values: np.ndarray) -> float:
    """Score basé sur l'amplitude maximale de l'ACF (hors lag 0). Idéal : 0."""
    max_abs = float(np.max(np.abs(acf_values)))
    # Tolérance : ACF < 0.05 est excellent, > 0.3 est mauvais
    return float(max(0.0, 1.0 - max_abs / 0.3))


# ---------------------------------------------------------------------------
# Test de runs (Wald-Wolfowitz)
# ---------------------------------------------------------------------------

def _runs_test(x: np.ndarray) -> tuple[float, float]:
    """Retourne (z_stat, p_value) du test de runs au-dessus/en-dessous de la médiane."""
    try:
        from scipy.stats import norm as _norm
    except ImportError:
        return 0.0, 1.0

    med = np.median(x)
    above = (x > med).astype(int)

    runs = 1
    for i in range(1, len(above)):
        if above[i] != above[i - 1]:
            runs += 1

    n1 = int(np.sum(above))
    n2 = int(len(above) - n1)
    n = n1 + n2

    if n1 == 0 or n2 == 0:
        return 0.0, 1.0

    mu_r = (2 * n1 * n2) / n + 1
    sigma_r = np.sqrt((2 * n1 * n2 * (2 * n1 * n2 - n)) / (n * n * (n - 1)))

    if sigma_r == 0:
        return 0.0, 1.0

    z = (runs - mu_r) / sigma_r
    p = float(2 * _norm.sf(abs(z)))
    return float(z), p


# ---------------------------------------------------------------------------
# Entropie de Shannon
# ---------------------------------------------------------------------------

def _shannon_entropy_ratio(x: np.ndarray, n_bins: int = 20) -> float:
    """H / H_max — ratio d'entropie de Shannon. 1.0 = distribution parfaitement uniforme."""
    counts, _ = np.histogram(x, bins=n_bins, range=(0.0, 1.0))
    counts = counts[counts > 0]
    if len(counts) == 0:
        return 0.0
    p = counts / counts.sum()
    h = -float(np.sum(p * np.log2(p)))
    h_max = np.log2(n_bins)
    return min(1.0, h / h_max)


# ---------------------------------------------------------------------------
# Approximate Entropy (ApEn)
# ---------------------------------------------------------------------------

def _approximate_entropy(x: np.ndarray, m: int = 2, r_factor: float = 0.2) -> float:
    """ApEn(m, r) normalisé dans [0, 1]. Plus élevé = plus aléatoire."""
    n = len(x)
    if n < 10:
        return 0.0
    # Sous-échantillonnage pour les grandes séquences (calcul O(n²))
    if n > 500:
        rng = np.random.default_rng(seed=42)
        x = rng.choice(x, size=500, replace=False)
        n = 500
    r = r_factor * float(np.std(x))
    if r == 0:
        return 0.0

    def _phi(m_):
        templates = np.array([x[i:i + m_] for i in range(n - m_ + 1)])
        count = 0
        for i in range(len(templates)):
            diffs = np.max(np.abs(templates - templates[i]), axis=1)
            count += np.sum(diffs <= r)
        return np.log(count / len(templates) ** 2)

    try:
        apen = float(_phi(m) - _phi(m + 1))
        # Normalisation grossière : ApEn ∈ [0, ~2.2] pour des séries aléatoires
        return min(1.0, max(0.0, apen / 2.2))
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# Test χ²
# ---------------------------------------------------------------------------

def _chi2_uniformity(x: np.ndarray, n_bins: int = 20) -> tuple[float, float]:
    """χ² d'uniformité. Retourne (stat, p_value)."""
    try:
        from scipy.stats import chisquare as _chi2
    except ImportError:
        return 0.0, 1.0
    counts, _ = np.histogram(x, bins=n_bins, range=(0.0, 1.0))
    expected = np.full(n_bins, len(x) / n_bins)
    stat, p = _chi2(counts, f_exp=expected)
    return float(stat), float(p)


# ---------------------------------------------------------------------------
# Spectre de puissance (FFT)
# ---------------------------------------------------------------------------

def _power_spectrum_flatness(x: np.ndarray) -> float:
    """Score de platitude du spectre de puissance. 1.0 = bruit blanc parfait."""
    fft_vals = np.abs(np.fft.rfft(x - x.mean())) ** 2
    fft_vals = fft_vals[1:]  # exclure composante DC
    if len(fft_vals) == 0 or fft_vals.mean() == 0:
        return 0.0
    cv = float(np.std(fft_vals) / fft_vals.mean())
    # Un bruit blanc a CV ≈ 1. Trop grand = structure, trop petit improbable
    return float(max(0.0, 1.0 - abs(cv - 1.0) / 2.0))


# ---------------------------------------------------------------------------
# Exposant de Lyapunov
# ---------------------------------------------------------------------------

def compute_lyapunov(m1: float = 1.0, m2: float = 1.0,
                     l1: float = 1.0, l2: float = 1.0,
                     g: float = 9.81, damping: float = 0.999,
                     n_steps: int = 5000, epsilon: float = 1e-8) -> float:
    """
    Estime le plus grand exposant de Lyapunov (LEMax) du double pendule.

    λ > 0 confirme le chaos déterministe.
    Retourne λ en bits/step (log₂). -1 en cas d'erreur.
    """
    try:
        from tych.pendulum import PendulumParams, _step_state, _check_stability
    except ImportError:
        return -1.0

    p = PendulumParams(m1=m1, m2=m2, l1=l1, l2=l2, g=g, damping=damping)

    rng = np.random.default_rng(seed=0)
    s0 = [rng.uniform(-1.0, 1.0) for _ in range(4)]
    s1 = [s0[0] + epsilon, s0[1], s0[2], s0[3]]

    lyap_sum = 0.0
    valid_steps = 0

    for _ in range(n_steps):
        if not _check_stability(s0, p) or not _check_stability(s1, p):
            break
        s0 = _step_state(s0, p)
        s1 = _step_state(s1, p)

        dist = np.sqrt(sum((a - b) ** 2 for a, b in zip(s0, s1)))
        if dist < 1e-16 or not np.isfinite(dist):
            break

        lyap_sum += np.log2(dist / epsilon)
        valid_steps += 1

        # Renormalisation pour éviter l'overflow
        s1 = [s0[i] + (s1[i] - s0[i]) * epsilon / dist for i in range(4)]

    if valid_steps == 0:
        return -1.0
    return float(lyap_sum / valid_steps)


# ---------------------------------------------------------------------------
# Score global
# ---------------------------------------------------------------------------

def compute_quality_score(
    sequence: list[float] | np.ndarray,
    compute_apen: bool = True,
) -> dict[str, Any]:
    """
    Calcule un score de qualité enrichi pour une séquence pseudo-aléatoire.

    Retourne un dict avec :
    - "global" : score global [0, 100]
    - "uniformite", "independance", "entropie", "moments" : dict avec score + métriques brutes
    - "acf" : tableau des valeurs d'ACF (lags 1..20)
    - "spectrum" : tableau des puissances FFT normalisées
    """
    x = np.asarray(sequence, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)

    if n < 10:
        return {"global": 0, "error": "Séquence trop courte"}

    # ── Uniformité ──────────────────────────────────────────────────────────
    try:
        from scipy.stats import kstest as _kstest
        ks_stat, ks_p = _kstest(x, 'uniform')
    except Exception:
        ks_stat, ks_p = 0.5, 0.5

    chi2_stat, chi2_p = _chi2_uniformity(x)

    score_unif = float(np.sqrt(float(ks_p) * float(chi2_p)))  # moyenne géométrique
    counts_hist, bin_edges = np.histogram(x, bins=20, range=(0.0, 1.0))

    # ── Indépendance ────────────────────────────────────────────────────────
    acf_values = _acf(x, n_lags=20)
    acf_score  = _acf_score(acf_values)

    _, runs_p = _runs_test(x)
    score_indep = float(np.sqrt(acf_score * float(runs_p)))

    spectrum_raw = np.abs(np.fft.rfft(x - x.mean())) ** 2
    spectrum_raw = spectrum_raw[1:]
    spectrum_norm = (spectrum_raw / spectrum_raw.max()).tolist() if spectrum_raw.max() > 0 else []
    spectrum_score = _power_spectrum_flatness(x)

    # ── Entropie ────────────────────────────────────────────────────────────
    shannon = _shannon_entropy_ratio(x)
    apen = _approximate_entropy(x) if (compute_apen and n >= 50) else None

    if apen is not None:
        score_entropie = float(np.sqrt(shannon * apen)) if apen > 0 else shannon * 0.5
    else:
        score_entropie = shannon

    # ── Moments ─────────────────────────────────────────────────────────────
    _IDEAL_MEAN = 0.5
    _IDEAL_STD  = float(1.0 / np.sqrt(12))
    mean_val = float(x.mean())
    std_val  = float(x.std())

    score_mean = float(max(0.0, 1.0 - abs(mean_val - _IDEAL_MEAN) / 0.10))
    score_std  = float(max(0.0, 1.0 - abs(std_val  - _IDEAL_STD)  / 0.05))
    score_moments = float(np.sqrt(score_mean * score_std))

    # ── Score global ────────────────────────────────────────────────────────
    global_score = round((
        score_unif     * 0.30
        + score_indep  * 0.30
        + score_entropie * 0.25
        + score_moments  * 0.15
    ) * 100)

    bin_centers = ((bin_edges[:-1] + bin_edges[1:]) / 2).tolist()

    return {
        "global": global_score,
        "uniformite": {
            "score":      round(score_unif, 4),
            "ks_stat":    round(float(ks_stat), 4),
            "ks_p":       round(float(ks_p), 4),
            "chi2_stat":  round(float(chi2_stat), 4),
            "chi2_p":     round(float(chi2_p), 4),
        },
        "independance": {
            "score":         round(score_indep, 4),
            "acf_max":       round(float(np.max(np.abs(acf_values))), 4),
            "runs_p":        round(float(runs_p), 4),
            "spectrum_score": round(spectrum_score, 4),
        },
        "entropie": {
            "score":         round(score_entropie, 4),
            "shannon_ratio": round(float(shannon), 4),
            "apen":          round(float(apen), 4) if apen is not None else None,
        },
        "moments": {
            "score":      round(score_moments, 4),
            "mean":       round(mean_val, 6),
            "std":        round(std_val, 6),
            "mean_error": round(abs(mean_val - _IDEAL_MEAN), 6),
            "std_error":  round(abs(std_val - _IDEAL_STD), 6),
        },
        "acf":      [round(v, 4) for v in acf_values.tolist()],
        "spectrum": [round(v, 6) for v in spectrum_norm[:100]],  # max 100 points
        "histogram": {
            "bin_centers": [round(v, 3) for v in bin_centers],
            "counts":      counts_hist.tolist(),
        },
        "n": n,
    }
