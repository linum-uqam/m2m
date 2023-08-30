# linum-m2m : LINUM's Meso to Macro Toolkit
A collection of tools to work with both mesoscale brain data (e.g. the Allen Mouse Brain Connectivity Atlas) and with macroscale brain data (e.g. diffusion MRI acquisitions). These tools were first developed by Mahdi Abou-Hamdan during his 2022 summer internship in both the [LINUM](https://linum.info.uqam.ca) lab at [UQAM](https://uqam.ca/) (Canada) and the [GIN-IMN](https://www.gin.cnrs.fr/fr/) at [Université Bordeaux](https://www.u-bordeaux.fr/) (France).

## Installation and Usage

> Please refer to https://m2m.readthedocs.io/ for up-to-date installation & usage instructions and the API documentation. 

* To install the tool, we recommend to use Anaconda. Once the source code is cloned / downloaded, open a terminal in the source code location and install it with

```bash
    conda env create -f environment.yml
    conda activate m2m
    pip install -e .
```

* To use the software, you then need to activate the Anaconda `m2m` environment. For example, to use the m2m web application:

```bash
    conda activate m2m
    streamlit run app/m2m_main_page.py
```

## References

* Mahdi Abou-Hamdan, Elise Cosenza, Sylvain Miraux, Laurent Petit, Joël Lefebvre, "Exploring the Allen mouse connectivity experiments with new neuroinformatic tools for neurophotonics, diffusion MRI and tractography applications," Proc. SPIE 12365, Neural Imaging and Sensing 2023, 123650A (14 March 2023); https://doi.org/10.1117/12.2649029


