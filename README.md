# stage-2022-mahdi

## Installation
* On utilise [poetry](https://python-poetry.org/) pour gérer l'environnement virtuel python et suivre les dépendances du projet. 
* Pour installer l'environnement lors de l'initialisation du projet

```bash
poetry install
```

* Pour ajouter une dépendance <nouveau-paquet-python> à l'environnement

```bash
poetry add <nouveau-paquet-python>
```

* **Note** : Après l'ajout d'une dépendance, ne pas oublié d'ajouter les modifications aux fichiers `pyproject.toml` et `poetry.lock` à l'historique `git`.