# linum-m2m : LINUM's Meso to Macro Toolkit
A collection of tools to work with both mesoscale brain data (e.g. the Allen Mouse Brain Connectivity Atlas) and with macroscale brain data (e.g. diffusion MRI acquisitions). These tools were first developed by Mahdi Abou-Hamdan during his 2022 summer internship in both the [LINUM](https://linum.info.uqam.ca) lab at [UQAM](https://uqam.ca/) (Canada) and the [GIN-IMN](https://www.gin.cnrs.fr/fr/) at [Université Bordeaux](https://www.u-bordeaux.fr/) (France).

## Installation and Usage

> Please refer to https://m2m.readthedocs.io/ for up-to-date installation & usage instructions and the API documentation.

### Quick Installation

#### Option 1: Docker (Recommended - No Python Installation Needed!)

The easiest way to use m2m - just install Docker:

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create data directories
mkdir -p data/input data/output

# Start with Docker Compose
docker-compose up

# Access the web interface at http://localhost:8501
```

**Benefits**: No Python setup, works on all platforms, isolated environment.

#### Option 2: Local Python Installation

For development or if you prefer local installation:

```bash
# Clone and navigate to the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package (includes all dependencies)
pip install --upgrade pip
pip install -e .
```

**Requirements**: Python 3.9-3.12 (Python 3.11 recommended). Python 3.13+ not yet supported.

📖 For detailed instructions, troubleshooting, and platform-specific notes, see [INSTALL.md](INSTALL.md).

### Usage

#### Using Docker

```bash
# Start web interface
docker-compose up

# Run m2m scripts from the scripts/ directory
# Example: Download template data
docker run --rm \
  -v $(pwd)/scripts:/scripts:ro \
  -v $(pwd)/data:/data:rw \
  linum/m2m:latest \
  python /scripts/m2m_download_template.py --help

# Run your own scripts
docker run --rm \
  -v $(pwd)/scripts:/scripts:ro \
  -v $(pwd)/data:/data:rw \
  linum/m2m:latest \
  python /scripts/your_analysis.py

# Interactive Python session
docker run --rm -it -v $(pwd)/data:/data linum/m2m:latest python

# Interactive bash shell
docker run --rm -it -v $(pwd)/scripts:/scripts -v $(pwd)/data:/data linum/m2m:latest bash

# Stop the application
docker-compose down
```

Access the web interface at **http://localhost:8501**

#### Using Local Installation

After installation, activate your environment before using the software:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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

* Abou-Hamdan, M., Cosenza, E., Miraux, S., Petit, L. et Lefebvre, J. (2023). **Exploring the Allen mouse connectivity experiments with new neuroinformatic tools for neurophotonics, diffusion MRI and tractography applications.** In *SPIE Photonics West 2023 (vol. 12365, p. 123650A-123650A‑10)*. https://doi.org/10.1117/12.2649029


