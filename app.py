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

    # 1. 데이터 규모 확인
    st.subheader("1. 데이터 규모 확인")

    row_count = data.shape[0]
    column_count = data.shape[1]

    st.write(f"표본 수(행): {row_count}개")
    st.write(f"변수 수(열): {column_count}개")

    # 2. 결측치 확인
    st.subheader("2. 결측치 확인")

    missing_count = data.isnull().sum()
    missing_ratio = (data.isnull().sum() / len(data)) * 100

    missing_info = pd.DataFrame({
        "결측치 개수": missing_count,
        "결측치 비율(%)": missing_ratio.round(1)
    })

    st.dataframe(missing_info)

    # 3. 이상치 후보 확인
    st.subheader("3. 이상치 후보 확인")

    numeric_columns = list(
        data.select_dtypes(include="number").columns
    )

    excluded_columns = st.multiselect(
        "이상치 검사에서 제외할 변수를 선택하세요",
        options=numeric_columns,
        help="학생번호, ID, 학번처럼 식별을 위한 숫자 변수는 제외할 수 있습니다."
    )

    outlier_columns = [
        column for column in numeric_columns
        if column not in excluded_columns
    ]

    outlier_results = []

    for column in outlier_columns:
        column_data = data[column].dropna()

        if len(column_data) > 0:
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

    if len(outlier_info) > 0:
        st.dataframe(outlier_info)
    else:
        st.write("이상치 검사를 수행할 수치형 변수가 없습니다.")

    st.info(
        "이상치 후보는 반드시 오류이거나 제거해야 하는 값이라는 뜻은 아닙니다. "
        "실제 관측값인지 입력 오류인지 확인하고, 분석 결과에 미치는 영향을 "
        "함께 살펴볼 필요가 있습니다."
    )

    # 4. 범주형 변수 쏠림 확인
    st.subheader("4. 범주형 변수 쏠림 확인")

    categorical_columns = data.select_dtypes(
        include=["object", "category"]
    ).columns

    category_results = []

    for column in categorical_columns:
        column_data = data[column].dropna()

        if len(column_data) > 0:
            category_ratio = column_data.value_counts(
                normalize=True
            )

            top_category = category_ratio.index[0]
            top_ratio = category_ratio.iloc[0] * 100

            category_results.append({
                "변수": column,
                "가장 많은 범주": top_category,
                "비율(%)": round(top_ratio, 1)
            })

    category_info = pd.DataFrame(category_results)

    if len(category_info) > 0:
        st.dataframe(category_info)

        for _, row in category_info.iterrows():
            if row["비율(%)"] >= 80:
                st.warning(
                    f"'{row['변수']}' 변수에서 "
                    f"'{row['가장 많은 범주']}' 범주가 "
                    f"전체의 {row['비율(%)']}%를 차지합니다. "
                    "특정 범주에 데이터가 많이 분포되어 있으므로, "
                    "전체 집단으로 일반화할 때 데이터의 구성과 "
                    "수집 방식을 함께 확인할 필요가 있습니다."
                )

        st.info(
            "특정 범주의 비율이 높다는 사실만으로 데이터가 "
            "잘못되었거나 편향되었다고 판단할 수는 없습니다. "
            "실제 집단의 특성과 표본 수집 과정을 함께 확인해야 합니다."
        )

    else:
        st.write("확인할 범주형 변수가 없습니다.")

    # 5. 해석 시 주의사항
    st.subheader("5. 해석 시 주의사항")

    warning_found = False

    # 결측치 주의사항
    for column in data.columns:
        if missing_count[column] > 0:
            warning_found = True

            st.warning(
                f"결측치 확인 필요: '{column}' 변수에 "
                f"{missing_count[column]}개의 결측치 "
                f"({missing_ratio[column]:.1f}%)가 있습니다. "
                "결측치를 제외하거나 대체하는 방식에 따라 "
                "분석 결과가 달라질 수 있으므로 처리 방법을 "
                "함께 확인해야 합니다."
            )

    # 이상치 후보 주의사항
    for result in outlier_results:
        if result["이상치 후보 개수"] > 0:
            warning_found = True

            st.warning(
                f"이상치 후보 확인 필요: '{result['변수']}' 변수에서 "
                f"{result['이상치 후보 개수']}개의 이상치 후보가 "
                "확인되었습니다. 이를 바로 제거하지 말고 실제 "
                "관측값인지 입력 오류인지 확인하고, 분석 결과에 "
                "미치는 영향을 살펴볼 필요가 있습니다."
            )

    # 범주 쏠림 주의사항
    for result in category_results:
        if result["비율(%)"] >= 80:
            warning_found = True

            st.warning(
                f"범주 분포 확인 필요: '{result['변수']}' 변수에서 "
                f"'{result['가장 많은 범주']}' 범주가 "
                f"전체의 {result['비율(%)']}%를 차지합니다. "
                "이 분포가 실제 집단의 특성인지 표본 수집 과정에서 "
                "나타난 것인지 확인한 뒤 해석해야 합니다."
            )

    if not warning_found:
        st.success(
            "현재 설정한 자동 점검 기준에서는 별도의 "
            "주의 요소가 발견되지 않았습니다."
        )

    st.info(
        "자동 점검에서 주의 요소가 발견되지 않았더라도 "
        "데이터가 신뢰할 수 있다고 자동으로 판단할 수는 없습니다. "
        "데이터의 출처, 수집 목적, 표본 추출 방식, 누락된 정보와 "
        "같은 맥락은 사용자가 별도로 확인해야 합니다."
    )
