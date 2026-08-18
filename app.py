    # 6. 데이터 맥락 점검
    st.subheader("6. 데이터 맥락 점검")

    st.write(
        "CSV 파일만으로는 데이터의 출처나 수집 과정을 확인할 수 없습니다. "
        "아래 항목을 직접 점검해 보세요."
    )

    source_checked = st.checkbox(
        "데이터의 출처와 작성 기관을 확인했다."
    )

    purpose_checked = st.checkbox(
        "데이터가 어떤 목적으로 수집되었는지 확인했다."
    )

    sampling_checked = st.checkbox(
        "조사 대상과 표본 추출 방식을 확인했다."
    )

    time_checked = st.checkbox(
        "데이터가 언제 수집되었는지 확인했다."
    )

    definition_checked = st.checkbox(
        "각 변수의 의미와 측정 기준을 확인했다."
    )

    context_checks = [
        source_checked,
        purpose_checked,
        sampling_checked,
        time_checked,
        definition_checked
    ]

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
