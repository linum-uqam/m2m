import streamlit as st
import subprocess
from pathlib import Path

st.title('Compute Affine Transformation Matrix')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_compute_transform_matrix.html')
st.write("Please upload the input files and set the arguments for the script:")

# Reference Image Path
#ref_path = st.file_uploader('Upload reference Image (.nii/.nii.gz)', type=([".nii",".nii.gz"]))
ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
if ref :
    ref_path = Path(ref.name)
    ref_path.write_bytes(ref.getvalue())

# Output Matrix Path
out_path = st.text_input('Enter output Matrix Path (/path/to/output.mat)')

# Resolution
allen_res = st.radio('Select Allen resolution (microns)', [25, 50, 100])

# User Resolution
user_res = st.number_input('Enter User resolution (microns)', value=0, step=1)

# Button to run script
if st.button('Compute Affine Transformation Matrix'):
    command = ['python3', 'scripts/m2m_compute_transform_matrix.py', str(ref_path), str(out_path), str(allen_res), str(user_res)]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        st.success("Matrix {} downloaded successfully".format(out_path))
    except subprocess.CalledProcessError as e:
        st.error(e.stderr)
