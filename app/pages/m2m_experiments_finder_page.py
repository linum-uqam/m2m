import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import pandas as pd

# Page configuration
st.set_page_config(page_title='M2M Experiments Finder', page_icon='🔍')
st.title('M2M Experiments Finder')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_experiments_finder.html')
st.write('Find experiments IDs in the Allen Mouse Brain Connectivity Atlas dataset')

# Step 1: Upload Matrix File
st.subheader('Step 1: Upload Matrix File')
mat = st.file_uploader('Matrix file (.mat)', type=["mat"])

# Step 2: Upload Reference Image
st.subheader('Step 2: Upload Reference Image')
ref = st.file_uploader('Reference image (nifti)', type=['nii', 'nii.gz'])

# Step 3: Set Resolution
st.subheader('Step 3: Set Resolution')
resolution = st.radio('Resolution (same as matrix)', [25, 50, 100])

# Step 4: Set Coordinates
st.subheader('Step 4: Set Coordinates (UDS-voxels)')
x = st.number_input('X-coordinate', value=0, step=1)
y = st.number_input('Y-coordinate', value=0, step=1)
z = st.number_input('Z-coordinate', value=0, step=1)

# Step 5: Search Type
st.subheader('Step 5: Search Type')
search_type = st.radio(
    'Search Type', ['Injection center', 'High signal region'])

# Step 6: Number of Experiments
st.subheader('Step 6: Number of Experiments')
nb_of_exps = st.number_input('Number of Experiments', value=1, step=1)

# Step 7: Run Script
st.subheader('Step 7: Find experiments')
if st.button('Find'):
    with tempfile.TemporaryDirectory() as tempdir:
        # Define the output filename
        output_filename = Path(tempdir) / f'experiments.csv'
        # Save the matrix file in the tempdir
        mat_path = Path(tempdir) / Path(mat.name).name
        with open(mat_path, 'wb') as f:
            f.write(mat.getvalue())
        # Save the reference image in the tempdir
        ref_path = Path(tempdir) / Path(ref.name).name
        with open(ref_path, 'wb') as f:
            f.write(ref.getvalue())
        # Run the script
        cmd = ['python3', 'scripts/m2m_experiments_finder.py', str(resolution), str(
            mat_path), str(ref_path), str(output_filename), str(x), str(y), str(z)]
        if search_type == 'Injection center':
            cmd.append('--injection')
        else:
            cmd.append('--spatial')
        cmd.append('--nb_of_exps')
        cmd.append(str(nb_of_exps))
        try:
            result = subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success('Experiments found successfully')
            # Download experiments
            st.subheader('Step 8: Download experiments ids')
            csv = pd.read_csv(output_filename)
            st.download_button(
                label="Save CSV",
                data=csv.to_csv(index=False).encode('utf-8'),
                file_name=output_filename.name,
                mime="text/csv"
            )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
