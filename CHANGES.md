# Changelog

## Recent Improvements

### Installation & Dependencies
- **Fixed dependency conflicts**: Resolved numpy version conflicts with AllenSDK (requires numpy<1.24)
- **Simplified installation**: Removed conda dependency, now uses standard pip + venv
- **Added pyproject.toml**: Modern Python packaging configuration (PEP 621)
- **Single source of truth**: All dependencies managed in requirements.txt

### Docker Support
- **Added Docker containerization**: Zero-setup installation option
- **Pre-built images on Docker Hub**: Automatically published at [linumuqam/m2m](https://hub.docker.com/r/linumuqam/m2m)
- **CI/CD automation**: GitHub Actions builds and publishes images on every release
- **Fast builds**: Uses official `antsx/ants` base image to avoid long compilation times
- **Easy script execution**: Mount scripts/ directory for running m2m tools
- **Web interface**: Streamlit app ready out-of-the-box at http://localhost:8501

### Cross-Platform Support
- **Python 3.9-3.12 support**: Works across all major Python versions (3.11 recommended)
- **Platform markers**: Proper handling of platform-specific dependencies like antspyx
- **Tested on**: Linux, macOS (Intel/ARM), Windows (limited antspyx support)

### Documentation
- **Simplified documentation structure**: Removed redundant files, ReadTheDocs is the main documentation source
- **Markdown conversion**: Converted Sphinx docs from reStructuredText (.rst) to Markdown (.md)
- **Streamlined README**: Focused on quick start with clear pointers to full documentation
- **Updated installation guides**: Comprehensive Docker and local installation instructions

---

For detailed documentation, see https://m2m.readthedocs.io/
