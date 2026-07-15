import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 안내 서비스")

uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV 업로드",
    type="csv"
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file, encoding="cp949")

    # 위도/경도 없는 데이터 제거
    df = df.dropna(subset=["위도", "경도"])

    st.success(f"총 {len(df)}개의 주차장 정보를 불러왔습니다.")

    ##############################################
    # 주소 검색
    ##############################################

    st.header("📍 주소 검색")

    keyword = st.text_input("주소를 입력하세요")

    if keyword:

        result = df[df["주소"].str.contains(keyword, na=False)]

        if len(result) == 0:
            st.warning("검색 결과가 없습니다.")

        else:

            st.subheader("검색 결과")

            for _, row in result.iterrows():

                st.markdown(f"""
### {row['주차장명']}

**주소** : {row['주소']}

**기본요금** : {row['기본 주차 요금']}원

**기본시간** : {row['기본 주차 시간(분 단위)']}분

**추가요금** : {row['추가 단위 요금']}원

**추가시간** : {row['추가 단위 시간(분 단위)']}분

**일 최대요금** : {row['일 최대 요금']}원
""")

    ##############################################
    # 지도
    ##############################################

    st.header("🗺️ 공영주차장 지도")

    m = folium.Map(
        location=[37.5665,126.9780],
        zoom_start=11
    )

    for _, row in df.iterrows():

        popup = f"""
<b>{row['주차장명']}</b><br>

주소 : {row['주소']}<br>

기본요금 : {row['기본 주차 요금']}원<br>

기본시간 : {row['기본 주차 시간(분 단위)']}분
"""

        tooltip = f"""
{row['주차장명']}
<br>
{row['주소']}
<br>
{row['기본 주차 요금']}원
"""

        folium.Marker(
            location=[row["위도"], row["경도"]],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=1200,
        height=700
    )
