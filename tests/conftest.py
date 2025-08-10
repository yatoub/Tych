"""
Configuration des tests pour Tych
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Ajouter le chemin du package au Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Fixture pour créer un répertoire temporaire."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_data():
    """Fixture pour fournir des données d'exemple."""
    return {
        'small_n': 10,
        'medium_n': 100,
        'large_n': 1000,
        'default_pendulums': 3,
        'default_noise': 0.2,
    }


@pytest.fixture
def mock_matplotlib():
    """Fixture pour mocker matplotlib dans tous les tests."""
    import unittest.mock
    
    with unittest.mock.patch('matplotlib.pyplot.show'), \
         unittest.mock.patch('matplotlib.pyplot.savefig'), \
         unittest.mock.patch('matplotlib.pyplot.figure'), \
         unittest.mock.patch('matplotlib.pyplot.subplot'):
        yield


@pytest.fixture
def mock_urandom():
    """Fixture pour mocker os.urandom."""
    import unittest.mock
    
    with unittest.mock.patch('os.urandom') as mock:
        # Retourner des données déterministes
        mock.return_value = b'\x01\x02\x03\x04\x05\x06\x07\x08' * 1000
        yield mock


@pytest.fixture(scope="session")
def check_dependencies():
    """Fixture pour vérifier les dépendances disponibles."""
    dependencies = {}
    
    try:
        import numpy
        dependencies['numpy'] = True
    except ImportError:
        dependencies['numpy'] = False
    
    try:
        import matplotlib
        dependencies['matplotlib'] = True
    except ImportError:
        dependencies['matplotlib'] = False
    
    try:
        import scipy
        dependencies['scipy'] = True
    except ImportError:
        dependencies['scipy'] = False
    
    return dependencies


def pytest_configure(config):
    """Configuration pytest."""
    # Ajouter des markers personnalisés
    config.addinivalue_line(
        "markers", "requires_matplotlib: mark test as requiring matplotlib"
    )
    config.addinivalue_line(
        "markers", "requires_scipy: mark test as requiring scipy"
    )
    config.addinivalue_line(
        "markers", "requires_all_deps: mark test as requiring all dependencies"
    )


def pytest_collection_modifyitems(config, items):
    """Modifier la collection de tests selon les dépendances disponibles."""
    try:
        import matplotlib
        has_matplotlib = True
    except ImportError:
        has_matplotlib = False
    
    try:
        import scipy
        has_scipy = True
    except ImportError:
        has_scipy = False
    
    skip_matplotlib = pytest.mark.skip(reason="matplotlib not available")
    skip_scipy = pytest.mark.skip(reason="scipy not available")
    skip_all_deps = pytest.mark.skip(reason="required dependencies not available")
    
    for item in items:
        if "requires_matplotlib" in item.keywords and not has_matplotlib:
            item.add_marker(skip_matplotlib)
        elif "requires_scipy" in item.keywords and not has_scipy:
            item.add_marker(skip_scipy)
        elif "requires_all_deps" in item.keywords and not (has_matplotlib and has_scipy):
            item.add_marker(skip_all_deps)


def pytest_runtest_setup(item):
    """Setup avant chaque test."""
    # Supprimer les warnings pour les tests
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)


@pytest.fixture(autouse=True)
def suppress_prints():
    """Supprimer les prints pendant les tests."""
    import unittest.mock
    with unittest.mock.patch('builtins.print'):
        yield
