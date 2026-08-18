import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="데이터 해석 점검 도구",
    page_icon="📊",
    layout="centered"
)

st.title("데이터 해석 점검 도구")
st.write("CSV 파일을 업로드하면 데이터 해석 전에 확인해야 할 요소를 점검합니다.")

uploaded_file = st.file_uploader(
    "CSV 파일을 업로드하세요",
    type=["csv"]
)

if uploaded_file is not None:

    # CSV 읽기
    try:
        data = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        data = pd.read_csv(uploaded_file, encoding="cp949")
    except Exception as e:
        st.error(f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}")
        st.stop()

    st.subheader("업로드한 데이터")
    st.dataframe(data, use_container_width=True)

    row_count = data.shape[0]
    column_count = data.shape[1]

    # --------------------------------------------------
    # 1. 데이터 규모 확인
    # --------------------------------------------------

    st.subheader("1. 데이터 규모 확인")

    st.write(f"표본 수(행): {row_count}개")
    st.write(f"변수 수(열): {column_count}개")

    if row_count < 30:
        st.info(
            "표본 수가 비교적 적습니다. 비율이나 이상치 후보를 해석할 때 "
            "실제 관찰 개수도 함께 확인하는 것이 좋습니다."
        )

    # --------------------------------------------------
    # 2. 결측치 확인
    # --------------------------------------------------

    st.subheader("2. 결측치 확인")

    missing_count = data.isna().sum()

    if row_count > 0:
        missing_ratio = (missing_count / row_count * 100).round(1)
    else:
        missing_ratio = pd.Series(0, index=data.columns)

    missing_info = pd.DataFrame({
        "결측치 개수": missing_count,
        "결측치 비율(%)": missing_ratio
    })

    st.dataframe(missing_info, use_container_width=True)

    # --------------------------------------------------
    # 3. 이상치 후보 확인
    # --------------------------------------------------

    st.subheader("3. 이상치 후보 확인")

    numeric_columns = data.select_dtypes(
        include=np.number
    ).columns.tolist()

    default_exclude = []

    for column in numeric_columns:

        column_name = str(column)
        column_lower = column_name.lower().strip()

        id_names = [
            "id",
            "고객id",
            "학생id",
            "회원id",
            "사용자id",
            "customerid",
            "studentid",
            "userid",
            "memberid"
        ]

        if (
            "번호" in column_name
            or "학번" in column_name
            or column_lower in id_names
            or column_lower.endswith("_id")
        ):
            default_exclude.append(column)

    exclude_columns = st.multiselect(
        "이상치 검사에서 제외할 변수를 선택하세요",
        options=numeric_columns,
        default=default_exclude,
        help=(
            "학생번호, 고객ID처럼 단순 식별 목적으로 사용하는 숫자형 변수는 "
            "이상치 분석에서 제외하는 것이 좋습니다."
        )
    )

    analysis_columns = [
        column
        for column in numeric_columns
        if column not in exclude_columns
    ]

    outlier_results = []
    outlier_details = {}

    for column in analysis_columns:

        clean_data = data[column].dropna()

        if len(clean_data) < 4:
            outlier_results.append({
                "변수": column,
                "이상치 후보 개수": 0
            })
            outlier_details[column] = []
            continue

        q1 = clean_data.quantile(0.25)
        q3 = clean_data.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = clean_data[
            (clean_data < lower_bound)
            | (clean_data > upper_bound)
        ]

        outlier_results.append({
            "변수": column,
            "이상치 후보 개수": len(outliers)
        })

        outlier_details[column] = outliers.tolist()

    outlier_info = pd.DataFrame(outlier_results)

    if len(outlier_info) > 0:
        st.dataframe(
            outlier_info,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("이상치 검사를 수행할 숫자형 변수가 없습니다.")

    for column, values in outlier_details.items():

        if len(values) > 0:

            preview_values = values[:10]

            st.warning(
                f"'{column}' 변수에서 이상치 후보 "
                f"{len(values)}개가 확인되었습니다. "
                f"후보 값 예시: {preview_values}"
            )

    st.info(
        "IQR 방식은 다른 값들과 비교해 통계적으로 멀리 떨어진 값을 "
        "이상치 후보로 찾습니다. 후보 값이 실제 관찰값인지 입력 오류인지는 "
        "자동으로 판단할 수 없으므로 후보 값을 직접 확인해야 합니다."
    )

    # --------------------------------------------------
    # 4. 범주형 변수 쏠림 확인
    # --------------------------------------------------

    st.subheader("4. 범주형 변수 쏠림 확인")

    categorical_columns = data.select_dtypes(
        exclude=np.number
    ).columns.tolist()

    category_results = []

    for column in categorical_columns:

        valid_data = data[column].dropna()
        valid_count = len(valid_data)

        if valid_count == 0:
            continue

        value_counts = valid_data.value_counts()

        top_category = value_counts.index[0]
        top_count = int(value_counts.iloc[0])

        top_ratio = round(
            top_count / valid_count * 100,
            1
        )

        category_results.append({
            "변수": column,
            "가장 많은 범주": top_category,
            "개수": top_count,
            "유효 관찰치 수": valid_count,
            "비율(%)": top_ratio
        })

    category_info = pd.DataFrame(category_results)

    if len(category_info) > 0:

        st.dataframe(
            category_info,
            hide_index=True,
            use_container_width=True
        )

        for _, row in category_info.iterrows():

            if row["비율(%)"] >= 80:

                st.warning(
                    f"'{row['변수']}' 변수에서 "
                    f"'{row['가장 많은 범주']}' 범주가 "
                    f"전체 유효 관찰치의 {row['비율(%)']}%를 차지합니다. "
                    f"({row['개수']}/{row['유효 관찰치 수']}개) "
                    "특정 범주에 데이터가 많이 분포되어 있으므로 "
                    "전체 집단으로 일반화할 때 데이터의 구성과 "
                    "수집 방식을 함께 확인할 필요가 있습니다."
                )

        st.info(
            "특정 범주의 비율이 높다는 사실만으로 데이터가 잘못되었거나 "
            "편향되었다고 판단할 수는 없습니다. 특히 표본 수가 적을 때는 "
            "비율뿐 아니라 실제 관찰 개수와 표본 수집 과정을 함께 확인해야 합니다."
        )

    else:
        st.info("확인할 범주형 변수가 없습니다.")

    # --------------------------------------------------
    # 5. 해석 시 주의사항
    # --------------------------------------------------

    st.subheader("5. 해석 시 주의사항")

    warning_found = False

    for column in data.columns:

        count = int(missing_count[column])
        ratio = float(missing_ratio[column])

        if count > 0:

            warning_found = True

            if ratio >= 10:

                st.warning(
                    f"결측치 확인 필요: '{column}' 변수에 "
                    f"{count}개의 결측치({ratio:.1f}%)가 있습니다. "
                    "결측치를 제외하거나 대체하는 방식에 따라 분석 결과가 "
                    "달라질 수 있으므로 처리 방법을 함께 확인해야 합니다."
                )

            else:

                st.info(
                    f"결측치 참고: '{column}' 변수에 "
                    f"{count}개의 결측치({ratio:.1f}%)가 있습니다. "
                    "비율이 비교적 낮더라도 분석 목적에 따라 "
                    "결측치 처리 방법을 확인하는 것이 좋습니다."
                )

    for column, values in outlier_details.items():

        if len(values) > 0:

            warning_found = True

            preview_values = values[:5]

            st.warning(
                f"이상치 후보 확인 필요: '{column}' 변수에서 "
                f"{len(values)}개의 이상치 후보가 확인되었습니다. "
                f"후보 값 예시: {preview_values}. "
                "이를 바로 제거하지 말고 실제 관찰값인지 입력 오류인지 "
                "확인하고 분석 결과에 미치는 영향을 살펴볼 필요가 있습니다."
            )

    if len(category_info) > 0:

        for _, row in category_info.iterrows():

            if row["비율(%)"] >= 80:

                warning_found = True

                st.warning(
                    f"범주 분포 확인 필요: '{row['변수']}' 변수에서 "
                    f"'{row['가장 많은 범주']}' 범주가 "
                    f"{row['비율(%)']}% "
                    f"({row['개수']}/{row['유효 관찰치 수']}개)를 "
                    "차지합니다. 이 분포가 실제 집단의 특성인지 "
                    "표본 수집 과정에서 나타난 것인지 확인한 뒤 "
                    "해석해야 합니다."
                )

    if not warning_found:

        st.success(
            "현재 설정한 자동 점검 기준에서는 "
            "별도의 주의 요소가 발견되지 않았습니다."
        )

    st.info(
        "자동 점검에서 주의 요소가 발견되지 않았더라도 데이터가 "
        "신뢰할 수 있다고 자동으로 판단할 수는 없습니다. "
        "데이터의 출처, 수집 목적, 표본 추출 방식, 누락된 정보와 같은 "
        "맥락은 사용자가 별도로 확인해야 합니다."
    )

    # --------------------------------------------------
    # 6. 데이터 맥락 점검
    # --------------------------------------------------

    st.subheader("6. 데이터 맥락 점검")

    st.write(
        "CSV 파일만으로는 데이터의 출처나 수집 과정을 확인할 수 없습니다. "
        "아래 항목을 직접 점검해 보세요."
    )

    context_checks = []

    context_checks.append(
        st.checkbox(
            "데이터의 출처와 작성 기관을 확인했다."
        )
    )

    context_checks.append(
        st.checkbox(
            "데이터가 어떤 목적으로 수집되었는지 확인했다."
        )
    )

    context_checks.append(
        st.checkbox(
            "조사 대상과 표본 추출 방식을 확인했다."
        )
    )

    context_checks.append(
        st.checkbox(
            "데이터가 언제 수집되었는지 확인했다."
        )
    )

    context_checks.append(
        st.checkbox(
            "각 변수의 의미와 측정 기준을 확인했다."
        )
    )

    checked_count = sum(context_checks)

    st.write(
        f"맥락 점검: {checked_count}/5 항목 확인"
    )

    if checked_count == 5:

        st.success(
            "기본적인 데이터 맥락 항목을 모두 확인했습니다. "
            "이제 자동 점검 결과와 함께 고려하여 데이터를 해석하세요."
        )

    else:

        st.warning(
            "아직 확인하지 않은 데이터 맥락 항목이 있습니다. "
            "확인하지 않은 내용을 모르는 상태에서 분석 결과를 "
            "과도하게 일반화하지 않도록 주의하세요."
        )

    # --------------------------------------------------
    # 7. 최종 점검 요약
    # --------------------------------------------------

    st.subheader("7. 최종 점검 요약")

    missing_variable_count = int(
        (missing_count > 0).sum()
    )

    outlier_variable_count = sum(
        1
        for values in outlier_details.values()
        if len(values) > 0
    )

    imbalance_variable_count = 0

    if len(category_info) > 0:
        imbalance_variable_count = int(
            (category_info["비율(%)"] >= 80).sum()
        )

    summary_data = pd.DataFrame({
        "점검 항목": [
            "데이터 규모",
            "결측치가 있는 변수",
            "이상치 후보가 있는 변수",
            "80% 이상 범주 쏠림 변수",
            "데이터 맥락 확인"
        ],
        "결과": [
            f"{row_count}행 × {column_count}열",
            f"{missing_variable_count}개",
            f"{outlier_variable_count}개",
            f"{imbalance_variable_count}개",
            f"{checked_count}/5"
        ]
    })

    st.dataframe(
        summary_data,
        hide_index=True,
        use_container_width=True
    )

    st.info(
        "이 요약은 데이터에서 자동으로 확인할 수 있는 특징과 "
        "사용자가 직접 확인한 맥락 항목을 정리한 것입니다. "
        "결과를 합격·불합격이나 신뢰도 점수로 해석하지 말고, "
        "각 점검 항목을 데이터 해석 과정에서 함께 고려하세요."
    )
