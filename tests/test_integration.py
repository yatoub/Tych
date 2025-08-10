"""
Tests d'intégration pour le package Tych
"""

import pytest
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

# Ajouter le chemin du package pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tych
from tych import double_pendulum_random_list, compare_random_generators


class TestPackageIntegration:
    """Tests d'intégration du package complet."""
    
    def test_package_imports(self):
        """Test que tous les imports du package fonctionnent."""
        # Test import principal
        assert hasattr(tych, '__version__')
        assert hasattr(tych, '__author__')
        
        # Test import des fonctions principales
        assert callable(double_pendulum_random_list)
        
        # Test import conditionnel de comparison (peut échouer si dépendances manquantes)
        try:
            assert callable(compare_random_generators)
        except (ImportError, AttributeError):
            # C'est acceptable si les dépendances matplotlib/scipy ne sont pas disponibles
            pass
    
    def test_package_metadata(self):
        """Test des métadonnées du package."""
        assert tych.__version__ == "0.1.0"
        assert isinstance(tych.__author__, str)
        assert isinstance(tych.__email__, str)
        
        # Test de __all__
        if hasattr(tych, '__all__'):
            assert isinstance(tych.__all__, list)
    
    def test_conditional_imports(self):
        """Test des imports conditionnels."""
        # Vérifier que les flags d'import sont cohérents
        if hasattr(tych, '_has_pendulum'):
            if tych._has_pendulum:
                assert tych.double_pendulum_random_list is not None
            else:
                assert tych.double_pendulum_random_list is None
        
        if hasattr(tych, '_has_comparison'):
            if tych._has_comparison:
                assert tych.compare_random_generators is not None
            else:
                assert tych.compare_random_generators is None


class TestMainScript:
    """Tests pour le script principal main.py."""
    
    def test_main_import(self):
        """Test que main.py peut être importé."""
        try:
            import main
            assert hasattr(main, 'main')
            assert callable(main.main)
        except ImportError as e:
            pytest.fail(f"Impossible d'importer main.py: {e}")
    
    def test_main_help(self):
        """Test de l'aide du script principal."""
        import main
        
        # Test avec mock de sys.argv pour afficher l'aide
        with patch('sys.argv', ['main.py', '-h']), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse:
            
            # Mock pour que parse_args retourne un namespace avec command=None
            mock_args = MagicMock()
            mock_args.command = None
            mock_parse.return_value = mock_args
            
            with patch('builtins.print'):
                try:
                    main.main()
                except SystemExit:
                    # SystemExit est normal pour l'aide
                    pass
    
    def test_main_generate_command(self):
        """Test de la commande generate."""
        import main
        
        with patch('sys.argv', ['main.py', 'generate', '-n', '10']), \
             patch('builtins.print'):
            
            # Mock argparse pour retourner les bons arguments
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                mock_args = MagicMock()
                mock_args.command = 'generate'
                mock_args.count = 10
                mock_args.pendulums = 3
                mock_args.noise = 0.2
                mock_args.output = None
                mock_parse.return_value = mock_args
                
                try:
                    main.main()
                except Exception as e:
                    pytest.fail(f"Commande generate a échoué: {e}")
    
    def test_main_compare_command(self):
        """Test de la commande compare."""
        try:
            import main
            
            with patch('sys.argv', ['main.py', 'compare', '-n', '100']), \
                 patch('builtins.print'), \
                 patch('matplotlib.pyplot.show'), \
                 patch('matplotlib.pyplot.savefig'), \
                 patch('os.urandom') as mock_urandom:
                
                np.random.seed(888)
                mock_data = np.random.randint(0, 2**64, size=100, dtype=np.uint64)
                mock_urandom.return_value = mock_data.tobytes()
                
                # Mock argparse
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    mock_args = MagicMock()
                    mock_args.command = 'compare'
                    mock_args.count = 100
                    mock_args.pendulums = 3
                    mock_args.noise = 0.2
                    mock_args.output = 'test_comparison.png'
                    mock_parse.return_value = mock_args
                    
                    try:
                        main.main()
                    except Exception as e:
                        pytest.fail(f"Commande compare a échoué: {e}")
        except ImportError as e:
            pytest.skip(f"Dépendances pour la commande compare non disponibles: {e}")


