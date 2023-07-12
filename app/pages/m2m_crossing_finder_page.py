import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import zipfile

# Page configuration
st.set_page_config(page_title='M2M Crossing Finder', page_icon=':mouse:')
st.title('M2M Crossing Finder')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_crossing_finder.html')
st.write('Find crossing regions (ROIs) between Allen Mouse Brain Connectivity experiments.')

# Step 1: Upload transform matrix file
st.subheader('Step 1: Upload transform matrix file')
file_mat = st.file_uploader("Matrix file (mat):", type=["mat"])

# Step 2: Upload reference file
st.subheader('Step 2: Upload reference file')
reference = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])

# Step 3: Select Allen resolution
st.subheader('Step 3: Select resolution')
res = st.radio('Resolution (same as matrix)', [25, 50, 100])

# Step 4: Enter UDS voxel coordinates
st.subheader('Step 4: Enter UDS voxel coordinates')

coord_option = st.radio('Choose crossing study type:', ['2-color', '3-color'])

color_options = {'red': 'Red', 'green': 'Green', 'blue': 'Blue'}

if coord_option == '2-color':
    color_names = ['red', 'green']
else:
    color_names = ['red', 'green', 'blue']

coordinates = {}

for color_name in color_names:
    color_label = color_options[color_name]
    coordinates[color_name] = st.text_input(
        f'{color_label} coordinates (X Y Z) space separated', value='0 0 0').split()
    if len(coordinates[color_name]) != 3:
        st.error(
            f'Please enter all three coordinates (X, Y, Z) for the {color_label} color.')

# Step 5: Select search type
st.subheader('Step 5: Select search type')
search_type = st.radio(
    'Search Type:', ['Injection Coordinate Search', 'Spatial Search'])

# Step 6: Enter threshold
st.subheader('Step 6: Enter threshold')
threshold = st.number_input(
    'Threshold:', value=0.10, min_value=0.0, max_value=1.0, step=0.01)

dir = Path(tempfile.mkdtemp()) / f"crossing_files"

# Step 7: Run Script
st.subheader('Step 7: Find Crossing ROI(s)')
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
        cmd = ['python3', 'scripts/m2m_crossing_finder.py',
               str(mat_path), str(ref_path), str(res)]

        # Add UDS voxel coordinates
        cmd += ['--red'] + coordinates['red'] + \
            ['--green'] + coordinates['green']

        # Add optional blue coordinates
        if coord_option == '3-color':
            cmd += ['--blue'] + coordinates['blue']

        # Add search type and threshold
        if search_type == 'Injection Coordinate Search':
            cmd.append('--injection')
        else:
            cmd.append('--spatial')

        cmd += ['--threshold', str(threshold), '-d', str(dir)]

        try:
            result = subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            # Create a ZIP archive of the directory
            zip_path = Path(tempdir) / "data.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in Path(dir).rglob("*"):
                    zip_file.write(file, arcname=file.relative_to(dir))

            st.success("Crossing regions found successfully")
            st.subheader(
                'Step 8: Download Crossing ROIs and Merged Projection Maps')

            # Provide download link for the zip file
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()
                st.download_button(
                    label='Download Files',
                    data=zip_bytes,
                    file_name='output_crossing_files.zip',
                    mime='application/zip'
                )

        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
