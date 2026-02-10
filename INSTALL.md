# Installation Guide for m2m

This guide provides detailed installation instructions for the m2m (Meso to Macro) toolkit across different platforms.

## Prerequisites

### Option 1: Docker (Easiest - No Python Installation Required)
- **Docker** ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** (usually included with Docker Desktop)

### Option 2: Local Python Installation
- **Python 3.9, 3.10, 3.11, or 3.12** (Python 3.11 recommended for best compatibility)
- Python 3.13+ is **not supported** due to dependency constraints
- **Git** (for cloning the repository)
- **pip** (usually comes with Python)

## Quick Start

### Option A: Docker (Recommended for Simplicity)

Docker provides the simplest installation - no Python setup required! All dependencies are pre-installed in the container.

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create data directories
mkdir -p data/input data/output

# Start the application with Docker Compose
docker-compose up

# The Streamlit web interface will be available at http://localhost:8501
```

**That's it!** The container includes Python 3.11, all dependencies, and the m2m toolkit ready to use.

**To run Python scripts instead of the web interface:**
```bash
# Run a Python script in the container
docker-compose run --rm m2m-cli python your_script.py

# Or get an interactive Python session
docker-compose run --rm m2m-cli python

# Or get a bash shell
docker-compose run --rm m2m-cli bash
```

**To stop the application:**
```bash
docker-compose down
```

**Benefits of Docker:**
- ✅ No Python installation required
- ✅ No dependency management
- ✅ Works identically on all platforms (Linux, macOS, Windows)
- ✅ Isolated environment - won't affect your system
- ✅ Easy cleanup - just remove the container

### Option B: Local Python Installation (Pip + Venv)

If you prefer a local installation or need to develop/modify the code:

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create a virtual environment with Python 3.11 (recommended)
python3.11 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Upgrade pip to the latest version
pip install --upgrade pip setuptools wheel

# Install the package in development mode (includes all dependencies)
pip install -e .
```

**Note**: All dependencies are automatically installed from [requirements.txt](requirements.txt) when you run `pip install -e .`

### Option C: Using Conda (Optional)

If you prefer conda for Python version management:

```bash
# Create a conda environment with Python 3.11
conda create -n m2m python=3.11 pip
conda activate m2m

# Install the package
pip install -e .
```

## Platform-Specific Notes

### macOS (Intel and Apple Silicon)

Installation should work smoothly on both Intel and Apple Silicon Macs:

```bash
# Standard installation works for both architectures
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
```

**Note**: antspyx has pre-built wheels for both x86_64 and arm64 (M1/M2/M3) architectures.

### Windows

On Windows, antspyx may have compatibility issues. If installation fails:

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Try standard installation
pip install -e .

# If antspyx fails, install without it
pip install -r requirements.txt --no-deps
# Then install dependencies one by one, skipping antspyx
```

**Note**: You may need [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) if any packages need to be built from source.

### Linux

Linux installation should work smoothly with the standard approach:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
```

For older distributions, ensure you have:
- GCC >= 7.0 (if building from source)
- System libraries: `python3-dev`, `build-essential`

On Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev build-essential
```

## Docker Usage (Detailed)

### Building the Docker Image

If you want to build the image yourself (instead of using docker-compose):

```bash
# Build the image
docker build -t linum/m2m:latest .

# Run the Streamlit web interface
docker run -d \
  --name m2m \
  -p 8501:8501 \
  -v $(pwd)/data/input:/data/input:ro \
  -v $(pwd)/data/output:/data/output:rw \
  linum/m2m:latest

# View logs
docker logs -f m2m

# Stop and remove container
docker stop m2m
docker rm m2m
```

### Running Python Scripts with Docker

```bash
# Run a Python script
docker run --rm \
  -v $(pwd)/data/input:/data/input:ro \
  -v $(pwd)/data/output:/data/output:rw \
  -v $(pwd)/my_script.py:/app/my_script.py:ro \
  linum/m2m:latest \
  python /app/my_script.py

