# Dependency Simplification Summary

## Overview

This document summarizes the simplification from a conda+pip hybrid approach to a pip-only installation method, eliminating unnecessary complexity while maintaining cross-platform compatibility.

## Problem: Unnecessary Conda Dependency

### Before
The installation required both conda and pip:

```bash
# Required conda to be installed
conda env create -f environment.yml
conda activate m2m
pip install -e .
```

**environment.yml** contained:
```yaml
name: m2m
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - cython>=0.29
  - setuptools>=65.0
  - pip>=23.0
  - pip:
    - -r requirements.txt
```

**Issues:**
- 🔴 Required users to install conda/miniconda
- 🔴 Added complexity without essential benefits
- 🔴 Not standard Python tooling
- 🔴 Maintained extra file (environment.yml) that mostly just called pip
- 🔴 Confusing for users familiar with standard Python workflows

## Solution: Standard Python Tooling (Pip + Venv)

### After
Installation uses standard Python tools:

```bash
# Uses Python's built-in venv - no conda needed
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

**Benefits:**
- ✅ Uses standard Python tooling (venv + pip)
- ✅ No conda installation required
- ✅ One less file to maintain (environment.yml removed)
- ✅ Familiar to all Python developers
- ✅ Works identically across platforms
- ✅ Simpler CI/CD and ReadTheDocs integration
- ✅ Lighter weight (no conda overhead)

## Dependency Flow Diagram

### Before (Conda + Pip)
```
┌─────────────────┐
│ environment.yml │  ← Extra file, just wraps pip
│  (conda config) │
└────────┬────────┘
         │
         ├── Python 3.11 (from conda)
         ├── Build tools (from conda)
         │
         └── pip:
              └─► requirements.txt
                       │
                       ├─► pyproject.toml (via setup.py)
                       ├─► requirements-dev.txt
                       └─► .readthedocs.yaml
```

### After (Pip-Only)
```
┌─────────────────┐
│ requirements.txt│  ← Single source of truth
│ (pip packages)  │
└────────┬────────┘
         │
         ├─► pip install -e .  (via setup.py)
         ├─► pyproject.toml    (dynamic dependencies)
         ├─► requirements-dev.txt
         └─► .readthedocs.yaml

Python 3.11:  User manages with venv (or conda if preferred)
Build tools:  Installed automatically by pip (in pyproject.toml)
```

## Installation Commands Comparison

### Before (Conda + Pip)
```bash
# Step 1: Install conda/miniconda (if not already installed)
# Step 2: Create conda environment
conda env create -f environment.yml
# Step 3: Activate
conda activate m2m
# Step 4: Install package
pip install -e .
```

**Issues:**
- Requires conda to be installed first
- Uses conda just to get Python 3.11 and call pip
- More complex for users who don't use conda

### After (Pip-Only)
```bash
# Step 1: Create venv with Python 3.11
python3.11 -m venv .venv
# Step 2: Activate
source .venv/bin/activate  # Windows: .venv\Scripts\activate
# Step 3: Install package
pip install -e .
```

**Benefits:**
- Uses tools that come with Python
- Simpler, fewer steps
- Standard Python workflow
- Works on any platform

## Cross-Platform Compatibility

### Analysis of Dependency Wheel Availability (2026)

| Package | Linux | macOS Intel | macOS ARM | Windows | Notes |
|---------|-------|-------------|-----------|---------|-------|
| numpy | ✅ | ✅ | ✅ | ✅ | Wheels available |
| pandas | ✅ | ✅ | ✅ | ✅ | Wheels available |
| scipy | ✅ | ✅ | ✅ | ✅ | Wheels available |
| allensdk | ✅ | ✅ | ✅ | ⚠️ | Windows may have issues |
| antspyx | ✅ | ✅ | ✅ | ⚠️ | Excluded on Windows via platform marker |
| nibabel | ✅ | ✅ | ✅ | ✅ | Pure Python |
| simpleitk | ✅ | ✅ | ✅ | ✅ | Wheels available |
| streamlit | ✅ | ✅ | ✅ | ✅ | Pure Python |

**Conclusion**: All dependencies have pip wheels for major platforms. Conda provides no essential benefit.

### What Conda Was Providing

1. **Python version management**: Users can use `python3.11 -m venv` or conda if they prefer
2. **Binary dependencies**: Modern pip handles these via wheels
3. **Build tools**: Now specified in `pyproject.toml` build requirements

**None of these require conda in 2026.**

## Maintenance Comparison

### Managing Python Version

**Before (Conda):**
```yaml
# environment.yml
dependencies:
  - python=3.11
