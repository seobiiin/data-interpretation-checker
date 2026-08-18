import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="데이터 해석 점검 도구",
    layout="wide"
)

st.title("데이터 해석 점검 도구")

st.write(
    "CSV 파일을 업로드하면 데이터 해석 전에 "
    "확인해야 할 요소를 점검합니다."
)

uploaded_file = st.file_uploader(
    "CSV 파일을 업로드하세요",
    type=["csv"]
)

if uploaded_file is not None:

    # =========================
    # CSV 읽기
    # =========================

    try:
        data = pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        data = pd.read_csv(uploaded_file, encoding="cp949")

    st.subheader("업로드한 데이터")
    st.dataframe(
        data,
        use_container_width=True
    )

    row_count = data.shape[0]
    column_count = data.shape[1]

    # =========================
    # 1. 데이터 규모 확인
    # =========================

    st.subheader("1. 데이터 규모 확인")

    st.write(f"표본 수(행): {row_count}개")
    st.write(f"변수 수(열): {column_count}개")

    # =========================
    # 2. 결측치 확인
    # =========================

    st.subheader("2. 결측치 확인")

    missing_count = data.isnull().sum()

    if row_count > 0:
        missing_ratio = (
            missing_count / row_count * 100
        )
    else:
        missing_ratio = missing_count * 0

    missing_info = pd.DataFrame({
        "결측치 개수": missing_count,
        "결측치 비율(%)": missing_ratio.round(1)
    })

    st.dataframe(
        missing_info,
        use_container_width=True
    )

    # =========================
    # 3. 이상치 후보 확인
    # =========================

    st.subheader("3. 이상치 후보 확인")

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    default_exclude = []

    for column in numeric_columns:
        column_lower = str(column).lower()

        if (
            "번호" in str(column)
            or "id" == column_lower
            or column_lower.endswith("_id")
        ):
            default_exclude.append(column)

    excluded_columns = st.multiselect(
        "이상치 검사에서 제외할 변수를 선택하세요",
        numeric_columns,
        default=default_exclude
    )

    outlier_results = []

    for column in numeric_columns:

        if column in excluded_columns:
            continue

        clean_values = data[column].dropna()

        if len(clean_values) < 4:
            outlier_count = 0

        else:
            q1 = clean_values.quantile(0.25)
            q3 = clean_values.quantile(0.75)

            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_count = (
                (clean_values < lower_bound)
                | (clean_values > upper_bound)
            ).sum()

        outlier_results.append({
            "변수": column,
            "이상치 후보 개수": int(outlier_count)
        })

    outlier_info = pd.DataFrame(outlier_results)

    if len(outlier_info) > 0:
        st.dataframe(
            outlier_info,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info(
            "현재 설정으로 이상치를 검사할 "
            "수치형 변수가 없습니다."
        )

    st.info(
        "이상치 후보는 반드시 오류이거나 제거해야 하는 값이라는 "
        "뜻은 아닙니다. 실제 관측값인지 입력 오류인지 확인하고, "
        "분석 결과에 미치는 영향을 함께 살펴볼 필요가 있습니다."
    )

    # =========================
    # 4. 범주형 변수 쏠림 확인
    # =========================

    st.subheader("4. 범주형 변수 쏠림 확인")

    categorical_columns = data.select_dtypes(
        exclude="number"
    ).columns.tolist()

    category_results = []

    for column in categorical_columns:

        clean_values = data[column].dropna()

        if len(clean_values) == 0:
            continue

        counts = clean_values.value_counts()

        top_category = counts.index[0]
        top_count = int(counts.iloc[0])

        top_ratio = (
            top_count / len(clean_values) * 100
        )

        category_results.append({
            "변수": column,
            "가장 많은 범주": top_category,
            "개수": top_count,
            "유효 관측치 수": len(clean_values),
            "비율(%)": round(top_ratio, 1)
        })

    category_info = pd.DataFrame(category_results)

    if len(category_info) > 0:

        st.dataframe(
            category_info,
            hide_index=True,
            use_container_width=True
        )

        for result in category_results:

            if result["비율(%)"] >= 80:

                st.warning(
                    f"'{result['변수']}' 변수에서 "
                    f"'{result['가장 많은 범주']}' 범주가 "
                    f"{result['개수']}/{result['유효 관측치 수']}개"
                    f"({result['비율(%)']:.1f}%)를 차지합니다. "
                    "특정 범주에 관측치가 많이 분포되어 있으므로 "
                    "전체 집단으로 일반화할 때 데이터의 구성과 "
                    "수집 방식을 함께 확인할 필요가 있습니다."
                )

    else:

        st.info(
            "현재 데이터에서 범주형 변수를 찾지 못했습니다."
        )

    st.info(
        "특정 범주의 비율이 높다는 사실만으로 데이터가 "
        "잘못되었거나 편향되었다고 판단할 수는 없습니다. "
        "특히 표본 수가 적을 때는 비율뿐 아니라 실제 관측 "
        "개수와 표본 수집 과정을 함께 확인해야 합니다."
    )

    # =========================
    # 5. 해석 시 주의사항
    # =========================

    st.subheader("5. 해석 시 주의사항")

    warning_found = False

    # ----- 결측치 -----

    for column in data.columns:

        count = int(missing_count[column])

        if count == 0:
            continue

        ratio = float(missing_ratio[column])

        # 결측 비율이 높은 경우
        if ratio >= 10:

            st.warning(
                f"결측치 주의: '{column}' 변수에 "
                f"{count}/{row_count}개의 결측치"
                f"({ratio:.1f}%)가 있습니다. "
                "전체 관측치에서 차지하는 비율이 비교적 크므로 "
                "결측치를 제외하거나 대체하는 방식에 따라 "
                "분석 결과가 달라질 수 있습니다. "
                "결측 발생 원인과 처리 방법을 함께 확인하세요."
            )

            warning_found = True

        # 비율은 작지만 결측치는 존재하는 경우
        else:

            st.info(
                f"결측치 안내: '{column}' 변수에 "
                f"{count}/{row_count}개의 결측치"
                f"({ratio:.1f}%)가 있습니다. "
                "결측치가 존재하지만 현재 표본에서 차지하는 "
                "비율은 크지 않습니다. 다만 결측 발생 원인과 "
                "분석 목적에 따라 영향이 달라질 수 있으므로 "
                "처리 여부를 확인하세요."
            )

    # ----- 이상치 후보 -----

    for result in outlier_results:

        if result["이상치 후보 개수"] > 0:

            st.warning(
                f"이상치 후보 확인 필요: "
                f"'{result['변수']}' 변수에서 "
                f"{result['이상치 후보 개수']}개의 "
                "이상치 후보가 확인되었습니다. "
                "이를 바로 제거하지 말고 실제 관측값인지 "
                "입력 오류인지 확인하고 분석 결과에 미치는 "
                "영향을 살펴볼 필요가 있습니다."
            )

            warning_found = True

    # ----- 범주형 쏠림 -----

    for result in category_results:

        if result["비율(%)"] >= 80:

            st.warning(
                f"범주 분포 확인 필요: "
                f"'{result['변수']}' 변수에서 "
                f"'{result['가장 많은 범주']}' 범주가 "
                f"{result['개수']}/{result['유효 관측치 수']}개"
                f"({result['비율(%)']:.1f}%)를 차지합니다. "
                "이 분포가 실제 집단의 특성인지 표본 수집 "
                "과정에서 나타난 것인지 확인한 뒤 "
                "해석해야 합니다."
            )

            warning_found = True

    if not warning_found:

        st.success(
            "현재 설정한 자동 점검 기준에서는 "
            "별도의 강한 주의 요소가 발견되지 않았습니다."
        )

    st.info(
        "자동 점검에서 주의 요소가 발견되지 않았더라도 "
        "데이터가 신뢰할 수 있다고 자동으로 판단할 수는 없습니다. "
        "데이터의 출처, 수집 목적, 표본 추출 방식, 누락된 정보와 "
        "같은 맥락은 사용자가 별도로 확인해야 합니다."
    )

    # =========================
    # 6. 데이터 맥락 점검
    # =========================

    st.subheader("6. 데이터 맥락 점검")

    st.write(
        "CSV 파일만으로는 데이터의 출처나 수집 과정을 "
        "확인할 수 없습니다. 아래 항목을 직접 점검해 보세요."
    )

    check_source = st.checkbox(
        "데이터의 출처와 작성 기관을 확인했다."
    )

    check_purpose = st.checkbox(
        "데이터가 어떤 목적으로 수집되었는지 확인했다."
    )

    check_sample = st.checkbox(
        "조사 대상과 표본 추출 방식을 확인했다."
    )

    check_date = st.checkbox(
        "데이터가 언제 수집되었는지 확인했다."
    )

    check_measure = st.checkbox(
        "각 변수의 의미와 측정 기준을 확인했다."
    )

    context_checks = [
        check_source,
        check_purpose,
        check_sample,
        check_date,
        check_measure
    ]

    checked_count = sum(context_checks)

    st.write(
        f"맥락 점검: {checked_count}/5 항목 확인"
    )

    if checked_count == 5:

        st.success(
            "기본적인 데이터 맥락 항목을 모두 확인했습니다. "
            "이제 자동 점검 결과와 함께 고려하여 "
            "데이터를 해석하세요."
        )

    else:

        st.warning(
            "아직 확인하지 않은 데이터 맥락 항목이 있습니다. "
            "확인하지 않은 내용을 모르는 상태에서 분석 결과를 "
            "과도하게 일반화하지 않도록 주의하세요."
        )
    # =========================
    # 7. 최종 점검 요약
    # =========================

    st.subheader("7. 최종 점검 요약")

    # -------------------------
    # 결측치 수준 계산
    # -------------------------

    high_missing_variables = []
    low_missing_variables = []

    for column in data.columns:

        count = int(missing_count[column])

        if count == 0:
            continue

        ratio = float(missing_ratio[column])

        if ratio >= 10:
            high_missing_variables.append(column)
        else:
            low_missing_variables.append(column)

    # -------------------------
    # 이상치 후보 변수 계산
    # -------------------------

    outlier_variables = [
        result["변수"]
        for result in outlier_results
        if result["이상치 후보 개수"] > 0
    ]

    # -------------------------
    # 범주 쏠림 변수 계산
    # -------------------------

    imbalance_variables = [
        result["변수"]
        for result in category_results
        if result["비율(%)"] >= 80
    ]

    # -------------------------
    # 요약표
    # -------------------------

    summary_rows = []

    summary_rows.append({
        "점검 항목": "데이터 규모",
        "결과": f"{row_count}행 × {column_count}열",
        "수준": "정보"
    })

    if len(high_missing_variables) > 0:
        summary_rows.append({
            "점검 항목": "결측치",
            "결과": (
                f"주의 필요 {len(high_missing_variables)}개 변수 "
                f"({', '.join(map(str, high_missing_variables))})"
            ),
            "수준": "주의"
        })

    if len(low_missing_variables) > 0:
        summary_rows.append({
            "점검 항목": "결측치",
            "결과": (
                f"낮은 비율 {len(low_missing_variables)}개 변수 "
                f"({', '.join(map(str, low_missing_variables))})"
            ),
            "수준": "확인"
        })

    if (
        len(high_missing_variables) == 0
        and len(low_missing_variables) == 0
    ):
        summary_rows.append({
            "점검 항목": "결측치",
            "결과": "발견되지 않음",
            "수준": "정보"
        })

    if len(outlier_variables) > 0:
        summary_rows.append({
            "점검 항목": "이상치 후보",
            "결과": (
                f"{len(outlier_variables)}개 변수 "
                f"({', '.join(map(str, outlier_variables))})"
            ),
            "수준": "확인"
        })
    else:
        summary_rows.append({
            "점검 항목": "이상치 후보",
            "결과": "발견되지 않음",
            "수준": "정보"
        })

    if len(imbalance_variables) > 0:
        summary_rows.append({
            "점검 항목": "범주 쏠림",
            "결과": (
                f"{len(imbalance_variables)}개 변수 "
                f"({', '.join(map(str, imbalance_variables))})"
            ),
            "수준": "확인"
        })
    else:
        summary_rows.append({
            "점검 항목": "범주 쏠림",
            "결과": "발견되지 않음",
            "수준": "정보"
        })

    summary_rows.append({
        "점검 항목": "데이터 맥락",
        "결과": f"{checked_count}/5 항목 확인",
        "수준": (
            "정보"
            if checked_count == 5
            else "확인"
        )
    })

    summary_data = pd.DataFrame(summary_rows)

    st.dataframe(
        summary_data,
        hide_index=True,
        use_container_width=True
    )

    # -------------------------
    # 최종 안내
    # -------------------------

    strong_warning_count = len(high_missing_variables)

    check_item_count = (
        len(low_missing_variables)
        + len(outlier_variables)
        + len(imbalance_variables)
    )

    if strong_warning_count > 0:

        st.warning(
            f"현재 자동 점검에서 주의 수준 항목이 "
            f"{strong_warning_count}개 확인되었습니다. "
            "해당 항목이 분석 결과에 어떤 영향을 줄 수 있는지 "
            "확인한 뒤 해석하세요."
        )

    elif check_item_count > 0:

        st.info(
            "강한 주의 수준의 항목은 없지만 추가로 확인할 "
            "데이터 특성이 있습니다. 이것만으로 데이터의 "
            "품질이나 신뢰성을 판단하지 말고 분석 목적과 "
            "데이터 맥락을 함께 고려하세요."
        )

    else:

        st.success(
            "현재 설정한 자동 점검 기준에서는 강한 주의 "
            "요소가 발견되지 않았습니다."
        )

    st.info(
        "이 결과는 데이터의 품질을 합격·불합격으로 판정하거나 "
        "신뢰도 점수를 계산한 것이 아닙니다. 자동 점검 결과와 "
        "데이터의 출처, 수집 목적, 표본 추출 방식, 측정 기준을 "
        "함께 고려하여 해석하세요."
    )
   
