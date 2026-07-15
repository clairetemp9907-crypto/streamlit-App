import streamlit as st
import pandas as pd
import numpy as np
import folium

from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="공영주차장 안내", layout="wide")

st.title("🚗 공영주차장 추천 서비스")

############################################################
# 캐릭터
############################################################

col1, col2 = st.columns([1,3])

with col1:
    st.image("character.png", width=220)

with col2:
    st.info("💬 **지금 어디야?**\n\n현재 주소를 입력해줘!")

############################################################
# CSV 업로드
############################################################

uploaded_file = st.file_uploader(
    "공영주차장 CSV 업로드",
    type="csv"
)

if uploaded_file is None:
    st.stop()

df = pd.read_csv(uploaded_file, encoding="cp949")

df = df.dropna(subset=["위도","경도"])

############################################################
# 주소 입력
############################################################

address = st.text_input("현재 주소 입력")

if address == "":
    st.stop()

############################################################
# 주소 → 위도경도
############################################################

geolocator = Nominatim(user_agent="parking_app")

location = geolocator.geocode(address)

if location is None:
    st.error("주소를 찾을 수 없습니다.")
    st.stop()

user_lat = location.latitude
user_lon = location.longitude

############################################################
# 거리 계산
############################################################

distances = []

for idx,row in df.iterrows():

    d = geodesic(
        (user_lat,user_lon),
        (row["위도"],row["경도"])
    ).km

    distances.append(d)

df["거리(km)"] = distances

nearest = df.sort_values("거리(km)").head(3)

############################################################
# 추천 결과
############################################################

st.header("📍 가장 가까운 공영주차장 TOP3")

for i,row in nearest.iterrows():

    st.subheader(row["주차장명"])

    st.write("📍 주소 :",row["주소"])
    st.write(f"📏 거리 : {row['거리(km)']:.2f} km")
    st.write(f"💰 기본요금 : {row['기본 주차 요금']}원")
    st.write(f"⏰ 기본시간 : {row['기본 주차 시간(분 단위)']}분")
    st.write(f"➕ 추가요금 : {row['추가 단위 요금']}원")
    st.write(f"💵 일 최대요금 : {row['일 최대 요금']}원")

    st.divider()

############################################################
# 지도
############################################################

m = folium.Map(
    location=[user_lat,user_lon],
    zoom_start=14
)

# 사용자 위치
folium.Marker(
    [user_lat,user_lon],
    tooltip="현재 위치",
    icon=folium.Icon(color="red")
).add_to(m)

# 추천 주차장
for _,row in nearest.iterrows():

    tooltip = f"""
<b>{row['주차장명']}</b><br>
{row['주소']}<br>
기본요금 : {row['기본 주차 요금']}원
"""

    popup = f"""
<h4>{row['주차장명']}</h4>

주소 : {row['주소']}<br>

거리 : {row['거리(km)']:.2f} km<br>

기본요금 : {row['기본 주차 요금']}원<br>

기본시간 : {row['기본 주차 시간(분 단위)']}분
"""

    folium.Marker(
        [row["위도"],row["경도"]],
        tooltip=tooltip,
        popup=popup,
        icon=folium.Icon(color="blue")
    ).add_to(m)

st_folium(m,width=1000,height=600)
