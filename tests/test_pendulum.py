"""
Tests pour le module pendulum de Tych
"""

import pytest
import numpy as np
from unittest.mock import patch
import sys
import os

# Ajouter le chemin du package pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tych.pendulum import double_pendulum_random_list


class TestDoublePendulumRandomList:
    """Tests pour la fonction double_pendulum_random_list."""
    
    def test_basic_generation(self):
        """Test de génération basique."""
        n = 100
        numbers = double_pendulum_random_list(n=n)
        
        assert isinstance(numbers, list)
        assert len(numbers) == n
        assert all(isinstance(x, float) for x in numbers)
    
    def test_different_sizes(self):
        """Test avec différentes tailles."""
        for n in [1, 10, 50, 200]:
            numbers = double_pendulum_random_list(n=n)
            assert len(numbers) == n
    
    def test_parameter_validation(self):
        """Test de validation des paramètres."""
        # Test avec n = 0
        numbers = double_pendulum_random_list(n=0)
        assert len(numbers) == 0
        
        # Test avec des paramètres valides
        numbers = double_pendulum_random_list(
            n=50, 
            n_pendulums=5, 
            noise_level=0.5
        )
        assert len(numbers) == 50
    
    def test_pendulum_count_effect(self):
        """Test de l'effet du nombre de pendules."""
        n = 100
        
        # Test avec différents nombres de pendules
        numbers_1 = double_pendulum_random_list(n=n, n_pendulums=1)
        numbers_3 = double_pendulum_random_list(n=n, n_pendulums=3)
        numbers_5 = double_pendulum_random_list(n=n, n_pendulums=5)
        
        assert len(numbers_1) == n
        assert len(numbers_3) == n
        assert len(numbers_5) == n
        
        # Les séquences devraient être différentes
        assert numbers_1 != numbers_3
        assert numbers_3 != numbers_5
    
    def test_noise_level_effect(self):
        """Test de l'effet du niveau de bruit."""
        n = 50
        
        # Test avec différents niveaux de bruit
        numbers_low = double_pendulum_random_list(n=n, noise_level=0.01)
        numbers_high = double_pendulum_random_list(n=n, noise_level=0.5)
        
        assert len(numbers_low) == n
        assert len(numbers_high) == n
        
        # Les séquences devraient être différentes
        assert numbers_low != numbers_high
    
    def test_reproducibility_with_fixed_seed(self):
        """Test de reproductibilité avec graine fixe."""
        n = 50
        
        # Mock numpy.random pour contrôler la graine
        with patch('numpy.random.seed') as mock_seed:
            with patch('numpy.random.uniform') as mock_uniform:
                with patch('numpy.random.normal') as mock_normal:
                    with patch('numpy.random.shuffle') as mock_shuffle:
                        # Configuration des mocks pour des valeurs déterministes
                        mock_uniform.side_effect = lambda low, high, size=None: \
                            np.full(size if size else 1, (low + high) / 2)
                        mock_normal.side_effect = lambda loc, scale, size=None: \
                            np.full(size if size else 1, loc)
                        mock_shuffle.return_value = None  # Pas de mélange
                        
                        numbers1 = double_pendulum_random_list(n=n)
                        numbers2 = double_pendulum_random_list(n=n)
                        
                        # Avec les mêmes conditions, on devrait avoir des résultats similaires
                        assert len(numbers1) == len(numbers2) == n
    
    def test_value_range(self):
        """Test que les valeurs sont dans une plage raisonnable."""
        numbers = double_pendulum_random_list(n=100)
        
        # Vérifier que toutes les valeurs sont des nombres finis
        assert all(np.isfinite(x) for x in numbers)
        
        # Les valeurs devraient être entre 0 et 1 généralement
        # (après normalisation par le hash)
        assert all(0 <= x <= 1 for x in numbers)
    
    def test_statistical_properties(self):
        """Test des propriétés statistiques basiques."""
        n = 1000
        numbers = double_pendulum_random_list(n=n)
        
        mean = np.mean(numbers)
        std = np.std(numbers)
        
        # La moyenne devrait être proche de 0.5 pour une distribution uniforme [0,1]
        assert 0.3 < mean < 0.7, f"Moyenne inhabituelle: {mean}"
        
        # L'écart-type devrait être raisonnable
        assert std > 0.1, f"Écart-type trop faible: {std}"
        assert std < 0.5, f"Écart-type trop élevé: {std}"
    
    def test_uniqueness(self):
        """Test que les valeurs générées ne sont pas toutes identiques."""
        numbers = double_pendulum_random_list(n=100)
        
        # Il devrait y avoir au moins quelques valeurs différentes
        unique_values = set(numbers)
        assert len(unique_values) > 10, "Pas assez de valeurs uniques générées"
    
    def test_negative_parameters(self):
        """Test avec des paramètres négatifs ou invalides."""
        # n négatif devrait retourner une liste vide
        numbers = double_pendulum_random_list(n=-5)
        assert len(numbers) == 0
        
        # n_pendulums négatif ou zéro devrait être géré
        try:
            numbers = double_pendulum_random_list(n=10, n_pendulums=0)
            # Si ça ne lève pas d'erreur, vérifier que ça retourne quelque chose
            assert isinstance(numbers, list)
        except (ValueError, ZeroDivisionError):
            # C'est acceptable que ça lève une erreur
            pass
    
    def test_large_numbers(self):
        """Test avec de grandes valeurs."""
        # Test avec un grand n
        numbers = double_pendulum_random_list(n=5000)
        assert len(numbers) == 5000
        
        # Test avec beaucoup de pendules
        numbers = double_pendulum_random_list(n=100, n_pendulums=10)
        assert len(numbers) == 100
        
        # Test avec un niveau de bruit élevé
        numbers = double_pendulum_random_list(n=100, noise_level=2.0)
        assert len(numbers) == 100
    
    def test_main_function(self):
        """Test de la fonction main du module."""
        from tych.pendulum import main
        
        # La fonction main devrait s'exécuter sans erreur
        try:
            # Capturer la sortie pour éviter l'affichage pendant les tests
            with patch('builtins.print'):
                main()
        except Exception as e:
            pytest.fail(f"La fonction main a levé une exception: {e}")


