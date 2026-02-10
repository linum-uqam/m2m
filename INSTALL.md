# Installation Guide for m2m

This guide provides detailed installation instructions for the m2m (Meso to Macro) toolkit across different platforms.

## Prerequisites

- **Python 3.9, 3.10, 3.11, or 3.12** (Python 3.11 recommended for best compatibility)
- Python 3.13+ is **not supported** due to dependency constraints
- **Git** (for cloning the repository)
- **pip** (usually comes with Python)

## Quick Start (Recommended)

The recommended installation method uses Python's built-in `venv` module to create an isolated environment:

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

## Alternative: Using Conda (Optional)

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
