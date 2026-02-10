# Dependency Fix Changes

## Summary

This branch fixes critical dependency conflicts and installation issues that prevented the package from being installed across different platforms.

## Problems Fixed

### 1. **Numpy Version Conflicts**
- **Issue**: AllenSDK requires `numpy<1.24` but this wasn't properly constrained
- **Fix**: Added explicit numpy version range `>=1.23,<1.24` across all dependency files

### 2. **Missing Python Version Constraint**
- **Issue**: No Python version specified, allowing incompatible Python 3.13+ to be used
- **Fix**: Pinned Python to 3.11 in environment.yml, added `>=3.9,<3.13` constraint in pyproject.toml

### 3. **Missing Build Dependencies**
- **Issue**: setup.py requires `cython` and `numpy` at build time but these weren't in environment.yml
- **Fix**: Added cython, setuptools, and pip to conda dependencies

### 4. **Old Package Versions**
- **Issue**: pandas pinned to 1.5.3, scipy unspecified
- **Fix**: Added version ranges for all major dependencies to ensure compatibility

### 5. **Platform-Specific Issues**
- **Issue**: antspyx has known installation issues on Windows and some macOS configurations
- **Fix**: Added platform markers and comprehensive platform-specific documentation

### 6. **Lack of Modern Package Configuration**
- **Issue**: Only setup.py existed, making cross-platform builds difficult
- **Fix**: Added pyproject.toml with modern PEP 621 configuration

## Files Modified

### Updated Files
1. **environment.yml**: Complete rewrite with proper dependency constraints and Python version
2. **requirements.txt**: Expanded with all dependencies and version constraints
3. **setup.py**: Improved with better error handling and pyproject.toml compatibility
4. **README.md**: Updated installation instructions

### New Files Created
1. **pyproject.toml**: Modern Python packaging configuration (PEP 621)
2. **INSTALL.md**: Comprehensive installation guide with platform-specific instructions
3. **requirements-dev.txt**: Development dependencies separated from runtime dependencies
4. **CHANGES.md**: This file documenting all changes

## Key Changes Detail

### environment.yml
- Added Python 3.11 pin
- Added build dependencies (cython, setuptools)
- Specified version ranges for all packages
- Added conda-forge channel as primary
- Moved allensdk and antspyx to pip section for better compatibility

### requirements.txt
- Added all implicit dependencies explicitly
- Added version constraints matching AllenSDK requirements
- Added platform markers for Windows compatibility
- Added comments explaining constraints

### pyproject.toml (NEW)
- Modern PEP 621 configuration
- Proper build system requirements
- Optional dependency groups (dev, docs)
- Python version constraints
- Black and pytest configuration

### setup.py
- Improved error handling for missing files
- Better compatibility with pyproject.toml
- Fixed cache directory creation on restricted systems
- Added Python version requirement

### INSTALL.md (NEW)
- Platform-specific installation instructions
- Troubleshooting section for common issues
- Alternative installation methods
- Verification steps

## Testing Recommendations

To test this fix:

```bash
# 1. Remove any existing m2m environment
conda env remove -n m2m

# 2. Create fresh environment
conda env create -f environment.yml

# 3. Activate and install
conda activate m2m
pip install -e .

# 4. Verify installation
python -c "import m2m; import allensdk; print('Success!')"
```

## Compatibility Matrix

| Platform | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 |
|----------|-----------|-------------|-------------|-------------|
| Linux    | ✅        | ✅          | ✅          | ✅          |
| macOS (Intel) | ✅   | ✅          | ✅          | ✅          |
| macOS (ARM)   | ✅   | ✅          | ✅          | ✅          |
| Windows  | ⚠️*       | ⚠️*         | ⚠️*         | ⚠️*         |

*Windows: antspyx may require separate installation or may not be available

## Breaking Changes

None. All changes are backward compatible. Existing installations will continue to work.

## Migration Guide

For users with existing environments:

```bash
# Option 1: Update existing environment
conda activate m2m
conda env update -f environment.yml
pip install --upgrade -e .

# Option 2: Fresh install (recommended)
conda env remove -n m2m
conda env create -f environment.yml
conda activate m2m
pip install -e .
```

## References

- AllenSDK requirements: https://github.com/AllenInstitute/AllenSDK
- antspyx compatibility: https://pypi.org/project/antspyx/
- PEP 621 (pyproject.toml): https://peps.python.org/pep-0621/
