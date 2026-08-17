import streamlit as st
import pandas as pd

st.title("데이터 해석 점검 도구")

st.write(
    "CSV 파일을 업로드하면 데이터 해석 전에 확인해야 할 요소를 점검합니다."
)

uploaded_file = st.file_uploader(
    "CSV 파일을 업로드하세요",
    type=["csv"]
)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)

    st.subheader("업로드한 데이터")
    st.dataframe(data)
