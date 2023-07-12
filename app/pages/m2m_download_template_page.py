import streamlit as st
import subprocess
from pathlib import Path
import tempfile

# Page configuration
st.set_page_config(page_title='M2M Download Template', page_icon=":mouse:")

st.title('M2M Download Template')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_download_template.html')
st.write('Download Allen Mouse Brain Template')

# Step 1: Select template resolution
st.subheader('Step 1: Select template resolution')
resolution = st.radio('Allen resolution (microns)', [10, 25, 50, 100])

# Step 3: Download template
st.subheader('Step 2: Download template')
if st.button('Download template'):
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define the output filename
        output_filename = Path(temp_dir) / f'allen_template_{resolution}.nii.gz'
        # Run script as subprocess
        command = ['python3', 'scripts/m2m_download_template.py', str(output_filename), '-r', str(resolution)]
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success("Template downloaded successfully.")
            # Download the file
            with open(output_filename, 'rb') as f:
                file_bytes = f.read()
                st.download_button(
                    label="Save template", 
                    data=file_bytes, 
                    file_name=output_filename.name, 
                    mime="application/x-gzip"
                )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)