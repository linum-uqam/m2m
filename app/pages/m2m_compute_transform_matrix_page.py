import streamlit as st
import subprocess
import scipy.io as sio
import tempfile
import sys
from pathlib import Path

# Page configuration
st.set_page_config(page_title='M2M Compute Transform Matrix', page_icon=':matrix:')

st.title('Compute Affine Transformation Matrix')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_compute_transform_matrix.html')
st.write('Please upload the input files and set the arguments for the script:')

# Step 1: Upload reference image
st.subheader('Step 1: Upload reference image')
ref = st.file_uploader('Nifti image', type=['nii', 'nii.gz'])
if ref:
    ref_path = Path(ref.name)
    ref_bytes = ref.getvalue()

    # Step 2: Set output matrix name
    st.subheader('Step 2: Set output matrix name')
    out_mat = st.text_input('Name without file extension')

    if out_mat:

        # Step 3: Select Allen resolution
        st.subheader('Step 3&4: Select Allen&User resolutions (in microns)')
        allen_res = st.radio('Allen resolution', [25, 50, 100])
        # Step 4: Enter user resolution
        user_res = st.number_input('User resolution', value=0, step=1)
    
        if allen_res and user_res:

            # Step 5: Run the script
            st.subheader('Step 5: Compute affine transformation matrix')
            if st.button('Compute matrix'):
                with tempfile.TemporaryDirectory() as tempdir:
                    # Save the reference image in the tempdir
                    ref_path = Path(tempdir) / ref_path.name
                    with open(ref_path, 'wb') as f:
                        f.write(ref_bytes)
                    # Build the command to run the script
                    mat = '{}.mat'.format(out_mat)
                    command = ['python3', 'scripts/m2m_compute_transform_matrix.py', str(ref_path), str(Path(tempdir) / mat), str(allen_res), str(user_res)]
                    # Run the command
                    try:
                        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                        st.success('Matrix {} computation completed successfully'.format(mat))
                        # Download the output matrix
                        st.subheader('Step 6: Download affine transformation matrix')
                        with open(Path(tempdir) / mat, 'rb') as f:
                            matrix_bytes = f.read()
                        st.download_button(
                            label='Download matrix',
                            data=matrix_bytes,
                            file_name=mat,
                            mime='application/octet-stream'
                        )
                    except subprocess.CalledProcessError as e:
                        st.error(e.stderr)