import streamlit as st
import subprocess

st.title('Compute Affine Transformation Matrix')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_compute_transform_matrix.html')

# Reference Image Path
ref_path = st.text_input('Enter reference Image Path (/path/to/reference.nii.gz)')

# Output Matrix Path
out_path = st.text_input('Enter output Matrix Path (/path/to/output.mat)')

# Resolution
resolution = st.selectbox('Select Allen resolution (microns)', [25, 50, 100])

# User Resolution
user_res = st.number_input('Enter User resolution', value=0, step=1)

# Button to run script
if st.button('Compute Affine Transformation Matrix'):
    command = ['python', 'scripts/m2m_compute_transform_matrix.py', ref_path, out_path, str(resolution), str(user_res)]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        st.success(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error(e.stderr)
