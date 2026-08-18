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

    st.subheader("1. 데이터 규모 확인")

    row_count = data.shape[0]
    column_count = data.shape[1]

    st.write(f"표본 수(행): {row_count}개")
    st.write(f"변수 수(열): {column_count}개")

    st.subheader("2. 결측치 확인")

    missing_count = data.isnull().sum()
    missing_ratio = (data.isnull().sum() / len(data)) * 100

    missing_info = pd.DataFrame({
        "결측치 개수": missing_count,
        "결측치 비율(%)": missing_ratio.round(1)
    })

    st.dataframe(missing_info)

    st.subheader("3. 이상치 후보 확인")

    numeric_columns = data.select_dtypes(include="number").columns

    outlier_results = []

    for column in numeric_columns:
        column_data = data[column].dropna()

        q1 = column_data.quantile(0.25)
        q3 = column_data.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = column_data[
            (column_data < lower_bound) |
            (column_data > upper_bound)
        ]

        outlier_results.append({
            "변수": column,
            "이상치 후보 개수": len(outliers)
        })

    outlier_info = pd.DataFrame(outlier_results)

    st.dataframe(outlier_info)

    st.info(
        "이상치 후보는 반드시 오류이거나 제거해야 하는 값이라는 뜻은 아닙니다. "
        "실제 관측값인지 입력 오류인지 확인하고, 분석 결과에 미치는 영향을 함께 살펴볼 필요가 있습니다."
    )
