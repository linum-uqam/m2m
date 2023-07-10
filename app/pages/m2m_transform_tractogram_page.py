import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
import tempfile

# Page configuration
st.set_page_config(page_title='M2M Transform Tractogram', page_icon=':mouse:')
st.title('M2M Transform Tractogram')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_transform_tractogram.html')
st.write('Transform the Allen tractogram (Wildtype, RAS@50um) to the User\'s Data Space (UDS).')

# Step 1: Upload transform matrix file
st.subheader('Step 1: Upload transform matrix file')
file_mat = st.file_uploader("Transform matrix file (mat):", type=["mat"])

# Step 2: Upload reference file
st.subheader('Step 2: Upload reference file')
reference = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])

# Step 3: Run Script
st.subheader('Step 3: Run Script')
if st.button('Run'):
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the transform matrix file
        mat_path = Path(tempdir) / Path(file_mat.name).name
        with open(mat_path, 'wb') as f:
            f.write(file_mat.getvalue())

        # Save the reference file
        ref_path = Path(tempdir) / Path(reference.name).name
        with open(ref_path, 'wb') as f:
            f.write(reference.getvalue())

        # Prepare the command
        cmd = ['python3', 'scripts/m2m_transform_tractogram.py', 'transformed_tractogram.trk', str(mat_path), str(ref_path)]

        try:
            result = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
            st.success("Tractogram transformation completed successfully")

            # Download the transformed tractogram
            st.subheader('Step 4: Download transformed tractogram')
            with open(Path(tempdir) / 'transformed_tractogram.trk', 'rb') as f:
                trk_bytes = f.read()
                st.download_button(
                    label='Download transformed tractogram',
                    data=trk_bytes,
                    file_name='transformed_tractogram.trk',
                    mime='application/octet-stream'
                )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
