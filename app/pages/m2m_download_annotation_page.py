import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import zipfile

# Page configuration
st.set_page_config(page_title='M2M Download Annotation', page_icon=":mouse:")
st.title('M2M Download Annotation')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_download_annotation.html')
st.write('Download Allen Mouse Brain Annotation')

# Step 1: Select Annotation resolution
st.subheader('Step 1: Select Annotation resolution')
resolution = st.radio('Allen resolution (microns)', [10, 25, 50, 100])

# Step 2: Select Annotation resolution
st.subheader('Step 2: Select Labels format')
label = st.radio('Labels format', ['.txt', '.label (ITKSnap)'])

# Step 3: Download Annotation
st.subheader('Step 3: Download Annotation')
if st.button('Download Annotation'):
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define the output filename
        output_filename = Path(temp_dir) / \
            f'allen_annotation_{resolution}.nii.gz'
        if label == '.txt':
            output_labels = Path(temp_dir) / f'allen_annotation_labels.txt'
        else:
            output_labels = Path(temp_dir) / f'allen_annotation_labels.label'
        # Run script as subprocess
        command = ['python3', 'scripts/m2m_download_annotation.py',
                   str(output_filename), str(output_labels), '-r', str(resolution)]
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            st.success("Annotation downloaded successfully.")
            # Download the file
            # Create a ZIP archive of the files
            zip_path = Path(temp_dir) / 'annotation_files.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(output_filename, arcname=output_filename.name)
                zip_file.write(output_labels, arcname=output_labels.name)

            # Download the ZIP file using st.download_button
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
                st.download_button(label='Save Annotation and Labels', data=zip_data,
                                   file_name='annotation_files.zip', mime='application/zip')

        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
