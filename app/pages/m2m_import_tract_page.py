import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
import tempfile
import zipfile

# Page configuration
st.set_page_config(page_title='M2M Import Tract', page_icon=':mouse:')
st.title('M2M Import Tract')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_import_tract.html')
st.write('Download streamlines from Allen Mouse Brain Connectivity Atlas and combine them into a single tractogram.')

# Step 1: Upload reference file and matrix file
st.subheader('Step 1: Upload reference file and matrix file') 
ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
mat = st.file_uploader("Matrix file (mat):", type=["mat"])

# Step 2: Select Allen resolution
st.subheader('Step 2: Select resolution)')
res = st.radio('Resolution', [25, 50, 100])

# Step34: Set Experiment IDs
st.subheader('Step 3: Set Experiment IDs')
ids_type = st.radio('IDs Type', ['CSV File', 'Manual'])
if ids_type == 'CSV File':
    ids_csv = st.file_uploader('CSV File', type=['csv'])
    if ids_csv:
        ids = pd.read_csv(ids_csv)
        in_ids = ids['id'].tolist()
else:
    in_ids = st.text_input('Experiment IDs (separated by spaces)').split()

# Step 4: Run Script
st.subheader('Step 4: Run Script')
if st.button('Run'):
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the reference image and the matrix in the tempdir
        ref_path = Path(tempdir) / Path(ref.name).name
        with open(ref_path, 'wb') as f:
            f.write(ref.getvalue())
        mat_path = Path(tempdir) / Path(mat.name).name
        with open(mat_path, 'wb') as f:
            f.write(mat.getvalue())
        out_tract = "tract.trk"
        cmd = ['python3', 'scripts/m2m_import_tract.py', str(out_tract), str(mat_path), str(ref_path), str(res)]
        if ids_type == 'CSV File':
            cmd.extend(['--ids_csv', str(ids_csv.name)])
        else:
            cmd.extend(['--ids'] + str(in_ids))
        try:
            result = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success("Tract imported successfully")
            # Download the output tract
            st.subheader('Step 5: Download tract')
            with open(Path(tempdir) / out_tract, 'rb') as f:
                trk_bytes = f.read()
                st.download_button(
                    label='Download tract',
                    data=trk_bytes,
                    file_name=out_tract,
                    mime='application/octet-stream'
                )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
