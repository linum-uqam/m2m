import streamlit as st
import subprocess
import scipy.io as sio
import tempfile
import sys
from pathlib import Path

# Page configuration
st.set_page_config(page_title="M2M Compute Transform Matrix", page_icon=":mouse:")

st.title('Compute Affine Transformation Matrix')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_compute_transform_matrix.html')
st.write("Please upload the input files and set the arguments for the script:")

# Reference image
ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
if ref:
    ref_path = Path(ref.name)
    ref_bytes = ref.getvalue()

# Output matrix
out_mat = st.text_input('Enter output matrix name (without file extension)')
mat = "{}.mat".format(out_mat)

# Resolution
allen_res = st.radio('Select allen resolution (microns)', [25, 50, 100])

# User resolution
user_res = st.number_input('Enter user resolution (microns)', value=0, step=1)

# Run script
if st.button('Compute Affine Transformation Matrix'):
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the reference image in the tempdir
        ref_path = Path(tempdir) / ref_path.name
        with open(ref_path, 'wb') as f:
            f.write(ref_bytes)

        # Build the command to run the script
        command = ['python3', 'scripts/m2m_compute_transform_matrix.py', str(ref_path), str(Path(tempdir) / mat), str(allen_res), str(user_res)]

        # Run the command
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success("Matrix {} computation completed successfully".format(mat))

            # Download the output matrix
            with open(Path(tempdir) / mat, 'rb') as f:
                matrix_bytes = f.read()
            st.download_button(
                label="Download matrix",
                data=matrix_bytes,
                file_name=mat,
                mime="application/octet-stream"
            )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
