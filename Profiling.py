import pandas as pd
import ydata_profiling
import streamlit as st
from streamlit_pandas_profiling import st_profile_report
df = pd.read_csv(
r"C:\Users\DELL\OneDrive\Desktop\Profiling\Test.csv"
)
pr = df.profile_report()

st.title("Profiling in Streamlit")
st.write(df)
st_profile_report(pr)
pr.to_file("your_report.html")