# stage-2022-mahdi

# Installation
## Docker Installation (Recommended)

* Compile the docker image `linum_m2m:latest`
```bash
docker build --pull --rm -t linum_m2m:latest .
```

## Pip installation (for development)

* Cloner ce dépôt sur un environnement virtuel avec python 3.7.0 et executer
```bash
pip install -e .
```

## Remarque !
Vous aurez probablement besoin de libraires supplémentaires avant d'installer le paquet
* MacOS

```bash
brew install libpng openblas lapack gfortran
```

* Linux

```bash
sudo apt-get install libpng-dev libblas-dev liblapack-dev
```

Si tout cela ne fonctionne pas, installez les librairies dans l'environement virtuel
* Conda
```
conda install libpng libblas liblapack
```

# Usage

## Docker
* Display the help for a script
```bash
docker run linum_m2m allen_compute_transform_matrix.py --help
```

* Compute the transform matrix `transform_50micron.mat`, given a user-space reference volume `reference.nii.gz` in the folder `/path/to/local/data`.
```bash
docker run -v /path/to/local/data:/data linum_m2m allen_compute_transform_matrix.py /data/reference.nii.gz /data/transform_50micron.mat 50
```
* Import the projection density from the experiment id `100140756`. The downloaded data will be save in the `/path/to/local/data/` directory which is binded to the `/data` directory in the docker container.

```bash
docker run -v /path/to/local/data:/data linum_m2m allen_import_proj_density.py 100140756 /data/reference.nii.gz /data/transform_50micron.mat 50 -d /data
```

* Find crossings based on two injection positions, (132,133,69) for the first injection position and (143,94,69) for the second injection position. The injection positions are given in voxel in the user space. For this example, a threshold of 0.07 is used to generate the crossings mask.

```
docker run -v /path/to/local/data:/data linum_m2m allen_crossing_finder.py /data/transform_50micron.mat /data/reference.nii.gz 50 --red 132 133 69 --green 143 94 69 --injection --dir /data/detected_crossings --threshold 0.07
```

* Import tracts given an experiment ID.

```bash
docker run -v /path/to/local/data:/data linum_m2m allen_import_tract.py /data/output_tracts_100140756.trk /data/transform_50micron.mat /data/reference.nii.gz 50 --ids 100140756
```

* To execute an image interactively (note that no modification inside the container will be saved)
```bash
docker run --rm -it --entrypoint bash linum_m2m
```

# TODOs
* [ ] Configure the automated docker image build to be able to pull it from docker hub.
* [ ] Find a way to use cache with docker
* [ ] Document how to use the docker image for development (manually, and with Visual Studio Code)
* [ ] Document MI-Brain visualization & interaction

