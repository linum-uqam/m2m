import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import zipfile
import pandas as pd

# Page configuration
st.set_page_config(page_title="M2M Import Projection Density", page_icon=":mouse:")
st.title("M2M Import Projection Density")

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_import_proj_density.html')
st.write("Import Allen Mouse Brain Connectivity Projection Density Map")

# Step 1: Choose an experiment id in the Allen Mouse Brain Connectivity Atlas dataset
st.subheader('Step 1: Choose an experiment id in the Allen Mouse Brain Connectivity Atlas dataset')
# Step 4: Set Experiment IDs
st.subheader('Step 4: Set Experiment IDs')
ids_type = st.radio('Choose one', ['Multiple ids (CSV File)', 'Single id (Manual)'])
if ids_type == 'Multiple ids (CSV File)':
    ids_csv = st.file_uploader('CSV File', type=['csv'])
    if ids_csv:
        ids_df = pd.read_csv(ids_csv)
        # Store the CSV file in the temporary directory
        temp_csv_path = Path(tempfile.mkdtemp()) / ids_csv.name
        ids_df.to_csv(temp_csv_path, index=False)
else:
    id_manual = st.number_input('Experiment ID', value=0, step=1)

dir = Path(tempfile.mkdtemp()) / f"output_files"

# Step 2: Upload reference file and matrix file
st.subheader('Step 2: Upload reference file and matrix file') 
ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
mat = st.file_uploader("Matrix file (mat):", type=["mat"])

# Step 3: Choose which files to download (file flags)
st.subheader('Step 3: Choose which files to import')
map = st.checkbox("Projection density map of the experiment (.nii.gz)", value=True)
roi = st.checkbox("Spherical mask at the injection coordinates of the experiment (.nii.gz)", value=True)
infos = st.checkbox("Informations about the experiment (.json)", value=True)
bin = st.checkbox("Binarized projection density map upon a certain threshold (.nii.gz)", value=True)

# Step 4: Configure the outputs resolution and rendering
st.subheader('Step 4: Configure the outputs resolution and rendering')
resolution = st.radio("Allen resolution: (same as the matrix)", [25, 50, 100])
smooth = st.checkbox("Use smooth interpolation method for rendering", value=False)
if bin:
    threshold = st.number_input("Threshold for the binarized map:", value=0.5)

# Step 5: Import outputs files
st.subheader('Step 5: Import file(s)')
# Run the script with subprocess
if st.button("Import") and id and ref and mat:
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the reference image and the matrix in the tempdir
        ref_path = Path(tempdir) / Path(ref.name).name
        with open(ref_path, 'wb') as f:
            f.write(ref.getvalue())
        mat_path = Path(tempdir) / Path(mat.name).name
        with open(mat_path, 'wb') as f:
            f.write(mat.getvalue())

        # Run the script
        if ids_type == 'Multiple ids (CSV File)':
            # Move the temporary CSV file to the tempdir
            temp_csv_path.rename(Path(tempdir) / temp_csv_path.name)
            ids_csv_path = Path(tempdir) / temp_csv_path.name
            cmd = ["python3", "scripts/m2m_import_proj_density.py", "--ids_csv", str(ids_csv_path), str(ref_path), str(mat_path), str(resolution), "--not_all"]
        else:
            cmd = ["python3", "scripts/m2m_import_proj_density.py", "--id", str(id_manual), str(ref_path), str(mat_path), str(resolution), "--not_all"]

        if smooth:
            cmd.append("--smooth")
        if map:
            cmd.append("--map")
        if roi:
            cmd.append("--roi")
        if infos:
            cmd.append("--infos")
        if bin:
            cmd.append("--bin")
            cmd.append("--threshold")
            cmd.append(str(threshold))
        cmd.append("-d")
        cmd.append(dir)
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success("File(s) imported successfully")
            # Create a ZIP archive of the directory
            zip_path = Path(tempdir) / "data.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in Path(dir).iterdir():
                    zip_file.write(file, arcname=file.name)
            # Download the ZIP file using st.download_button
            st.subheader('Step 6: Save file(s)')
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            st.download_button(label='Save file(s)', data=zip_data, file_name="output_files.zip", mime='application/zip')
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
