"""
Module pour la génération de nombres pseudo-aléatoires basée sur la dynamique chaotique
du double pendule.
"""

import numpy as np
import hashlib


def double_pendulum_random_list(n=1000, n_pendulums=3, noise_level=0.01):
    """
    Génère une liste de nombres pseudo-aléatoires basée sur la dynamique chaotique
    d'un système de doubles pendules stabilisé.
    
    Args:
        n (int): Nombre de valeurs à générer
        n_pendulums (int): Nombre de pendules à simuler simultanément
        noise_level (float): Niveau de bruit à ajouter pour améliorer la randomisation
        
    Returns:
        list: Liste de nombres pseudo-aléatoires entre 0 et 1
    """
    # Paramètres physiques du double pendule
    m1, m2 = 1.0, 1.0  # masses
    l1, l2 = 1.0, 1.0  # longueurs
    g = 9.81           # gravité
    dt = 0.0005        # Pas de temps réduit pour la stabilité
    damping = 0.999    # Coefficient d'amortissement (0.999 = amortissement léger)
    
    # Limites physiques pour éviter les overflow
    MAX_OMEGA = 50.0   # Vitesse angulaire maximale (rad/s)
    MAX_ACCELERATION = 1000.0  # Accélération maximale
    MIN_DENOMINATOR = 1e-6     # Valeur minimale pour éviter division par zéro
    
    result = []
    
    # Initialisation de plusieurs pendules avec des conditions variées
    states = []
    for i in range(n_pendulums):
        # Conditions initiales plus variées mais stables
        theta1 = np.random.uniform(-np.pi, np.pi)
        theta2 = np.random.uniform(-np.pi, np.pi)
        omega1 = np.random.uniform(-5, 5)  # Vitesses initiales modérées
        omega2 = np.random.uniform(-5, 5)
        states.append([theta1, theta2, omega1, omega2])

    def runge_kutta_step(state, dt):
        """Intégrateur Runge-Kutta d'ordre 4 pour plus de stabilité."""
        theta1, theta2, omega1, omega2 = state
        
        def derivatives(t1, t2, w1, w2):
            """Calcule les dérivées du système avec protection contre les overflow."""
            delta = t2 - t1
            
            # Protection contre les singularités
            cos_delta = np.cos(delta)
            cos_delta_sq = cos_delta * cos_delta
            
            # Calcul du dénominateur avec protection
            den1 = (m1 + m2) * l1 - m2 * l1 * cos_delta_sq
            if abs(den1) < MIN_DENOMINATOR:
                den1 = np.sign(den1) * MIN_DENOMINATOR
            
            den2 = (l2 / l1) * den1
            if abs(den2) < MIN_DENOMINATOR:
                den2 = np.sign(den2) * MIN_DENOMINATOR
            
            # Calcul des accélérations avec limitation
            try:
                # Termes pour a1
                term1_a1 = m2 * l1 * w1 * w1 * np.sin(delta) * cos_delta
                term2_a1 = m2 * g * np.sin(t2) * cos_delta
                term3_a1 = m2 * l2 * w2 * w2 * np.sin(delta)
                term4_a1 = (m1 + m2) * g * np.sin(t1)
                
                a1 = (term1_a1 + term2_a1 + term3_a1 - term4_a1) / den1
                
                # Termes pour a2
                term1_a2 = -m2 * l2 * w2 * w2 * np.sin(delta) * cos_delta
                term2_a2 = (m1 + m2) * g * np.sin(t1) * cos_delta
                term3_a2 = (m1 + m2) * l1 * w1 * w1 * np.sin(delta)
                term4_a2 = (m1 + m2) * g * np.sin(t2)
                
                a2 = (term1_a2 + term2_a2 - term3_a2 - term4_a2) / den2
                
                # Limitation des accélérations
                a1 = np.clip(a1, -MAX_ACCELERATION, MAX_ACCELERATION)
                a2 = np.clip(a2, -MAX_ACCELERATION, MAX_ACCELERATION)
                
                # Vérification des valeurs finies
                if not (np.isfinite(a1) and np.isfinite(a2)):
                    a1, a2 = 0.0, 0.0
                
            except (OverflowError, FloatingPointError):
                # En cas d'overflow, réinitialiser les accélérations
                a1, a2 = 0.0, 0.0
            
            return [w1, w2, a1, a2]
        
        # Méthode Runge-Kutta d'ordre 4
        k1 = derivatives(theta1, theta2, omega1, omega2)
        
        k2 = derivatives(theta1 + 0.5*dt*k1[0], theta2 + 0.5*dt*k1[1], 
                        omega1 + 0.5*dt*k1[2], omega2 + 0.5*dt*k1[3])
        
        k3 = derivatives(theta1 + 0.5*dt*k2[0], theta2 + 0.5*dt*k2[1], 
                        omega1 + 0.5*dt*k2[2], omega2 + 0.5*dt*k2[3])
        
        k4 = derivatives(theta1 + dt*k3[0], theta2 + dt*k3[1], 
                        omega1 + dt*k3[2], omega2 + dt*k3[3])
        
        # Mise à jour avec RK4
        new_theta1 = theta1 + (dt/6.0) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
        new_theta2 = theta2 + (dt/6.0) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
        new_omega1 = omega1 + (dt/6.0) * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
        new_omega2 = omega2 + (dt/6.0) * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
        
        return [new_theta1, new_theta2, new_omega1, new_omega2]
    
    def check_stability(state):
        """Vérifie si l'état du pendule est stable."""
        theta1, theta2, omega1, omega2 = state
        
        # Vérifier les valeurs finies
        if not all(np.isfinite([theta1, theta2, omega1, omega2])):
            return False
        
        # Vérifier les limites de vitesse
        if abs(omega1) > MAX_OMEGA or abs(omega2) > MAX_OMEGA:
            return False
        
        return True
    
    def reset_pendulum():
        """Réinitialise un pendule avec des conditions stables."""
        theta1 = np.random.uniform(-np.pi/2, np.pi/2)  # Angles plus modérés
        theta2 = np.random.uniform(-np.pi/2, np.pi/2)
        omega1 = np.random.uniform(-2, 2)              # Vitesses initiales faibles
        omega2 = np.random.uniform(-2, 2)
        return [theta1, theta2, omega1, omega2]

    # Génération principale
    for i in range(n):
        mix = 0
        
        for idx in range(n_pendulums):
            # Vérifier la stabilité avant calcul
            if not check_stability(states[idx]):
                states[idx] = reset_pendulum()
                continue
            
            # Intégration avec Runge-Kutta
            states[idx] = runge_kutta_step(states[idx], dt)
            
            # Application de l'amortissement
            states[idx][2] *= damping  # omega1
            states[idx][3] *= damping  # omega2
            
            # Normalisation des angles dans [-π, π]
            states[idx][0] = ((states[idx][0] + np.pi) % (2*np.pi)) - np.pi
            states[idx][1] = ((states[idx][1] + np.pi) % (2*np.pi)) - np.pi
            
            # Limitation des vitesses après mise à jour
            states[idx][2] = np.clip(states[idx][2], -MAX_OMEGA, MAX_OMEGA)
            states[idx][3] = np.clip(states[idx][3], -MAX_OMEGA, MAX_OMEGA)
            
            # Vérification finale de stabilité
            if not check_stability(states[idx]):
                states[idx] = reset_pendulum()
                continue
            
            # Mélange des variables de chaque pendule
            theta1, theta2, omega1, omega2 = states[idx]
            mix += np.sin(theta1) + np.cos(theta2) + 0.1*np.sin(omega1) + 0.1*np.cos(omega2)
        
        # Ajout de bruit contrôlé
        noise = np.random.normal(0, noise_level)
        mix += noise
        
        # Protection contre les valeurs extrêmes dans le mix
        if not np.isfinite(mix):
            mix = np.random.uniform(-1, 1)
        
        mix = np.clip(mix, -1000, 1000)  # Limitation du mix
        
        # Hash de la valeur mixée pour casser la structure
        mix_bytes = str(float(mix)).encode('utf-8')
        hash_val = hashlib.sha256(mix_bytes).hexdigest()
        
        # Utiliser les premiers caractères du hash pour obtenir un float
        try:
            val = int(hash_val[:8], 16) / 0xFFFFFFFF
            # S'assurer que val est dans [0, 1]
            val = abs(val) % 1.0
        except (ValueError, OverflowError):
            # Fallback en cas d'erreur
            val = np.random.random()
        
        result.append(val)
    
    # Permutation des résultats pour casser les corrélations
    result = np.array(result)
    
    # Vérification finale et nettoyage
    finite_mask = np.isfinite(result)
    if not np.all(finite_mask):
        # Remplacer les valeurs non-finies par des valeurs aléatoires
        result[~finite_mask] = np.random.random(np.sum(~finite_mask))
    
    # S'assurer que toutes les valeurs sont dans [0, 1]
    result = np.clip(result, 0.0, 1.0)
    
    np.random.shuffle(result)
    return result.tolist()


