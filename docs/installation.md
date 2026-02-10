# Installation

m2m can be installed using Docker (recommended for simplicity) or locally with Python.

## Quick Start

### Option 1: Docker (Recommended)

The easiest way to use m2m - no Python installation needed! Pre-built images are automatically built and published to [Docker Hub](https://hub.docker.com/r/linumuqam/m2m).

**Using the pre-built image (no git clone needed):**

```bash
# Create data directories
mkdir -p data/input data/output

# Run the web interface directly
docker run -p 8501:8501 -v $(pwd)/data:/data linumuqam/m2m:latest

# Access the web interface at http://localhost:8501
```

**Using docker-compose (recommended for development):**

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

**Requirements:**

* Docker Desktop or Docker Engine
* Docker Compose (optional, for docker-compose method)

**Benefits:**

* ✅ No Python installation required
* ✅ Works identically on all platforms (Linux, macOS, Windows)
* ✅ All dependencies pre-installed
* ✅ Isolated environment
* ✅ Pre-built images updated automatically on each release

### Option 2: Local Python Installation

For development or if you prefer a local installation:

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create a virtual environment with Python 3.11 (recommended)
python3.11 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install --upgrade pip
pip install -e .
```

**Requirements:**

* Python 3.9, 3.10, or 3.11 (Python 3.11 recommended)
* Python 3.12+ is not supported due to AllenSDK dependency constraints
* pip (usually comes with Python)
* Git

**Platform Notes:**

* **Linux**: Fully supported
* **macOS**: Fully supported (Intel and Apple Silicon)
* **Windows**: Most features work, but antspyx may have limited support. Use Docker for full compatibility.

### Option 3: Using Conda (Optional)

If you prefer conda for Python version management:

```bash
# Create a conda environment with Python 3.11
conda create -n m2m python=3.11 pip
conda activate m2m

# Install m2m using pip
cd m2m
pip install -e .
```

```{note}
Conda is no longer required. The package uses standard pip + venv installation for simplicity.
```

## Running m2m

### Docker Usage

**Web Interface:**

```bash
docker-compose up
# Access at http://localhost:8501
```

**Run m2m Scripts:**

```bash
docker run --rm \
  -v $(pwd)/scripts:/scripts:ro \
  -v $(pwd)/data:/data:rw \
  linumuqam/m2m:latest \
  python /scripts/m2m_download_template.py --help
```

**Interactive Python Session:**

```bash
docker run --rm -it \
  -v $(pwd)/data:/data \
  linumuqam/m2m:latest \
  python
```

**Bash Shell:**

```bash
docker run --rm -it \
  -v $(pwd)/scripts:/scripts \
  -v $(pwd)/data:/data \
  linumuqam/m2m:latest \
  bash
```

### Local Installation Usage

**Web Interface:**

```bash
source .venv/bin/activate  # Activate your virtual environment
streamlit run app/m2m_main_page.py
```

**Python API:**

```python
import m2m
# Your code here
```

**Command Line Scripts:**

```bash
source .venv/bin/activate
m2m_download_template.py --help
```

## Update

### Docker

To update the Docker image:

```bash
docker-compose down
git pull
docker-compose build --no-cache
docker-compose up
```

### Local Installation

To update your local installation:

```bash
git pull
source .venv/bin/activate  # or: conda activate m2m
pip install --upgrade -e .
```

## Troubleshooting

### NumPy Version Conflicts

The Allen SDK requires numpy < 1.24. If you encounter numpy version conflicts:

```bash
pip install "numpy>=1.23,<1.24"
pip install -e .
```

### Docker Build Issues

If Docker build fails or takes too long:

```bash
# Clear Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

### Port Already in Use

If port 8501 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8502:8501"  # Use port 8502 instead
```

Then access at http://localhost:8502

### Platform-Specific Issues

**Windows (WSL):**

For native Windows, we recommend using Docker. Alternatively, use WSL2:

```bash
# Install WSL (run as administrator)
wsl --install
```

For more details, see the [official WSL documentation](https://learn.microsoft.com/en-us/windows/wsl/install/)

**macOS Apple Silicon:**

All dependencies work on Apple Silicon (M1/M2/M3). Python 3.11 recommended.

**Linux:**

Ensure you have development tools:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev build-essential
```

## Getting Help

* **GitHub Issues**: https://github.com/linum-uqam/m2m/issues
* **Documentation**: https://m2m.readthedocs.io/