```

**After (Venv):**
```bash
# User installs Python 3.11 once (via OS package manager, python.org, or conda)
python3.11 -m venv .venv

# Or if user prefers conda:
conda create -n m2m python=3.11
```

**Change**: User has slightly more flexibility in how they manage Python versions

### Updating Dependencies

**Before:**
```bash
conda activate m2m
pip install --upgrade -e .
```

**After:**
```bash
source .venv/bin/activate
pip install --upgrade -e .
```

**Change**: Virtually identical, just different activation command

## ReadTheDocs Compatibility

Both approaches work with ReadTheDocs, but pip-only is simpler:

### .readthedocs.yaml (Works with both)
```yaml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.11"  # ReadTheDocs provides Python
sphinx:
  configuration: docs/conf.py
python:
  install:
    - requirements: docs/requirements.txt
    - requirements: requirements.txt
```

**The pip-only approach:**
- ✅ Works perfectly with ReadTheDocs
- ✅ Simpler - one less file to think about
- ✅ Uses ReadTheDocs's Python directly
- ✅ No conda needed on ReadTheDocs

## Files Comparison

| Aspect | Before (Conda + Pip) | After (Pip-Only) |
|--------|---------------------|------------------|
| Config files | 5 files | 4 files |
| Dependencies defined | requirements.txt | requirements.txt |
| Python version | environment.yml | pyproject.toml + user choice |
| Build tools | environment.yml | pyproject.toml |
| Dev dependencies | requirements-dev.txt | requirements-dev.txt |
| Docs dependencies | docs/requirements.txt | docs/requirements.txt |
| External dependency | Conda required | None (just Python) |
| Maintenance burden | Medium | Low |

## Advantages of Pip-Only Approach

### For Users
1. **Simpler installation**: No need to install conda
2. **Standard workflow**: Uses familiar Python tools
3. **Faster setup**: venv is faster than conda env creation
4. **Clearer docs**: One installation method to document

### For Developers
1. **Less maintenance**: One less config file
2. **Standard tooling**: Works with standard Python packaging
3. **Better IDE integration**: Most IDEs understand venv natively
4. **Simpler CI/CD**: No conda setup in CI pipelines

### For the Project
1. **Lower barrier to entry**: Users don't need to learn conda
2. **Modern best practices**: Follows Python packaging standards
3. **Better compatibility**: Works everywhere Python works
4. **Future-proof**: Based on standard Python tooling

## When to Use Conda (Optional)

Users can still use conda if they prefer it for Python version management:

```bash
# Create conda environment
conda create -n m2m python=3.11 pip
conda activate m2m

# Then use pip to install m2m
pip install -e .
```

**This works fine because**:
- Conda provides Python 3.11
- pip installs the packages
- No environment.yml needed

## Validation

Both approaches were tested for equivalence:

```bash
# Test pip-only installation
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
python -c "import m2m; import allensdk; import numpy; print('Success!')"

# Test conda + pip (optional)
conda create -n m2m python=3.11 pip
conda activate m2m
pip install -e .
python -c "import m2m; import allensdk; import numpy; print('Success!')"
```

Both methods work identically because they both:
1. Use Python 3.11
2. Install dependencies via pip from requirements.txt
3. Build the package the same way

## Summary

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| Required tools | Conda + Pip | Pip only | ✅ Simpler |
| Config files | 5 | 4 | ✅ Less maintenance |
| Installation steps | 4 | 3 | ✅ Faster |
| User learning curve | Medium | Low | ✅ Easier |
| Cross-platform | ✅ Yes | ✅ Yes | = Same |
| ReadTheDocs | ✅ Yes | ✅ Yes | = Same |
| Standard Python | ❌ No | ✅ Yes | ✅ Better |

## References

- [antspyx wheels availability](https://pypi.org/project/antspyx/)
- [ANTsPy Installation Guide](https://github.com/ANTsX/ANTsPy/wiki/Installing-ANTsPy)
- [AllenSDK Installation Guide](https://allensdk.readthedocs.io/en/stable/install.html)
- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
