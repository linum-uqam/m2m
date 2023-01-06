# linum-m2m : LINUM's Meso to Macro Toolkit
A collection of tools to work with both mesoscale brain data (e.g. the Allen Mouse Brain Connectivity Atlas) and with macroscale brain data (e.g. diffusion MRI acquisitions). These tools were first developed by Mahdi Abou-Hamdan during his 2022 summer internship in both the [LINUM](https://linum.info.uqam.ca) lab at [UQAM](https://uqam.ca/) (Canada) and the [GIN-IMN](https://www.gin.cnrs.fr/fr/) at [Université Bordeaux](https://www.u-bordeaux.fr/) (France).

# Installation

A docker image for this project is automatically built and pushed to DockerHub (https://hub.docker.com/r/linumuqam/m2m) everytime the `main` branch is updated. This image contains the toolkit dependencies (Python 3.7, AllenSDK, antspyx, etc.) along with the m2m module and scripts. Using the docker image is recommendend to simplify the installation process and dependency management.

## Docker Installation (Recommended)
* Install [Docker Desktop](https://www.docker.com/get-started/)
* Pull the latest docker image from DockerHub
```bash
docker pull linumuqam/m2m:latest
```

* Alternatively, clone the repository and compile the docker image locally.
```bash
docker build --pull --rm -t linumuqam/m2m:latest .
```

## Pip installation (for development)

* Clone the repository, create a python virtual environment with Python 3.7, and then install the package with
```bash
pip install -e .
```

### Notes
You will probably need to install these additionnal dependencies before installing the package
* MacOS
```bash
brew install libpng openblas lapack gfortran
```

* Linux

```bash
sudo apt-get install libpng-dev libblas-dev liblapack-dev
```

If none of this work, try installing the dependencies with an anaconda virtual environment
* Conda
```
conda install libpng libblas liblapack
```

# Usage

## Docker
* Display the help for a script
```bash
docker run linumuqam/m2m allen_compute_transform_matrix.py --help
```

* Compute the transform matrix `transform_50micron.mat`, given a user-space reference volume `reference.nii.gz` in the folder `/path/to/local/data`.
```bash
docker run -v /path/to/local/data:/data linumuqam/m2m allen_compute_transform_matrix.py /data/reference.nii.gz /data/transform_50micron.mat 50
```
* Import the projection density from the experiment id `100140756`. The downloaded data will be save in the `/path/to/local/data/` directory which is binded to the `/data` directory in the docker container.

```bash
docker run -v /path/to/local/data:/data linumuqam/m2m allen_import_proj_density.py 100140756 /data/reference.nii.gz /data/transform_50micron.mat 50 -d /data
```

* Find crossings based on two injection positions, (132,133,69) for the first injection position and (143,94,69) for the second injection position. The injection positions are given in voxel in the user space. For this example, a threshold of 0.07 is used to generate the crossings mask.

```
docker run -v /path/to/local/data:/data linumuqam/m2m allen_crossing_finder.py /data/transform_50micron.mat /data/reference.nii.gz 50 --red 132 133 69 --green 143 94 69 --injection --dir /data/detected_crossings --threshold 0.07
```

* Import tracts given an experiment ID.

```bash
docker run -v /path/to/local/data:/data linumuqam/m2m allen_import_tract.py /data/output_tracts_100140756.trk /data/transform_50micron.mat /data/reference.nii.gz 50 --ids 100140756
```

* To execute an image interactively (note that no modification inside the container will be saved)
```bash
docker run --rm -it --entrypoint bash linumuqam/m2m
```

# TODOs
* [x] Configure the automated docker image build to be able to pull it from docker hub.
* [ ] Find a way to use cache with docker
* [ ] Document how to use the docker image for development (manually, and with Visual Studio Code)
* [ ] Document MI-Brain visualization & interaction

# References


