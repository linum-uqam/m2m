import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import zipfile

# Page configuration
st.set_page_config(page_title="M2M Import Projection Density", page_icon=":mouse:")

# Create Streamlit app
st.title("Import Allen Mouse Brain Connectivity Projection Density Map")
# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_import_proj_density.html')
st.write("Please upload the input files and set the arguments for the script:")

# Step 1: Choose an experiment id in the Allen Mouse Brain Connectivity Atlas dataset
st.subheader('Step 1: Choose an experiment id in the Allen Mouse Brain Connectivity Atlas dataset')
id = st.number_input("Experiment id:",value=0, step=1)
dir = Path(tempfile.mkdtemp()) / f"{id}_files"

if id:

    # Step 2: Upload reference file and matrix file
    st.subheader('Step 2: Upload reference file and matrix file') 
    ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
    mat = st.file_uploader("Matrix file (mat):", type=["mat"])

    if ref and mat :
        
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
        if st.button("Import"):
            with tempfile.TemporaryDirectory() as tempdir:
                # Save the reference image and the matrix in the tempdir
                ref_path = Path(tempdir) / Path(ref.name).name
                with open(ref_path, 'wb') as f:
                    f.write(ref.getvalue())
                mat_path = Path(tempdir) / Path(mat.name).name
                with open(mat_path, 'wb') as f:
                    f.write(mat.getvalue())
                # Run the script
                cmd = ["python3", "scripts/m2m_import_proj_density.py", str(id), str(ref_path), str(mat_path), str(resolution), "--not_all"]
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
                        st.download_button(label='Save file(s)', data=zip_data, file_name="{}_files.zip".format(id), mime='application/zip')
                except subprocess.CalledProcessError as e:
                    st.error(e.stderr)