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
docker run linumuqam/m2m m2m_compute_transform_matrix.py --help
```

* Compute the transform matrix `transform_50micron.mat`, given a user-space reference volume `reference.nii.gz` in the folder `/path/to/local/data`.
```bash
docker run -v /path/to/local/data:/data linumuqam/m2m m2m_compute_transform_matrix.py /data/reference.nii.gz /data/transform_50micron.mat 50
```
* Import the projection density from the experiment id `100140756`. The downloaded data will be save in the `/path/to/local/data/` directory which is binded to the `/data` directory in the docker container.

```bash
docker run -v /path/to/local/data:/data linumuqam/m2m m2m_import_proj_density.py 100140756 /data/reference.nii.gz /data/transform_50micron.mat 50 -d /data
```

* Find crossings based on two injection positions, (132,133,69) for the first injection position and (143,94,69) for the second injection position. The injection positions are given in voxel in the user space. For this example, a threshold of 0.07 is used to generate the crossings mask.

```
docker run -v /path/to/local/data:/data linumuqam/m2m m2m_crossing_finder.py /data/transform_50micron.mat /data/reference.nii.gz 50 --red 132 133 69 --green 143 94 69 --injection --dir /data/detected_crossings --threshold 0.07
```

* Import tracts given an experiment ID.

```bash
docker run -v /path/to/local/data:/data linumuqam/m2m m2m_import_tract.py /data/output_tracts_100140756.trk /data/transform_50micron.mat /data/reference.nii.gz 50 --ids 100140756
```

* Transform the Allen tractogram (Wildtype, RAS@50um) to the User's Data Space. Note that this command will take a few minutes to complete, as the tractogram first need to be downloaded and then each streamline have to be transformed to the user data space.
```bash
docker run -v /path/to/local/data:/data linumuqam/m2m python m2m_transform_tractogram.py /data/transformed_tractogram.trk /data/transform_50micron.mat /data/reference.nii.gz
```

* Extract a bundle of streamlines from the transformed Allen tractogram.
```bash
docker run -v /path/to/local/data:/data linumuqam/m2m m2m_tract_filter.py /data/input_tractogram.trk /data/output.trk /data/reference.nii.gz --sphere --center 132 133 69 --radius 2
```

* To execute an image interactively (note that no modification inside the container will be saved)
```bash
docker run --rm -it --entrypoint bash linumuqam/m2m
```

* **Note**: Some scripts will require a cache to accelerate processing. To do this with docker, we can use a docker volume named `m2m_cache` and mount it in the docker's home directory. You can add this option to the previous command to use a cache.
```bash
-v m2m_cache:/home/appuser/.m2m 
```

## **Docker (development)**
To use the docker image for development, you need to replace the module and script source code by your own development version. To do this, we can bind mount the local working directory containing the source code and replace the `/app` source code in the docker image.

* Pull or build the latest version of the `linumuqam/m2m` docker image as explained in the [Installation] section.
* Make sure you are in the source code directory on your computer
* Execute your code while mounting the local source code directory. For example, to use your modified version of the `m2m_compute_transform_matrix.py` script,

```bash
docker run -v ${PWD}:/app linumuqam/m2m python scripts/m2m_compute_transform_matrix.py --help
```

Likewise, the docker image can be configured to be used as a Python interpreter by your IDE. Please refer to [these instructions](https://code.visualstudio.com/docs/containers/quickstart-python) for Visual Studio Code and to [these instructions](https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html) for PyCharm. 

# References

* Abou-Hamdan, M., Cosenza, E., Miraux, S., Petit, L. and Lefebvre, J. (2023). Exploring the Allen Mouse Connectivity experiments with new neuroinformatic tools for neurophotonics, diffusion MRI and tractography applications. _SPIE Photonics West 2023_ (San Francisco, USA).


