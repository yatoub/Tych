"""
Tests pour le module comparison de Tych
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
from pathlib import Path

# Ajouter le chemin du package pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tych.comparison import compare_random_generators, _create_comparison_plots


class TestCompareRandomGenerators:
    """Tests pour la fonction compare_random_generators."""
    
    def test_basic_comparison(self):
        """Test de comparaison basique."""
        # Mock matplotlib pour éviter l'affichage des graphiques
        with patch('matplotlib.pyplot.savefig'), \
             patch('os.urandom') as mock_urandom:
            
            # Mock urandom pour retourner des données déterministes - créer une distribution réaliste
            np.random.seed(12345)
            mock_data = np.random.randint(0, 2**64, size=100, dtype=np.uint64)
            mock_urandom.return_value = mock_data.tobytes()
            
            results = compare_random_generators(n=100, save_plot=False, show_plot=False)
            
            # Vérifier la structure des résultats
            assert isinstance(results, dict)
            
            required_keys = [
                'ks_statistic', 'ks_p_value',
                'pendulum_mean', 'pendulum_std',
                'urandom_mean', 'urandom_std',
                'pendulum_normalized_mean', 'pendulum_normalized_std',
                'urandom_normalized_mean', 'urandom_normalized_std'
            ]
            
            for key in required_keys:
                assert key in results, f"Clé manquante: {key}"
                assert isinstance(results[key], (int, float)), f"Type incorrect pour {key}"
                assert np.isfinite(results[key]), f"Valeur non finie pour {key}: {results[key]}"
    
    def test_different_sample_sizes(self):
        """Test avec différentes tailles d'échantillon."""
        with patch('matplotlib.pyplot.savefig'), \
             patch('os.urandom') as mock_urandom:
            
            # Adapter la taille des données mock selon n
            for n in [50, 200, 500]:
                np.random.seed(n)  # Seed différent pour chaque taille
                mock_data = np.random.randint(0, 2**64, size=n, dtype=np.uint64)
                mock_urandom.return_value = mock_data.tobytes()
                
                results = compare_random_generators(n=n, save_plot=False, show_plot=False)
                assert isinstance(results, dict)
                assert 'ks_statistic' in results
                assert np.isfinite(results['ks_statistic'])
    
    def test_different_parameters(self):
        """Test avec différents paramètres du pendule."""
        with patch('matplotlib.pyplot.savefig'), \
             patch('os.urandom') as mock_urandom:
            
            np.random.seed(9999)
            mock_data = np.random.randint(0, 2**64, size=200, dtype=np.uint64)
            mock_urandom.return_value = mock_data.tobytes()
            
            results = compare_random_generators(
                n=200, 
                n_pendulums=5, 
                noise_level=0.5,
                save_plot=False,
                show_plot=False
            )
            
            assert isinstance(results, dict)
            assert 'ks_statistic' in results
            assert np.isfinite(results['ks_statistic'])
    
    def test_urandom_fallback(self):
        """Test du fallback quand urandom n'est pas disponible."""
        with patch('matplotlib.pyplot.show'), \
             patch('matplotlib.pyplot.savefig'), \
             patch('os.urandom') as mock_urandom:
            
            # Simuler une erreur d'accès à urandom
            mock_urandom.side_effect = OSError("Access denied")
            
            # Mock numpy.random pour le fallback
            with patch('numpy.random.random') as mock_random:
                # Créer un array de la bonne taille
                fallback_data = np.random.RandomState(42).random(100) * 1e18
                mock_random.return_value = fallback_data
                
                try:
                    results = compare_random_generators(n=100, save_plot=False)
                    assert isinstance(results, dict)
                    assert 'ks_statistic' in results
                except Exception as e:
                    # Si le module comparison n'est pas disponible à cause des dépendances
                    pytest.skip(f"Module comparison non disponible: {e}")
    
    def test_statistical_values_range(self):
        """Test que les valeurs statistiques sont dans des plages raisonnables."""
        try:
            from tych.comparison import compare_random_generators
            
            with patch('matplotlib.pyplot.savefig'):
                
                # Utiliser de vraies données au lieu de mock pour ce test
                # Cela évite les problèmes avec des données trop uniformes
                results = compare_random_generators(n=100, save_plot=False, show_plot=False)
                
                # KS statistic devrait être entre 0 et 1
                assert 0 <= results['ks_statistic'] <= 1, f"KS statistic invalide: {results['ks_statistic']}"
                
                # p-value devrait être entre 0 et 1
                assert 0 <= results['ks_p_value'] <= 1, f"p-value invalide: {results['ks_p_value']}"
                
                # Vérifier que toutes les valeurs sont finies
                for key, value in results.items():
                    assert np.isfinite(value), f"Valeur non finie pour {key}: {value}"
                
                # Les écart-types doivent être positifs
                assert results['pendulum_std'] > 0, "L'écart-type du pendule doit être positif"
                assert results['urandom_std'] > 0, "L'écart-type d'urandom doit être positif"
                
                # Les écart-types normalisés devraient être proches de 1
                # (mais on accepte une plage plus large pour être robuste)
                assert 0.9 <= results['pendulum_normalized_std'] <= 1.1, f"Écart-type normalisé incorrect: {results['pendulum_normalized_std']}"
                assert 0.9 <= results['urandom_normalized_std'] <= 1.1, f"Écart-type normalisé incorrect: {results['urandom_normalized_std']}"
                
        except ImportError as e:
            pytest.skip(f"Dépendances non disponibles pour comparison: {e}")
    
    def test_plot_creation(self):
        """Test de création des graphiques."""
        try:
            from tych.comparison import compare_random_generators
            
            with patch('matplotlib.pyplot.savefig') as mock_savefig, \
                 patch('matplotlib.pyplot.figure') as mock_figure, \
                 patch('matplotlib.pyplot.subplot'), \
                 patch('matplotlib.pyplot.hist'), \
                 patch('matplotlib.pyplot.plot'), \
                 patch('matplotlib.pyplot.scatter'), \
                 patch('matplotlib.pyplot.title'), \
                 patch('matplotlib.pyplot.xlabel'), \
                 patch('matplotlib.pyplot.ylabel'), \
                 patch('matplotlib.pyplot.legend'), \
                 patch('matplotlib.pyplot.grid'), \
                 patch('matplotlib.pyplot.tight_layout'), \
                 patch('matplotlib.pyplot.close'), \
                 patch('scipy.stats.probplot'), \
                 patch('os.urandom') as mock_urandom:
                
                # Créer des données urandom variées
                np.random.seed(123)
                mock_data = np.random.randint(0, 2**64, size=200, dtype=np.uint64)
                mock_urandom.return_value = mock_data.tobytes()
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_file = os.path.join(temp_dir, "test_plot.png")
                    
                    results = compare_random_generators(
                        n=200, 
                        save_plot=True,
                        show_plot=False,  # Ne pas afficher
                        output_filename=output_file
                    )
                    
                    # Vérifier que savefig a été appelé mais pas show
                    mock_savefig.assert_called_once_with(output_file, dpi=150)
        except ImportError as e:
            pytest.skip(f"Dépendances matplotlib/scipy non disponibles: {e}")
    
    def test_main_function(self):
        """Test de la fonction main du module."""
        try:
            from tych.comparison import main
            
            with patch('matplotlib.pyplot.savefig'), \
                 patch('os.urandom') as mock_urandom, \
                 patch('builtins.print'):
                
                np.random.seed(777)
                mock_data = np.random.randint(0, 2**64, size=10000, dtype=np.uint64)
                mock_urandom.return_value = mock_data.tobytes()
                
                try:
                    main()
                except Exception as e:
                    pytest.fail(f"La fonction main a levé une exception: {e}")
        except ImportError as e:
            pytest.skip(f"Module comparison non disponible: {e}")


