import streamlit as st

st.title("My Simple Dashboard")

# Interactive widget
number = st.slider("Select a value", 1, 100, 50)

# Dynamic output
st.write(f"You selected: {number}")
st.metric(label="Double the value", value=number * 2)