# linum-m2m : LINUM's Meso to Macro Toolkit
A collection of tools to work with both mesoscale brain data (e.g. the Allen Mouse Brain Connectivity Atlas) and with macroscale brain data (e.g. diffusion MRI acquisitions). These tools were first developed by Mahdi Abou-Hamdan during his 2022 summer internship in both the [LINUM](https://linum.info.uqam.ca) lab at [UQAM](https://uqam.ca/) (Canada) and the [GIN-IMN](https://www.gin.cnrs.fr/fr/) at [Université Bordeaux](https://www.u-bordeaux.fr/) (France).

## Installation and Usage

> Please refer to https://m2m.readthedocs.io/ for up-to-date installation & usage instructions and the API documentation.

### Quick Installation

We recommend using Anaconda/Miniconda for installation. Once the source code is cloned/downloaded, open a terminal in the source code location and install:

```bash
# Create and activate the conda environment
conda env create -f environment.yml
conda activate m2m

# Install the package
pip install -e .
```

**Note**: Python 3.9-3.12 is supported. Python 3.13+ is not yet compatible with all dependencies.

For detailed installation instructions, troubleshooting, and platform-specific notes, see [INSTALL.md](INSTALL.md).

### Usage

After installation, activate the `m2m` environment before using the software:

```bash
conda activate m2m
```

**Web Application**: Launch the m2m web application with:
```bash
streamlit run app/m2m_main_page.py
```

**Python API**: Import and use m2m in your Python scripts:
```python
import m2m
# Your code here
```

## References

* Mahdi Abou-Hamdan, Elise Cosenza, Sylvain Miraux, Laurent Petit, Joël Lefebvre, "Exploring the Allen mouse connectivity experiments with new neuroinformatic tools for neurophotonics, diffusion MRI and tractography applications," Proc. SPIE 12365, Neural Imaging and Sensing 2023, 123650A (14 March 2023); https://doi.org/10.1117/12.2649029


