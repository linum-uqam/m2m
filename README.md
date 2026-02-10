# linum-m2m : LINUM's Meso to Macro Toolkit

A collection of tools to work with both mesoscale brain data (e.g. the Allen Mouse Brain Connectivity Atlas) and with macroscale brain data (e.g. diffusion MRI acquisitions). These tools were first developed by Mahdi Abou-Hamdan during his 2022 summer internship in both the [LINUM](https://linum.info.uqam.ca) lab at [UQAM](https://uqam.ca/) (Canada) and the [GIN-IMN](https://www.gin.cnrs.fr/fr/) at [Université Bordeaux](https://www.u-bordeaux.fr/) (France).

---

📖 **Full documentation**: https://m2m.readthedocs.io/

---

## Quick Installation

### Option 1: Docker (Recommended)

The easiest way to use m2m - no Python installation needed! Pre-built images are available on [Docker Hub](https://hub.docker.com/r/linumuqam/m2m).

**Using docker-compose (with web interface):**

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

**Using the pre-built image directly:**

```bash
# Run m2m scripts
docker run --rm \
  -v $(pwd)/scripts:/scripts:ro \
  -v $(pwd)/data:/data:rw \
  linumuqam/m2m:latest \
  python /scripts/m2m_download_template.py --help

# Or launch the web interface
docker run -p 8501:8501 \
  -v $(pwd)/data:/data \
  linumuqam/m2m:latest
```

### Option 2: Local Python Installation

For development or if you prefer local installation:

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create and activate a virtual environment (Python 3.9, 3.10 or 3.11)
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install --upgrade pip
pip install -e .
```

**Launch the web interface:**
```bash
streamlit run app/m2m_main_page.py
```

**Use the Python API:**
```python
import m2m
# Your code here
```

---

## Requirements

- **Docker**: No Python installation required (Option 1)
- **Python 3.9-3.11**: Python 3.11 recommended (Option 2)
  - Python 3.12+ is not supported due to AllenSDK dependency constraints

---

## Getting Help

- **Documentation**: https://m2m.readthedocs.io/
- **Issues**: https://github.com/linum-uqam/m2m/issues

## Reference

* Abou-Hamdan, M., Cosenza, E., Miraux, S., Petit, L. et Lefebvre, J. (2023). **Exploring the Allen mouse connectivity experiments with new neuroinformatic tools for neurophotonics, diffusion MRI and tractography applications.** In *SPIE Photonics West 2023 (vol. 12365, p. 123650A-123650A‑10)*. https://doi.org/10.1117/12.2649029