# Interactive Python session
docker run --rm -it \
  -v $(pwd)/data:/data \
  linum/m2m:latest \
  python

# Bash shell access
docker run --rm -it \
  -v $(pwd)/data:/data \
  linum/m2m:latest \
  bash
```

### Docker Volume Management

The docker-compose setup creates persistent volumes for cache and configuration:

```bash
# List volumes
docker volume ls

# Inspect a volume
docker volume inspect m2m_m2m-cache

# Remove volumes (clears cache)
docker-compose down -v
```

### Docker Resource Management

Docker containers are isolated and resource-limited by default. For large datasets:

```bash
# Run with more memory (example: 8GB)
docker run --memory="8g" -p 8501:8501 linum/m2m:latest

# Check container resource usage
docker stats m2m
```

### Updating the Docker Image

When m2m is updated:

```bash
# Rebuild the image
docker-compose build --no-cache

# Restart with new image
docker-compose up -d
```

## Troubleshooting

### NumPy Version Conflicts

The Allen SDK requires numpy < 1.24. If you encounter numpy version conflicts:

```bash
# Explicitly install compatible numpy version
pip install "numpy>=1.23,<1.24"
```

This constraint is already in [requirements.txt](requirements.txt), but you may need to force reinstall if you had a different numpy version.

### AllenSDK Installation Issues

If AllenSDK fails to install:

1. Ensure you're using Python 3.9-3.12 (Python 3.13+ is not yet supported)
2. Check your numpy version: `pip show numpy`
3. Try installing AllenSDK separately:

```bash
pip install "numpy>=1.23,<1.24"
pip install allensdk>=2.16.0
```

### antspyx Installation Issues

antspyx can be challenging to install on some platforms. Solutions:

1. **Windows**: antspyx may not have wheels for your platform. You can skip it:
   ```bash
   # The platform marker in requirements.txt already handles this
   pip install -e .  # Will skip antspyx on Windows automatically
   ```

2. **Build from source issues**: If wheels aren't available, antspyx may try to build from source and fail. Install via conda instead:
   ```bash
   conda install -c conda-forge antspyx
   ```

3. **Last resort**: Install m2m without antspyx (ANTs features will be unavailable):
   ```bash
   # Edit requirements.txt to comment out antspyx line
   pip install -e .
   ```

### Python Version Issues

If you don't have Python 3.11 installed:

**macOS** (using Homebrew):
```bash
brew install python@3.11
python3.11 -m venv .venv
```

**Windows** (using Python installer):
- Download Python 3.11 from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Use `py -3.11 -m venv .venv` to create the environment

**Linux** (using package manager):
```bash
# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Fedora/RHEL
sudo dnf install python3.11

# Arch
sudo pacman -S python311
```

**Using Conda** (all platforms):
```bash
conda create -n m2m python=3.11
conda activate m2m
```

## Verifying Installation

After installation, verify everything works:

```bash
# Activate your environment first
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
# or: conda activate m2m

# Test import
python -c "import m2m; import numpy; import allensdk; print('Success!')"

# Check version
python -c "import m2m; print('m2m version:', m2m.version.VERSION)"
```

Optional: Test antspyx (may fail on Windows):
```python
python -c "import antspyx; print('antspyx available')"
```

## Development Installation

For contributing to m2m development:

```bash
# Install with development dependencies
pip install -r requirements-dev.txt

# This installs:
# - All base requirements (from requirements.txt)
# - Testing tools (pytest, pytest-cov, pytest-mock)
# - Code quality tools (black, flake8, mypy, pylint)
# - Documentation tools (from docs/requirements.txt)
# - Jupyter for notebooks

# Run tests
pytest

# Format code
black m2m/

# Type checking
mypy m2m/
```

## Dependency Structure

All dependencies are managed through a single source of truth:

```
requirements.txt           ← Single source of truth for package dependencies
    ↑
    ├── pip install -e .   (via setup.py reading requirements.txt)
    ├── requirements-dev.txt (includes requirements.txt + dev tools)
    └── .readthedocs.yaml  (installs requirements.txt + docs/requirements.txt)

