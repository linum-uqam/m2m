import streamlit as st
import subprocess
import tempfile
from pathlib import Path

# Page configuration
st.set_page_config(page_title='M2M Compute Transform Matrix',page_icon='🔢')
st.title('M2M Compute Transform Matrix')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_compute_transform_matrix.html')
st.write('Compute Affine Transformation Matrix')

# Step 1: Upload reference image
st.subheader('Step 1: Upload reference image')
ref = st.file_uploader('Nifti image', type=['nii', 'nii.gz'])

# Step 2: Select Allen & User resolutions (in microns)
st.subheader('Step 2: Select Allen & User resolutions (in microns)')
allen_res = st.radio('Allen resolution', [25, 50, 100])
user_res = st.number_input('User resolution', value=0, step=1)

# Step 3: Run the script
st.subheader('Step 3: Compute affine transformation matrix')
if st.button('Compute matrix') and ref and allen_res and user_res:
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the reference image in the tempdir
        ref_path = Path(tempdir) / ref.name
        with open(ref_path, 'wb') as f:
            f.write(ref.getvalue())
        # Build the command to run the script
        mat = 'matrix.mat'
        command = ['python3', 'scripts/m2m_compute_transform_matrix.py',
                   str(ref_path), str(Path(tempdir) / mat), str(allen_res), str(user_res)]
        # Run the command
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True)
            st.success('Matrix computation completed successfully')
            # Download the output matrix
            st.subheader('Step 4: Download affine transformation matrix')
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
