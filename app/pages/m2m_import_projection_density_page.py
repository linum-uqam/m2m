import streamlit as st
import subprocess
from pathlib import Path

# Page configuration
st.set_page_config(page_title="M2M Import Projection Density", page_icon=":mouse:")

# Create Streamlit app
st.title("Import Allen Mouse Brain Connectivity Projection Density Map")
# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/scripts/m2m_import_proj_density.html')
st.write("Please upload the input files and set the arguments for the script:")

# Upload input files
id = st.number_input("Experiment id in the Allen Mouse Brain Connectivity Atlas dataset:",value=0, step=1)
ref = st.file_uploader("Reference file (nifti):", type=["nii", "nii.gz"])
mat = st.file_uploader("Matrix file (mat):", type=["mat"])

# Set arguments
smooth = st.checkbox("Use smooth interpolation method for registration", value=False)
threshold = st.number_input("Threshold for the binarized map:", value=0.5)
resolution = st.radio("Allen resolution: (same as the matrix)", [25, 50, 100])

not_all = st.checkbox("Save only the specified files", value=False)
# Set file flags
if not_all:
    map = st.checkbox("Save the projection density map of the experiment (.nii.gz)", value=False)
    roi = st.checkbox("Save a spherical mask at the injection coordinates of the experiment (.nii.gz)", value=False)
    bin = st.checkbox("Save a binarized projection density map (.nii.gz) with a certain threshold", value=False)
    infos = st.checkbox("Save informations about the experiment (.json)", value=False)

# Set output directory
output_dir = st.text_input("Output directory: (path)",)

# Set override
override = st.checkbox("Overwrite output file")

# Run the script with subprocess
if st.button("Run the script"):
    # Check if all input files are uploaded
    if not (ref and mat):
        st.error("Please upload all the input files.")
    else:
        # Save the input files in the current directory
        ref_path = Path(ref.name)
        ref_path.write_bytes(ref.getvalue())
        mat_path = Path(mat.name)
        mat_path.write_bytes(mat.getvalue())
        # Run the script
        cmd = ["python3", "scripts/m2m_import_proj_density.py", str(id), str(ref_path), str(mat_path), str(resolution), "--threshold", str(threshold)]
        if smooth:
            cmd.append("--smooth")
        if not_all:
            cmd.append("--not_all")
            if map:
                cmd.append("--map")
            if roi:
                cmd.append("--roi")
            if bin:
                cmd.append("--bin")
            if infos:
                cmd.append("--infos")
        if output_dir:
            cmd.append("--dir")
            cmd.append(str(output_dir))
        if override:
            cmd.append("-f")
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            st.success("File(s) downloaded successfully")
            # Remove the input files
            ref_path.unlink()
            mat_path.unlink()
        except subprocess.CalledProcessError as e:
            st.error(e.stderr)
            # Remove the input files
            ref_path.unlink()
            mat_path.unlink()

