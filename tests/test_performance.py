"""
Tests de performance pour le package Tych
"""

import pytest
import time
import sys
import os

# Ajouter le chemin du package pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tych.pendulum import double_pendulum_random_list


class TestPerformance:
    """Tests de performance du générateur."""
    
    @pytest.mark.slow
    def test_generation_speed_small(self):
        """Test de vitesse pour petite génération."""
        n = 100
        start_time = time.time()
        
        numbers = double_pendulum_random_list(n=n)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(numbers) == n
        assert duration < 1.0, f"Génération de {n} nombres trop lente: {duration:.3f}s"
    
    @pytest.mark.slow
    def test_generation_speed_medium(self):
        """Test de vitesse pour génération moyenne."""
        n = 1000
        start_time = time.time()
        
        numbers = double_pendulum_random_list(n=n)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(numbers) == n
        assert duration < 5.0, f"Génération de {n} nombres trop lente: {duration:.3f}s"
    
    @pytest.mark.slow
    def test_generation_speed_large(self):
        """Test de vitesse pour grande génération."""
        n = 5000
        start_time = time.time()
        
        numbers = double_pendulum_random_list(n=n)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(numbers) == n
        assert duration < 30.0, f"Génération de {n} nombres trop lente: {duration:.3f}s"
    
    def test_memory_usage(self):
        """Test basique d'utilisation mémoire."""
        import gc
        
        # Forcer le garbage collection
        gc.collect()
        
        # Générer plusieurs séquences
        for _ in range(10):
            numbers = double_pendulum_random_list(n=1000)
            assert len(numbers) == 1000
            del numbers
        
        # Le test passe s'il n'y a pas d'erreur de mémoire
        gc.collect()
    
    def test_scalability_pendulums(self):
        """Test de scalabilité avec le nombre de pendules."""
        n = 100
        times = []
        
        for n_pendulums in [1, 3, 5, 10]:
            start_time = time.time()
            numbers = double_pendulum_random_list(n=n, n_pendulums=n_pendulums)
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            
            assert len(numbers) == n
        
        # Le temps ne devrait pas croître de façon exponentielle
        # (test basique de scalabilité)
        assert times[-1] < times[0] * 50, "Scalabilité problématique"


class TestMemoryProfiler:
    """Tests de profiling mémoire (optionnels)."""
    
    def test_memory_leak_detection(self):
        """Test de détection de fuites mémoire."""
        import gc
        
        # Mesure initiale
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Générer plusieurs fois
        for _ in range(20):
            numbers = double_pendulum_random_list(n=500)
            del numbers
        
        # Mesure finale
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Ne devrait pas avoir une croissance significative d'objets
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Possible fuite mémoire: {object_growth} nouveaux objets"


if __name__ == "__main__":
    # Permettre d'exécuter les tests directement
    pytest.main([__file__, "-v", "-m", "not slow"])
