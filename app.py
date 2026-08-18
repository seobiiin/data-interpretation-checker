import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(
    page_title="데이터 해석 점검 도구",
    page_icon="📊",
    layout="centered"
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

    # ==================================================
    # CSV 읽기
    # ==================================================

    try:
        data = pd.read_csv(uploaded_file)

    except UnicodeDecodeError:
        data = pd.read_csv(
            uploaded_file,
            encoding="cp949"
        )

    except Exception as e:
        st.error(
            f"CSV 파일을 읽는 중 오류가 발생했습니다: {e}"
        )
        st.stop()

    st.subheader("업로드한 데이터")

    st.dataframe(
        data,
        use_container_width=True
    )

    row_count = data.shape[0]
    column_count = data.shape[1]

    # ==================================================
    # 식별자 후보 자동 탐지 함수
    # ==================================================

    def detect_identifier_candidate(column_name, series):

        name = str(column_name)
        name_lower = name.lower().strip()

        non_null = series.dropna()

        if len(non_null) == 0:
            return False, []

        reasons = []

        # ----------------------------------------------
        # 1. 열 이름 확인
        # ----------------------------------------------

        identifier_keywords = [
            "id",
            "번호",
            "학번",
            "코드",
            "code",
            "index",
            "key",
            "serial",
            "no"
        ]

        name_match = any(
            keyword in name_lower
            for keyword in identifier_keywords
        )

        if name_match:
            reasons.append("열 이름이 식별자 형태")

        # ----------------------------------------------
        # 2. 고유값 비율 확인
        # ----------------------------------------------

        unique_ratio = (
            non_null.nunique()
            / len(non_null)
        )

        highly_unique = (
            unique_ratio >= 0.95
        )

        if highly_unique:
            reasons.append(
                "대부분의 값이 서로 다름"
            )

        # ----------------------------------------------
        # 3. 숫자가 일정하게 증가하는지 확인
        # ----------------------------------------------

        sequential_number = False

        if pd.api.types.is_numeric_dtype(non_null):

            if len(non_null) >= 3:

                numeric_values = (
                    non_null
                    .sort_values()
                    .reset_index(drop=True)
                )

                differences = (
                    numeric_values
                    .diff()
                    .dropna()
                )

                if len(differences) > 0:

                    sequential_number = (
                        differences.nunique() == 1
                        and differences.iloc[0] == 1
                    )

        if sequential_number:
            reasons.append(
                "값이 연속적인 번호 형태"
            )

        # ----------------------------------------------
        # 4. 문자열 ID 형태 확인
        # 예: A0001, USER-001, KOR_100
        # ----------------------------------------------

        id_like_string = False

        if (
            pd.api.types.is_object_dtype(non_null)
            or pd.api.types.is_string_dtype(non_null)
        ):

            sample_values = (
                non_null
                .astype(str)
                .head(100)
            )

            id_pattern_count = 0

            for value in sample_values:

                value = value.strip()

                if re.match(
                    r"^[A-Za-z가-힣_-]*\d+[A-Za-z가-힣_-]*$",
                    value
                ):
                    id_pattern_count += 1

            if len(sample_values) > 0:

                pattern_ratio = (
                    id_pattern_count
                    / len(sample_values)
                )

                id_like_string = (
                    pattern_ratio >= 0.8
                )

        if id_like_string:
            reasons.append(
                "문자와 숫자가 결합된 ID 형태"
            )

        # ----------------------------------------------
        # 최종 추천 규칙
        # ----------------------------------------------

        candidate = False

        if name_match and highly_unique:
            candidate = True

        elif name_match and sequential_number:
            candidate = True

        elif highly_unique and sequential_number:
            candidate = True

        elif name_match and id_like_string:
            candidate = True

        elif highly_unique and id_like_string:
            candidate = True

        return candidate, reasons

    # ==================================================
    # 모든 열에서 식별자 후보 찾기
    # ==================================================

    identifier_candidates = []
    identifier_reasons = {}

    for column in data.columns:

        candidate, reasons = detect_identifier_candidate(
            column,
            data[column]
        )

        if candidate:

            identifier_candidates.append(column)
            identifier_reasons[column] = reasons

    # ==================================================
    # 1. 데이터 규모 확인
    # ==================================================

    st.subheader("1. 데이터 규모 확인")

    st.write(
        f"표본 수(행): {row_count}개"
    )

    st.write(
        f"변수 수(열): {column_count}개"
    )

    if row_count < 30:

        st.info(
            "표본 수가 비교적 적습니다. "
            "비율이나 이상치 후보를 해석할 때 "
            "실제 관찰 개수도 함께 확인하는 것이 좋습니다."
        )

    # ==================================================
    # 2. 결측치 확인
    # ==================================================

    st.subheader("2. 결측치 확인")

    missing_count = data.isna().sum()

    if row_count > 0:

        missing_ratio = (
            missing_count
            / row_count
            * 100
        ).round(1)

    else:

        missing_ratio = pd.Series(
            0,
            index=data.columns
        )

    missing_info = pd.DataFrame({
        "결측치 개수": missing_count,
        "결측치 비율(%)": missing_ratio
    })

    st.dataframe(
        missing_info,
        use_container_width=True
    )

    # ==================================================
    # 3. 이상치 후보 확인
    # ==================================================

    st.subheader("3. 이상치 후보 확인")

    st.write(
        "먼저 식별자처럼 보이는 변수를 확인합니다. "
        "식별자는 분석 값이라기보다 각 행을 구분하기 위한 "
        "값일 수 있으므로 이상치 검사에서 제외할 수 있습니다."
    )

    if len(identifier_candidates) > 0:

        st.info(
            "앱이 자동으로 찾은 식별자 후보: "
            + ", ".join(
                map(str, identifier_candidates)
            )
        )

    else:

        st.info(
            "자동으로 식별자 후보로 추천된 변수는 없습니다."
        )

    selected_identifiers = st.multiselect(
        "식별자로 사용할 변수를 확인하세요",
        options=data.columns.tolist(),
        default=identifier_candidates,
        help=(
            "앱의 추천이 항상 정확한 것은 아닙니다. "
            "실제 식별자가 아니라면 선택을 해제하고, "
            "누락된 식별자가 있다면 직접 추가하세요."
        )
    )

    # 자동 추천 이유 표시
    if len(identifier_candidates) > 0:

        with st.expander(
            "식별자 후보로 추천한 이유 보기"
        ):

            for column in identifier_candidates:

                reasons = identifier_reasons.get(
                    column,
                    []
                )

                reason_text = ", ".join(reasons)

                st.write(
                    f"- {column}: {reason_text}"
                )

    # 숫자형 변수만 실제 이상치 검사 대상으로 사용
    numeric_columns = data.select_dtypes(
        include=np.number
    ).columns.tolist()

    analysis_columns = [
        column
        for column in numeric_columns
        if column not in selected_identifiers
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

        lower_bound = (
            q1 - 1.5 * iqr
        )

        upper_bound = (
            q3 + 1.5 * iqr
        )

        outliers = clean_data[
            (clean_data < lower_bound)
            | (clean_data > upper_bound)
        ]

        outlier_results.append({
            "변수": column,
            "이상치 후보 개수": len(outliers)
        })

        outlier_details[column] = (
            outliers.tolist()
        )

    outlier_info = pd.DataFrame(
        outlier_results
    )

    if len(outlier_info) > 0:

        st.dataframe(
            outlier_info,
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "이상치 검사를 수행할 "
            "숫자형 변수가 없습니다."
        )

    # 이상치 후보 실제 값 표시
    for column, values in outlier_details.items():

        if len(values) > 0:

            preview_values = values[:10]

            st.warning(
                f"'{column}' 변수에서 이상치 후보 "
                f"{len(values)}개가 확인되었습니다. "
                f"후보 값 예시: {preview_values}"
            )

    st.info(
        "IQR 방식은 다른 값들과 비교해 통계적으로 "
        "멀리 떨어진 값을 이상치 후보로 찾습니다. "
        "후보 값이 실제 관찰값인지 입력 오류인지는 "
        "자동으로 판단할 수 없으므로 직접 확인해야 합니다."
    )

    # ==================================================
    # 4. 범주형 변수 쏠림 확인
    # ==================================================

    st.subheader(
        "4. 범주형 변수 쏠림 확인"
    )

    categorical_columns = data.select_dtypes(
        exclude=np.number
    ).columns.tolist()

    # 식별자로 선택된 문자열 변수도 범주 쏠림 검사에서 제외
    categorical_columns = [
        column
        for column in categorical_columns
        if column not in selected_identifiers
    ]

    category_results = []

    for column in categorical_columns:

        valid_data = (
            data[column]
            .dropna()
        )

        valid_count = len(valid_data)

        if valid_count == 0:
            continue

        value_counts = (
            valid_data.value_counts()
        )

        top_category = (
            value_counts.index[0]
        )

        top_count = int(
            value_counts.iloc[0]
        )

        top_ratio = round(
            top_count
            / valid_count
            * 100,
            1
        )

        category_results.append({
            "변수": column,
            "가장 많은 범주": top_category,
            "개수": top_count,
            "유효 관찰치 수": valid_count,
            "비율(%)": top_ratio
        })

    category_info = pd.DataFrame(
        category_results
    )

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
                    f"{row['개수']}/"
                    f"{row['유효 관찰치 수']}개 "
                    f"({row['비율(%)']}%)를 차지합니다. "
                    "특정 범주에 데이터가 많이 분포되어 있으므로 "
                    "전체 집단으로 일반화할 때 데이터의 구성과 "
                    "수집 방식을 함께 확인할 필요가 있습니다."
                )

    else:

        st.info(
            "확인할 범주형 변수가 없습니다."
        )

    st.info(
        "특정 범주의 비율이 높다는 사실만으로 "
        "데이터가 잘못되었거나 편향되었다고 판단할 수는 없습니다. "
        "특히 표본 수가 적을 때는 비율뿐 아니라 실제 관찰 개수와 "
        "표본 수집 과정을 함께 확인해야 합니다."
    )

    # ==================================================
    # 5. 해석 시 주의사항
    # ==================================================

    st.subheader(
        "5. 해석 시 주의사항"
    )

    warning_found = False

    # --------------------------------------------------
    # 결측치
    # --------------------------------------------------

    for column in data.columns:

        count = int(
            missing_count[column]
        )

        ratio = float(
            missing_ratio[column]
        )

        if count > 0:

            if ratio >= 10:

                warning_found = True

                st.warning(
                    f"결측치 확인 필요: '{column}' 변수에 "
                    f"{count}/{row_count}개의 결측치 "
                    f"({ratio:.1f}%)가 있습니다. "
                    "결측치를 제외하거나 대체하는 방식에 따라 "
                    "분석 결과가 달라질 수 있으므로 "
                    "처리 방법을 함께 확인해야 합니다."
                )

            else:

                st.info(
                    f"결측치 참고: '{column}' 변수에 "
                    f"{count}/{row_count}개의 결측치 "
                    f"({ratio:.1f}%)가 있습니다. "
                    "비율이 비교적 낮더라도 분석 목적에 따라 "
                    "결측치 처리 방법을 확인하는 것이 좋습니다."
                )

    # --------------------------------------------------
    # 이상치
    # --------------------------------------------------

    for column, values in outlier_details.items():

        if len(values) > 0:

            warning_found = True

            preview_values = values[:5]

            st.warning(
                f"이상치 후보 확인 필요: "
                f"'{column}' 변수에서 "
                f"{len(values)}개의 이상치 후보가 확인되었습니다. "
                f"후보 값 예시: {preview_values}. "
                "이를 바로 제거하지 말고 실제 관찰값인지 "
                "입력 오류인지 확인하고 분석 결과에 미치는 "
                "영향을 살펴볼 필요가 있습니다."
            )

    # --------------------------------------------------
    # 범주 쏠림
    # --------------------------------------------------

    if len(category_info) > 0:

        for _, row in category_info.iterrows():

            if row["비율(%)"] >= 80:

                warning_found = True

                st.warning(
                    f"범주 분포 확인 필요: "
                    f"'{row['변수']}' 변수에서 "
                    f"'{row['가장 많은 범주']}' 범주가 "
                    f"{row['개수']}/"
                    f"{row['유효 관찰치 수']}개 "
                    f"({row['비율(%)']}%)를 차지합니다. "
                    "이 분포가 실제 집단의 특성인지 "
                    "표본 수집 과정에서 나타난 것인지 "
                    "확인한 뒤 해석해야 합니다."
                )

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

    # ==================================================
    # 6. 데이터 맥락 점검
    # ==================================================

    st.subheader(
        "6. 데이터 맥락 점검"
    )

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

    checked_count = sum(
        context_checks
    )

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
            "확인하지 않은 내용을 모르는 상태에서 "
            "분석 결과를 과도하게 일반화하지 않도록 주의하세요."
        )

    # ==================================================
    # 7. 최종 점검 요약
    # ==================================================

    st.subheader(
        "7. 최종 점검 요약"
    )

    high_missing_variables = []
    low_missing_variables = []

    for column in data.columns:

        count = int(
            missing_count[column]
        )

        if count == 0:
            continue

        ratio = float(
            missing_ratio[column]
        )

        if ratio >= 10:

            high_missing_variables.append(
                column
            )

        else:

            low_missing_variables.append(
                column
            )

    outlier_variables = [
        column
        for column, values
        in outlier_details.items()
        if len(values) > 0
    ]

    imbalance_variables = []

    if len(category_info) > 0:

        imbalance_variables = (
            category_info[
                category_info["비율(%)"] >= 80
            ]["변수"]
            .tolist()
        )

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
                f"주의 필요 "
                f"{len(high_missing_variables)}개 변수 "
                f"({', '.join(map(str, high_missing_variables))})"
            ),
            "수준": "주의"
        })

    if len(low_missing_variables) > 0:

        summary_rows.append({
            "점검 항목": "결측치",
            "결과": (
                f"낮은 비율 "
                f"{len(low_missing_variables)}개 변수 "
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

    summary_data = pd.DataFrame(
        summary_rows
    )

    st.dataframe(
        summary_data,
        hide_index=True,
        use_container_width=True
    )

    st.info(
        "이 결과는 데이터의 품질을 합격·불합격으로 판정하거나 "
        "신뢰도 점수를 계산한 것이 아닙니다. "
        "자동 점검 결과와 데이터의 출처, 수집 목적, "
        "표본 추출 방식, 측정 기준을 함께 고려하여 해석하세요."
    )