docs/requirements.txt      ← Sphinx-only dependencies (for ReadTheDocs)
```

This means:
- ✅ Update dependencies in ONE place ([requirements.txt](requirements.txt))
- ✅ No duplication across files
- ✅ Consistent versions everywhere
- ✅ Easier maintenance

## Updating Dependencies

To update to newer compatible versions:

```bash
# Activate your environment
source .venv/bin/activate  # or conda activate m2m

# Update pip itself
pip install --upgrade pip

# Upgrade all packages
pip install --upgrade -r requirements.txt
```

To update specific packages:
```bash
pip install --upgrade numpy pandas scipy
```

## Uninstalling

To remove the m2m package and environment:

**Using venv**:
```bash
# Deactivate environment
deactivate

# Remove the virtual environment directory
rm -rf .venv  # or on Windows: rmdir /s .venv
```

**Using conda**:
```bash
conda deactivate
conda env remove -n m2m
```

## Common Issues and Solutions

### Issue: "No module named 'numpy'" during installation

**Cause**: Build dependencies not available during setup.

**Solution**: Install build dependencies first:
```bash
pip install --upgrade pip setuptools wheel
pip install "numpy>=1.23,<1.24" "cython>=0.29"
pip install -e .
```

### Issue: Build failures on Windows

**Solution**: Install Visual C++ Build Tools:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"

### Issue: Permission denied errors

**Solution**: Don't use `sudo` with pip. Use a virtual environment instead:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Issue: SSL certificate errors

**Solution**: Upgrade pip and certifi:
```bash
pip install --upgrade pip certifi
```

### Issue: Out of memory during installation

**Solution**: Install without caching:
```bash
pip install -e . --no-cache-dir
```

Or install large packages one at a time:
```bash
pip install numpy scipy pandas
pip install -e .
```

### Docker-Specific Issues

#### Issue: Port 8501 already in use

**Solution**: Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "8502:8501"  # Use port 8502 instead
```

#### Issue: Permission denied errors with volumes

**Cause**: The container runs as user ID 1000, which may not match your user ID.

**Solution on Linux**:
```bash
# Change ownership of data directories
sudo chown -R 1000:1000 data/
```

**Solution on macOS/Windows**: Docker Desktop handles this automatically.

#### Issue: Container keeps restarting

**Solution**: Check the logs:
```bash
docker-compose logs -f m2m
```

Common causes:
- Port already in use
- Memory limit too low
- Missing dependencies (rebuild with `--no-cache`)

#### Issue: Cannot access Streamlit interface

**Solution**:
1. Check container is running: `docker ps`
2. Check logs: `docker-compose logs m2m`
3. Try accessing: `http://localhost:8501`
4. On some systems, use `http://127.0.0.1:8501` instead

#### Issue: Docker build fails

**Solution**:
```bash
# Clear Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

#### Issue: Slow performance in Docker

**Cause**: Volume mounting can be slow on macOS/Windows.

**Solution**:
- Use Docker volumes instead of bind mounts for better performance
- Increase Docker Desktop resources (CPU/Memory) in settings
- On macOS, consider using VirtioFS (in Docker Desktop settings)

## Getting Help

If you continue to experience issues:

1. Check the [documentation](https://m2m.readthedocs.io/)
2. Search [existing issues](https://github.com/linum-uqam/m2m/issues)
3. Open a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - pip version (`pip --version`)
   - Full error message
   - Output of `pip list` in your environment

## Sources

- [antspyx PyPI](https://pypi.org/project/antspyx/)
- [ANTsPy Installation Guide](https://github.com/ANTsX/ANTsPy/wiki/Installing-ANTsPy)
- [AllenSDK Installation Guide](https://allensdk.readthedocs.io/en/stable/install.html)