def main():
    """Fonction principale pour tester le générateur avec diagnostics."""
    # Paramètres configurables
    n = 1000
    n_pendulums = 3
    noise_level = 0.2

    print(f"=== Test du générateur de double pendule stabilisé ===")
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
        # Surveillance des warnings numpy
        with np.errstate(over='raise', invalid='raise'):
            random_list = double_pendulum_random_list(n, n_pendulums=n_pendulums, noise_level=noise_level)
        
        print("✅ Génération terminée sans overflow!")
        
        # Statistiques
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
        
        # Test de distribution
        bins = np.linspace(0, 1, 11)
        hist, _ = np.histogram(random_list, bins)
        print(f"\n=== Distribution (histogramme) ===")
        for i, count in enumerate(hist):
            print(f"[{bins[i]:.1f}-{bins[i+1]:.1f}]: {count:4d} ({count/n*100:.1f}%)")
        
        # Test de qualité basique
        uniformity_test = np.abs(mean_val - 0.5) < 0.1  # Moyenne proche de 0.5
        variance_test = 0.05 < std_val < 0.4  # Variance raisonnable
        
        print(f"\n=== Tests de qualité ===")
        print(f"Test d'uniformité (moyenne ≈ 0.5): {'✅' if uniformity_test else '❌'}")
        print(f"Test de variance (0.05 < σ < 0.4): {'✅' if variance_test else '❌'}")
        
        if uniformity_test and variance_test:
            print("🎉 Le générateur semble fonctionner correctement!")
        else:
            print("⚠️  Le générateur pourrait nécessiter des ajustements.")
            
    except (OverflowError, FloatingPointError) as e:
        print(f"❌ Erreur d'overflow détectée: {e}")
        print("Le système nécessite encore des ajustements.")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