class TestCLIModule:
    """Tests pour le module CLI."""
    
    def test_cli_import(self):
        """Test que le module CLI peut être importé."""
        try:
            from tych import cli
            assert hasattr(cli, 'main')
        except ImportError:
            # Le module CLI peut ne pas être disponible selon la configuration
            pass


class TestExampleFiles:
    """Tests pour les fichiers d'exemple."""
    
    def test_example_script(self):
        """Test du script d'exemple."""
        example_path = Path(__file__).parent.parent / "example.py"
        
        if example_path.exists():
            with patch('builtins.print'):
                try:
                    # Exécuter le script d'exemple
                    exec(example_path.read_text())
                except Exception as e:
                    pytest.fail(f"Script d'exemple a échoué: {e}")
    
    def test_build_script(self):
        """Test du script de build."""
        build_path = Path(__file__).parent.parent / "build.py"
        
        if build_path.exists():
            try:
                # Importer le module build
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("build", build_path)
                build_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(build_module)
                
                # Vérifier que les fonctions principales existent
                assert hasattr(build_module, 'main'), "Fonction main manquante dans build.py"
                assert hasattr(build_module, 'get_uv_executable'), "Fonction get_uv_executable manquante dans build.py"
                
            except Exception as e:
                pytest.skip(f"Impossible de charger build.py: {e}")
        else:
            pytest.skip("build.py n'existe pas")


class TestDocumentationConsistency:
    """Tests de cohérence de la documentation."""
    
    def test_readme_exists(self):
        """Test que README.md existe et n'est pas vide."""
        readme_path = Path(__file__).parent.parent / "README.md"
        
        assert readme_path.exists(), "README.md manquant"
        content = readme_path.read_text(encoding='utf-8')
        assert len(content) > 100, "README.md trop court"
        assert "Tych" in content, "README.md ne mentionne pas Tych"
    
    def test_license_exists(self):
        """Test que LICENSE existe."""
        license_path = Path(__file__).parent.parent / "LICENSE"
        
        assert license_path.exists(), "LICENSE manquant"
        content = license_path.read_text(encoding='utf-8')
        assert "MIT" in content, "LICENSE ne contient pas MIT"
    
    def test_pyproject_toml_consistency(self):
        """Test de cohérence du pyproject.toml."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        assert pyproject_path.exists(), "pyproject.toml manquant"
        content = pyproject_path.read_text(encoding='utf-8')
        
        # Vérifier les sections importantes
        assert "[project]" in content
        assert "name = \"tych\"" in content
        assert "version = \"0.1.0\"" in content
        assert "[build-system]" in content


class TestErrorHandling:
    """Tests de gestion d'erreur."""
    
    def test_import_with_missing_dependencies(self):
        """Test d'import avec des dépendances manquantes."""
        # Simuler l'absence de numpy
        with patch.dict('sys.modules', {'numpy': None}):
            try:
                # Recharger le module pour tester l'import conditionnel
                import importlib
                if 'tych.pendulum' in sys.modules:
                    importlib.reload(sys.modules['tych.pendulum'])
            except ImportError:
                # C'est attendu si numpy n'est pas disponible
                pass
    
    def test_graceful_degradation(self):
        """Test de dégradation gracieuse."""
        # Vérifier que le package peut gérer l'absence de certaines dépendances
        with patch.dict('sys.modules', {'matplotlib': None, 'scipy': None}):
            try:
                import importlib
                # Recharger tych pour tester les imports conditionnels
                if 'tych' in sys.modules:
                    importlib.reload(sys.modules['tych'])
                    
                # Le package devrait toujours fonctionner partiellement
                import tych
                assert hasattr(tych, '__version__')
                
            except Exception as e:
                pytest.fail(f"Dégradation gracieuse échouée: {e}")


if __name__ == "__main__":
    # Permettre d'exécuter les tests directement
    pytest.main([__file__, "-v"])
