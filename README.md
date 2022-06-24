# stage-2022-mahdi

## Docker

* Clone this repository on a virtual environement and run
```bash
pip install -e .
```

## Installation avec poetry
* On utilise [poetry](https://python-poetry.org/) pour gérer l'environnement virtuel python et suivre les dépendances du projet. 
* Pour installer l'environnement lors de l'initialisation du projet

```bash
poetry install
```

* Pour ajouter une dépendance `<nouveau-paquet-python>` à l'environnement

```bash
poetry add <nouveau-paquet-python>
```

* **Note** : Après l'ajout d'une dépendance, ne pas oublié d'ajouter les modifications aux fichiers `pyproject.toml` et `poetry.lock` à l'historique `git`.

## Installation avec Miniconda3
* On utilise [Miniconda3]( https://docs.conda.io/en/latest/miniconda.html) pour gérer l'environnement virtuel python et suivre les dépendances du projet. 
* Pour installer l'environnement lors de l'initialisation du projet

```bash
conda env create -f environment.yml
```

* Pour activer l'environnement

```bash
conda activate allen2tract
```

* **Note:** Pour mettre à jour l'environnement après avoir modifié le fichier `environment.yml`

```bash
conda env update --file environment.yml #--prune pour désinstaller les dépendances retirées du fichier
```

* Pour ajouter une dépendance `<nouveau-paquet-python>` à l'environnement, l'ajouter dans `requirements.txt`

```bash
pip install -r requirements.txt
```

## Remarque
Pour importer `ANTsPy` à votre projet, vous aurez probablement besoin de libraires supplémentaires
* MacOS

```bash
brew install libpng
```

* Linux

```bash
sudo apt-get install libpng-dev
```