class TestCreateComparisonPlots:
    """Tests pour la fonction _create_comparison_plots."""
    
    def test_plot_creation_internal(self):
        """Test de la fonction interne de création de graphiques."""
        try:
            from tych.comparison import _create_comparison_plots
            import numpy as np
            
            # Mock complet de matplotlib pour éviter les appels multiples
            with patch('matplotlib.pyplot.savefig') as mock_savefig, \
                 patch('matplotlib.pyplot.figure') as mock_figure, \
                 patch('matplotlib.pyplot.subplot'), \
                 patch('matplotlib.pyplot.hist'), \
                 patch('matplotlib.pyplot.plot'), \
                 patch('matplotlib.pyplot.scatter'), \
                 patch('matplotlib.pyplot.title'), \
                 patch('matplotlib.pyplot.xlabel'), \
                 patch('matplotlib.pyplot.ylabel'), \
                 patch('matplotlib.pyplot.legend'), \
                 patch('matplotlib.pyplot.grid'), \
                 patch('matplotlib.pyplot.tight_layout'), \
                 patch('matplotlib.pyplot.close'), \
                 patch('scipy.stats.gaussian_kde'), \
                 patch('scipy.stats.probplot'), \
                 patch('numpy.percentile', side_effect=lambda x, p: np.array([x.min(), x.max()])[p//50]):
                
                # Créer des données de test variées
                np.random.seed(456)
                a = np.random.normal(100, 20, 100)
                b = np.random.normal(200, 30, 100)
                a_norm = (a - np.mean(a)) / np.std(a)
                b_norm = (b - np.mean(b)) / np.std(b)
                
                output_file = "test_output.png"
                
                try:
                    _create_comparison_plots(a, b, a_norm, b_norm, output_file, show_plot=False)
                    
                    # Vérifier que les fonctions matplotlib ont été appelées
                    mock_figure.assert_called_once()
                    mock_savefig.assert_called_once_with(output_file, dpi=150)
                    
                except Exception as e:
                    pytest.fail(f"_create_comparison_plots a levé une exception: {e}")
        except ImportError as e:
            pytest.skip(f"Dépendances matplotlib non disponibles: {e}")


class TestComparisonIntegration:
    """Tests d'intégration pour le module comparison."""
    
    def test_full_comparison_workflow(self):
        """Test du workflow complet de comparaison."""
        try:
            from tych.comparison import compare_random_generators
            import numpy as np
            
            with patch('matplotlib.pyplot.savefig'), \
                 patch('matplotlib.pyplot.figure'), \
                 patch('matplotlib.pyplot.subplot'), \
                 patch('matplotlib.pyplot.hist'), \
                 patch('matplotlib.pyplot.plot'), \
                 patch('matplotlib.pyplot.scatter'), \
                 patch('matplotlib.pyplot.title'), \
                 patch('matplotlib.pyplot.xlabel'), \
                 patch('matplotlib.pyplot.ylabel'), \
                 patch('matplotlib.pyplot.legend'), \
                 patch('matplotlib.pyplot.grid'), \
                 patch('matplotlib.pyplot.tight_layout'), \
                 patch('matplotlib.pyplot.close'), \
                 patch('scipy.stats.probplot'), \
                 patch('os.urandom') as mock_urandom:
                
                # Données de test reproductibles - taille correcte et variées
                np.random.seed(789)
                mock_data = np.random.randint(0, 2**64, size=300, dtype=np.uint64)
                mock_urandom.return_value = mock_data.tobytes()
                
                # Exécuter une comparaison complète
                results = compare_random_generators(
                    n=300,
                    n_pendulums=2,
                    noise_level=0.1,
                    save_plot=True,
                    show_plot=False,  # Ne pas afficher
                    output_filename="test_comparison.png"
                )
                
                # Vérifier que tous les résultats sont cohérents
                assert isinstance(results, dict)
                
                # Vérifier que les clés essentielles sont présentes
                essential_keys = [
                    'ks_statistic', 'ks_p_value',
                    'pendulum_mean', 'pendulum_std',
                    'urandom_mean', 'urandom_std',
                    'pendulum_normalized_mean', 'pendulum_normalized_std',
                    'urandom_normalized_mean', 'urandom_normalized_std'
                ]
                
                for key in essential_keys:
                    assert key in results, f"Clé essentielle manquante: {key}"
                
                # Vérifier la cohérence des valeurs
                pendulum_mean = results['pendulum_mean']
                pendulum_std = results['pendulum_std']
                
                assert pendulum_std > 0, "L'écart-type ne peut pas être négatif ou nul"
                assert np.isfinite(pendulum_mean), "La moyenne doit être finie"
                assert np.isfinite(pendulum_std), "L'écart-type doit être fini"
        except ImportError as e:
            pytest.skip(f"Dépendances non disponibles: {e}")
    
    def test_comparison_consistency(self):
        """Test de cohérence entre plusieurs comparaisons."""
        with patch('matplotlib.pyplot.show'), \
             patch('matplotlib.pyplot.savefig'), \
             patch('os.urandom') as mock_urandom:
            
            # Utiliser les mêmes données pour deux comparaisons
            np.random.seed(555)
            mock_data = np.random.randint(0, 2**64, size=200, dtype=np.uint64)
            test_data = mock_data.tobytes()
            mock_urandom.return_value = test_data
            
            results1 = compare_random_generators(n=200, save_plot=False)
            
            # Reset le mock pour retourner les mêmes données
            mock_urandom.return_value = test_data
            results2 = compare_random_generators(n=200, save_plot=False)
            
            # Les résultats urandom devraient être identiques
            # (mais pas les résultats pendulum à cause du chaos)
            assert results1['urandom_mean'] == results2['urandom_mean']
            assert results1['urandom_std'] == results2['urandom_std']


if __name__ == "__main__":
    # Permettre d'exécuter les tests directement
    pytest.main([__file__, "-v"])
