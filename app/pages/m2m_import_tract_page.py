import streamlit as st
import subprocess
from pathlib import Path

# Define Streamlit interface
st.set_page_config(page_title="M2M Import Tractogram", page_icon=":mouse:")

st.title("Import Allen Mouse Brain Connectivity Atlas Streamlines")

# Add file inputs
out_tract = st.text_input("Output tractogram (trk) file:")
mat = st.file_uploader("Transformation matrix file (mat):", type=["mat"])
if mat:
    mat_path = Path(mat.name)
    mat_path.write_bytes(mat.getvalue())
ref = st.file_uploader("Reference nifti file:", type=["nii", "nii.gz"])
if ref:
    ref_path = Path(ref.name)
    ref_path.write_bytes(ref.getvalue())

# Add input fields
st.subheader("Select experiment IDs")
ids_type = st.radio("How do you want to select the experiment IDs?", options=["Upload CSV file", "Manually"])
if ids_type == "Upload CSV file":
    ids_csv = st.file_uploader("CSV file containing experiment IDs:", type=["csv"])
    if ids_csv:
        ids_csv_path = Path(ids_csv.name)
        ids_csv_path.write_bytes(ids_csv.getvalue())
else:
    ids_csv = None
    ids = st.text_input("Experiment IDs (separated by space):")

# Add other options
res = st.radio('Select Allen resolution (microns)', [25, 50, 100])
nocache = st.checkbox("Disable cache")
overwrite = st.checkbox("Overwrite output file")

# Add download button
if st.button("Download streamlines"):
    # Validate inputs
    if not out_tract:
        st.error("Please select an output tractogram (trk) file")
    if not mat:
        st.error("Please select a transformation matrix (mat) file")
    if not ref:
        st.error("Please select a reference nifti file")
    if ids_type == "Upload CSV file" and not ids_csv:
        st.error("Please select a CSV file containing experiment IDs")
    if ids_type == "Manually" and not ids:
        st.error("Please enter experiment IDs")
    
    # Call script as subprocess
    cmd = ["python3", "scripts/m2m_import_tract.py", str(out_tract), str(mat_path), str(ref_path), str(res)]
    if ids_csv:
        cmd.append("--ids_csv")
        cmd.append(str(ids_csv_path))
    else:
        cmd.append("--ids")
        cmd.extend(ids.split())
    if nocache:
        cmd.append("--nocache")
    if overwrite:
        cmd.append("-f")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        st.success("Streamlines downloaded successfully")
        ref_path.unlink()
        mat_path.unlink()
        if ids_csv:
            ids_csv_path.unlink()
    except subprocess.CalledProcessError as e:
        st.error(e.stderr)    
        ref_path.unlink()
        mat_path.unlink()
        if ids_csv:
            ids_csv_path.unlink()