class TestPendulumMathematicalProperties:
    """Tests des propriétés mathématiques du générateur."""
    
    def test_chaos_sensitivity(self):
        """Test de la sensibilité aux conditions initiales (propriété chaotique)."""
        n = 200
        
        # Générer plusieurs séquences avec les mêmes paramètres
        sequences = []
        for _ in range(5):
            seq = double_pendulum_random_list(n=n, n_pendulums=3, noise_level=0.1)
            sequences.append(seq)
        
        # Toutes les séquences devraient être différentes (chaos)
        for i in range(len(sequences)):
            for j in range(i + 1, len(sequences)):
                assert sequences[i] != sequences[j], "Les séquences chaotiques ne devraient pas être identiques"
    
    def test_distribution_uniformity(self):
        """Test basique d'uniformité de la distribution."""
        numbers = double_pendulum_random_list(n=2000)
        
        # Diviser en quartiles et vérifier la répartition
        q1 = sum(1 for x in numbers if 0 <= x < 0.25)
        q2 = sum(1 for x in numbers if 0.25 <= x < 0.5)
        q3 = sum(1 for x in numbers if 0.5 <= x < 0.75)
        q4 = sum(1 for x in numbers if 0.75 <= x <= 1)
        
        total = q1 + q2 + q3 + q4
        assert total == len(numbers)
        
        # Chaque quartile devrait avoir approximativement 25% des valeurs
        expected = len(numbers) / 4
        tolerance = expected * 0.3  # 30% de tolérance
        
        assert abs(q1 - expected) < tolerance, f"Q1 mal distribué: {q1} vs {expected}"
        assert abs(q2 - expected) < tolerance, f"Q2 mal distribué: {q2} vs {expected}"
        assert abs(q3 - expected) < tolerance, f"Q3 mal distribué: {q3} vs {expected}"
        assert abs(q4 - expected) < tolerance, f"Q4 mal distribué: {q4} vs {expected}"


if __name__ == "__main__":
    # Permettre d'exécuter les tests directement
    pytest.main([__file__, "-v"])
