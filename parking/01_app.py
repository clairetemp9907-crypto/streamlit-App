import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="공영주차장 추천", layout="wide")

st.title("🚗 공영주차장 추천 서비스")

####################################
# 캐릭터
####################################

st.sidebar.header("캐릭터")

character = st.sidebar.file_uploader(
    "캐릭터 이미지를 업로드하세요",
    type=["png","jpg","jpeg"]
)

if character is not None:
    st.sidebar.image(character, width=220)

st.info("💬 지금 어디야? 현재 주소를 입력해줘!")

####################################
# CSV 업로드
####################################

uploaded_file = st.file_uploader(
    "공영주차장 CSV 업로드",
    type="csv"
)

if uploaded_file is None:
    st.stop()

####################################
# CSV 읽기
####################################

try:
    df = pd.read_csv(uploaded_file, encoding="cp949")
except:
    df = pd.read_csv(uploaded_file, encoding="utf-8")

####################################
# 컬럼명 확인
####################################

required = [
    "주차장명",
    "주소",
    "위도",
    "경도",
    "기본 주차 요금",
    "기본 주차 시간(분 단위)"
]

for c in required:
    if c not in df.columns:
        st.error(f"'{c}' 컬럼이 없습니다.")
        st.stop()

df = df.dropna(subset=["위도","경도"])

####################################
# 주소 입력
####################################

address = st.text_input("현재 주소를 입력하세요")

if address == "":
    st.stop()

####################################
# 주소 → 좌표
####################################

geolocator = Nominatim(user_agent="parking")

location = geolocator.geocode(address)

if location is None:
    st.error("주소를 찾을 수 없습니다.")
    st.stop()

user = (location.latitude, location.longitude)

####################################
# 거리 계산
####################################

distance_list = []

for _, row in df.iterrows():

    d = geodesic(
        user,
        (row["위도"], row["경도"])
    ).km

    distance_list.append(d)

df["거리"] = distance_list

nearest = df.sort_values("거리").head(3)

####################################
# 추천 결과
####################################

st.header("🏆 가장 가까운 공영주차장")

for i, (_, row) in enumerate(nearest.iterrows(), start=1):

    st.markdown(f"""
### {i}위 : {row['주차장명']}

📍 주소 : {row['주소']}

📏 거리 : **{row['거리']:.2f} km**

💰 기본요금 : **{row['기본 주차 요금']}원**

⏰ 기본시간 : **{row['기본 주차 시간(분 단위)']}분**
""")

####################################
# 지도
####################################

m = folium.Map(
    location=user,
    zoom_start=14
)

folium.Marker(
    user,
    tooltip="현재 위치",
    icon=folium.Icon(color="red")
).add_to(m)

for _, row in nearest.iterrows():

    tooltip = f"""
{row['주차장명']}

{row['주소']}

기본요금 : {row['기본 주차 요금']}원
"""

    popup = f"""
<b>{row['주차장명']}</b><br>
주소 : {row['주소']}<br>
거리 : {row['거리']:.2f} km<br>
기본요금 : {row['기본 주차 요금']}원
"""

    folium.Marker(
        [row["위도"], row["경도"]],
        tooltip=tooltip,
        popup=popup,
        icon=folium.Icon(color="blue")
    ).add_to(m)

st_folium(m, width=1000, height=650)
