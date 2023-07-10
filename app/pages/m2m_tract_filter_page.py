import streamlit as st
import subprocess
import pandas as pd
from pathlib import Path
import tempfile

# Page configuration
st.set_page_config(page_title='M2M Tract Filter', page_icon=':mouse:')
st.title('M2M Tract Filter')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_tract_filter.html')
st.write('Extract a bundle of streamlines from an aligned tractogram.')

# Step 1: Upload input tractogram
st.subheader('Step 1: Upload input tractogram')
in_tract = st.file_uploader("Input tractogram (trk):", type=["trk"])

# Step 2: Upload reference file
st.subheader('Step 2: Upload reference file')
reference = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])

# Step 3: Set ROI filters
st.subheader('Step 3: Set ROI filters')
roi_type = st.radio('ROI Type', ['Sphere', 'Binary Mask'])
if roi_type == 'Sphere':
    center = st.text_input('Center coordinates (x y z) separated by space:')
    radius = st.number_input('Radius:', value=1.0, step=0.1)
    download_sphere = st.checkbox('Download spherical mask')
    if download_sphere:
        sphere_path = st.text_input('Spherical mask path:')
else:
    mask = st.file_uploader('Binary mask (nifti):', type=['nii', 'nii.gz'])

# Step 4: Run Script
st.subheader('Step 4: Run Script')
if st.button('Run'):
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the input tractogram
        in_tract_path = Path(tempdir) / Path(in_tract.name).name
        with open(in_tract_path, 'wb') as f:
            f.write(in_tract.getvalue())

        # Save the reference file
        ref_path = Path(tempdir) / Path(reference.name).name
        with open(ref_path, 'wb') as f:
            f.write(reference.getvalue())

        # Prepare the command
        cmd = ['python3', 'scripts/m2m_tract_filter.py', str(in_tract_path), 'filtered_tract.trk', str(ref_path)]

        if roi_type == 'Sphere':
            cmd.extend(['--sphere', '--center', center, '--radius', str(radius)])

            if download_sphere:
                cmd.extend(['--download_sphere', sphere_path])
        else:
            mask_path = Path(tempdir) / Path(mask.name).name
            with open(mask_path, 'wb') as f:
                f.write(mask.getvalue())
            cmd.extend(['--in_mask', str(mask_path)])

        try:
            result = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
            st.success("Tract filtering completed successfully")

            # Download the filtered tract
            st.subheader('Step 5: Download filtered tract')
            with open(Path(tempdir) / 'filtered_tract.trk', 'rb') as f:
                trk_bytes = f.read()
                st.download_button(
                    label='Download filtered tract',
                    data=trk_bytes,
                    file_name='filtered_tract.trk',
                    mime='application/octet-stream'
                )
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
