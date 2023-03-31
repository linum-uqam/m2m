import streamlit as st
import subprocess
from pathlib import Path

# Page configuration
st.set_page_config(page_title='M2M Download Template', page_icon=":mouse:")

st.title('Download Allen Mouse Brain Template')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_download_template.html')

# Output filename
output_filename = st.text_input('Enter path to output filename (allen_template_res.nii.gz)')

# Template resolution
allen_resolutions = [10, 25, 50, 100]
resolution = st.radio('Select Allen resolution (microns)', allen_resolutions)

# Apply transform to align the volume to RAS+ instead of relying only on the volume metadata
apply_transform = st.checkbox('Apply transform to align the volume to RAS+')

# Button to download template
if st.button('Download Template'):
    # Prepare the output directory
    output = Path(output_filename)
    output.parent.mkdir(exist_ok=True, parents=True)
    
    # Run script as subprocess
    command = ['python3', 'scripts/m2m_download_template.py', str(output), '-r', str(resolution)]
    if apply_transform:
        command.append('--apply_transform')
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        st.success("Template downloaded successfully.")
    except subprocess.CalledProcessError as e:
        st.error(e.stderr)
