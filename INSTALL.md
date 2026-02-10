# Installation Guide for m2m

This guide provides detailed installation instructions for the m2m (Meso to Macro) toolkit across different platforms.

## Prerequisites

- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Git (for cloning the repository)

## Quick Start (Recommended)

The recommended installation method uses conda to manage dependencies and ensure cross-platform compatibility:

```bash
# Clone the repository
git clone https://github.com/linum-uqam/m2m.git
cd m2m

# Create and activate the conda environment
conda env create -f environment.yml
conda activate m2m

# Install the package in development mode
pip install -e .
```

## Platform-Specific Notes

### macOS (Intel and Apple Silicon)

On Apple Silicon (M1/M2/M3) Macs, some packages may need to be installed through conda-forge for ARM64 compatibility:

```bash
# If you encounter issues with antspyx on Apple Silicon
conda env create -f environment.yml
conda activate m2m
conda install -c conda-forge antspyx
pip install -e .
```

### Windows

On Windows, antspyx may have compatibility issues. If installation fails:

```bash
# Create environment without antspyx
conda env create -f environment.yml
conda activate m2m

# Try installing antspyx separately
pip install antspyx

# If antspyx still fails, you can continue without it
# (some ANTs-related features will be unavailable)
pip install -e .
```

### Linux

Linux installation should work smoothly with the standard approach. For older distributions, ensure you have:

- GCC >= 7.0
- CMake >= 3.12 (if building from source)

## Troubleshooting

### NumPy Version Conflicts

The Allen SDK requires numpy < 1.24. If you encounter numpy version conflicts:

```bash
# Explicitly install compatible numpy version
pip install "numpy>=1.23,<1.24"
```

### AllenSDK Installation Issues

If AllenSDK fails to install:

1. Ensure you're using Python 3.9-3.12 (Python 3.13+ is not yet supported)
2. Try installing AllenSDK separately:

```bash
conda activate m2m
pip install allensdk==2.16.2
```

### antspyx Installation Issues

antspyx can be challenging to install on some platforms. Solutions:

1. **Preferred**: Install via conda-forge:
   ```bash
   conda install -c conda-forge antspyx
   ```

2. **Alternative**: Use pip with pre-built wheels (available for Python 3.9-3.12):
   ```bash
   pip install antspyx
   ```

3. **Last resort**: If all else fails, you can install m2m without antspyx (ANTs features will be unavailable)

### Python Version Issues

If you have a very new Python version (3.13+) that isn't supported yet:

```bash
# Create environment with specific Python version
conda create -n m2m python=3.11
conda activate m2m
# Then follow standard installation steps
```

## Verifying Installation

After installation, verify everything works:

```python
import m2m
import numpy as np
import pandas as pd
import allensdk
import antspyx  # May fail on Windows

print("m2m version:", m2m.version.VERSION)
print("Installation successful!")
```

## Development Installation

For contributing to m2m development:

```bash
# Install with development dependencies
conda env create -f environment.yml
conda activate m2m
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black m2m/
```

## Updating Dependencies

To update to newer compatible versions:

```bash
conda activate m2m
conda update --all
pip install --upgrade -e .
```

## Common Issues and Solutions

### Issue: "Package conflicts" during conda environment creation

**Solution**: Try creating the environment with `--force`:
```bash
conda env create -f environment.yml --force
```

Or remove the existing environment first:
```bash
conda env remove -n m2m
conda env create -f environment.yml
```

### Issue: Build failures on Windows

**Solution**: Install Visual C++ Build Tools:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"

### Issue: Out of memory during installation

**Solution**: Increase available memory or install packages individually:
```bash
conda env create -f environment.yml --no-default-packages
conda activate m2m
pip install -e . --no-cache-dir
```

## Getting Help

If you continue to experience issues:

1. Check the [documentation](https://m2m.readthedocs.io/)
2. Search [existing issues](https://github.com/linum-uqam/m2m/issues)
3. Open a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Full error message
   - Output of `conda list` in your m2m environment
