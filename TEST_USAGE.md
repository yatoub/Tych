# Guide d'utilisation des tests pour Tych

## Tests de base
```bash
python run_tests.py
```

## Tests rapides (recommandé pour développement)
```bash
python run_tests.py --fast
```

## Tests avec couverture de code
```bash
python run_tests.py --coverage
```

## Tests spécifiques
```bash
python run_tests.py --unit           # Tests unitaires seulement
python run_tests.py --integration    # Tests d'intégration seulement
python run_tests.py --performance    # Tests de performance seulement
```

## Via pytest directement
```bash
pytest                               # Tous les tests
pytest -v                           # Mode verbeux
pytest -m "not slow"                # Exclure les tests lents
pytest tests/test_pendulum.py       # Tests d'un fichier spécifique
pytest --cov=tych                   # Avec couverture de code
```

## Via make (si disponible)
```bash
make test                           # Tests de base
make test-fast                      # Tests rapides
make test-coverage                  # Avec couverture
```

## Tests avec sélection de markers
```bash
pytest -m "unit"                    # Tests unitaires
pytest -m "integration"             # Tests d'intégration
pytest -m "slow"                    # Tests lents seulement
```
