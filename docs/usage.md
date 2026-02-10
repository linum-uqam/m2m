# Usage

## Web App (Discovering m2m)

The m2m toolkit provides a user-friendly Streamlit web interface for discovering its functionalities.

### Using Docker (Recommended)

```bash
docker-compose up
# Access at http://localhost:8501
```

### Using Local Installation

```bash
source .venv/bin/activate  # or: conda activate m2m
streamlit run app/m2m_main_page.py
# Click the link to open the Streamlit Web App
```

```{note}
The Streamlit Web App is designed for discovering m2m's functionalities. 
For large images (exceeding 200 MB) or advanced usage, we recommend using the command line interface.
```

## Command Line (Advanced Usage)

Here are examples of typical command line usage.

### Using Docker

All m2m scripts are available in the Docker container. You can run them by mounting your scripts directory:

```bash
docker run --rm \
  -v $(pwd)/scripts:/scripts:ro \
  -v $(pwd)/data:/data:rw \
  linum/m2m:latest \
  python /scripts/m2m_download_template.py allen_template_100.nii.gz -r 25
```

### Using Local Installation

Make sure your virtual environment is activated:

```bash
source .venv/bin/activate  # or: conda activate m2m
```

### Step 1 - Download a User-Space Reference Image

* Download an Allen mouse brain template at 100 microns (up to 10 microns):

```bash
m2m_download_template.py allen_template_100.nii.gz -r 25
```

* Download an Allen mouse brain annotation at 100 microns (up to 10 microns):

```bash
m2m_download_annotation.py allen_annotation_100.nii.gz labels.txt -r 25
```

### Step 2 - Compute a Transform Matrix

Compute the transform matrix `transform_50.mat` at 50 microns, 
given a user-space reference volume `reference.nii.gz` at 100 microns:

```bash
m2m_compute_transform_matrix.py reference.nii.gz transform_50.mat 50
```

```{note}
A transformation matrix for a specific resolution is valid only for that specific resolution.
If you want to import data (Step 3) with another resolution, compute another matrix.
```

### Step 3 - Example Use Cases

With your reference image (e.g., `reference.nii.gz`) and 
your resolution-specific transformation matrix (e.g., `transform_50.mat`), you can:

* Import the projection density from experiment id `100140756`:

```bash
m2m_import_proj_density.py --id 100140756 reference.nii.gz transform_50.mat 50
```

* Find crossing ROIs based on two injection positions:

  - First injection: `(132,133,69)`
  - Second injection: `(143,94,69)`
  - Threshold: 0.07

```bash
m2m_crossing_finder.py transform_50.mat reference.nii.gz 50 \
  --red 132 133 69 --green 143 94 69 --injection --threshold 0.07
```

* Find 5 experiment IDs given an injection position `(132,133,69)`:

```bash
m2m_experiments_finder.py 50 transform_50.mat reference.nii.gz \
  experiments_ids.csv 132 133 69 --injection --nb_of_exps 5
```

### Getting Help

Display help for any script:

```bash
m2m_compute_transform_matrix.py --help
```

Or consult the Scripts page in this documentation for detailed information about each tool.

## Using m2m as a Python Library

You can also use m2m directly in your Python code:

```python
import m2m
# Access m2m modules and functions
# See API documentation for available functions
```

Example workflow in Python:

```python
import m2m
from m2m import template, annotation

# Your analysis code here
# See API documentation for detailed examples
```
