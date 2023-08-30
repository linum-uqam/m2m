import streamlit as st

# Page configuration
st.set_page_config(page_title='M2M Web App')

st.title('Welcome to M2M Web App 🐭')

# Link to the documentation
st.write('https://m2m.readthedocs.io/en/latest/')

st.write('Here a quick guide to help you start using the toolkit ⬇️')
st.caption("Navigate between pages using the sidebar panel")

# Quick start
st.subheader("Step 1: Download a user-space reference image")
st.markdown("* 🐭 Download a template using **`m2m download template page`**")
st.markdown("* 🗒️ Download an annotation volume using **`m2m download annotation page`**")
st.caption("Choose one or both")

st.subheader("Step 2: Compute a transform matrix")
st.markdown("* 🔢 Compute a tranform matrix using **`m2m compute transform matrix page`**")
st.caption("One matrix is computed for one specific resolution, so you may want to have one for each resolution")

st.subheader("Step 3: Start working with the mouse brain!")
st.markdown("* 🗺️ Import projection density maps using **`m2m import proj density page`**")
st.markdown("* 🔎 Find crossing regions using **`m2m crossing finder page`**")
st.markdown("* 🔍 Find experiments IDs using **`m2m experiments finder page`**")
st.caption("Make sure to have your reference image 🖼️ and your matrix with you 🔢")