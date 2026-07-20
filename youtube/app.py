import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import re
from datetime import datetime

# --- 스트림릿 페이지 설정 및 한글 폰트 설정 ---
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")

# 리눅스(스트림릿 클라우드) 환경에서 한글 깨짐 방지를 위한 matplotlib 설정
plt.rcParams['font.family'] = 'NanumBarunGothic' # 스트림릿 클라우드 기본 내장 한글 폰트 시도
plt.rcParams['axes.unicode_minus'] = False

# --- 유튜브 API 관련 함수 ---
def get_video_id(url):
    """유튜브 URL에서 Video ID 추출"""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_youtube_comments(api_key, video_id, max_count):
    """유튜브 댓글 가져오기"""
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_count, 100), # 한 번에 최대 100개
            textFormat="plainText"
        )
        
        while request and len(comments) < max_count:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'like_count': comment['likeCount'],
                    'published_at': pd.to_datetime(comment['publishedAt'])
                })
                if len(comments) >= max_count:
                    break
                    
            # 다음 페이지가 있으면 계속 가져옴
            if 'nextPageToken' in response and len(comments) < max_count:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=min(max_count - len(comments), 100),
                    textFormat="plainText"
                )
            else:
                break
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return None

# --- 메인 앱 UI ---
st.title("📊 유튜브 댓글 종합 분석기")
st.markdown("유튜브 영상의 댓글을 분석하여 **시간대별 추이, 좋아요 반응도, 키워드 워드클라우드**를 제공합니다.")
st.markdown("---")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
video_url = st.sidebar.text_input("유튜브 영상 링크(URL)를 입력하세요")
max_comments = st.sidebar.slider("가져올 댓글 개수 설정", min_value=10, max_value=500, value=100, step=10)

if st.sidebar.button("분석 시작🚀"):
    if not api_key:
        st.warning("API Key를 입력해주세요.")
    elif not video_url:
        st.warning("유튜브 영상 링크를 입력해주세요.")
    else:
        video_id = get_video_id(video_url)
        
        if not video_id:
            st.error("올바른 유튜브 URL이 아닙니다. 다시 확인해주세요.")
        else:
            # 영상 보여주기
            st.subheader("📺 분석 대상 영상")
            st.video(video_url)
            
            # 데이터 로딩 스피너
            with st.spinner("댓글을 불러오고 분석하는 중입니다... 잠시만 기다려주세요."):
                df = get_youtube_comments(api_key, video_id, max_comments)
                
            if df is not None and not df.empty:
                st.success(f"총 {len(df)}개의 댓글을 성공적으로 가져왔습니다!")
                
                # 데이터 탭 구성
                tab1, tab2, tab3, tab4 = st.tabs(["💬 댓글 데이터", "📈 시간대별 추이", "❤️ 댓글 반응도", "☁️ 워드 클라우드"])
                
                # Tab 1: 댓글 데이터 원본
                with tab1:
                    st.subheader("수집된 댓글 목록")
                    st.dataframe(df[['author', 'text', 'like_count', 'published_at']], use_container_width=True)
                
                # Tab 2: 시간대별 작성 추이
                with tab2:
                    st.subheader("📈 시간대별 댓글 작성 추이")
                    # 날짜별로 그룹화 (스트림릿 내장 차트 사용으로 폰트 깨짐 방지)
                    df['date'] = df['published_at'].dt.date
                    date_counts = df.groupby('date').size().reset_index(name='댓글 수')
                    date_counts = date_counts.set_index('date')
                    st.line_chart(date_counts)
                
                # Tab 3: 댓글 반응도 (좋아요 수가 높은 댓글)
                with tab3:
                    st.subheader("❤️ 가장 반응이 좋은 댓글 (좋아요 순)")
                    top_liked = df.sort_values(by='like_count', ascending=False).head(10)
                    for idx, row in top_liked.iterrows():
                        st.markdown(f"**{row['author']}** (👍 {row['like_count']}개)")
                        st.caption(f"작성일: {row['published_at']}")
                        st.info(row['text'])
                        st.markdown("---")
                
                # Tab 4: 한글 워드 클라우드
                with tab4:
                    st.subheader("☁️ 한글 키워드 워드 클라우드")
                    
                    # 한글 텍스트 정제 및 명사 추출
                    okt = Okt()
                    all_text = " ".join(df['text'].astype(str))
                    # 한글만 남기기
                    ko_text = re.sub(r'[^가-힣\s]', '', all_text)
                    
                    # 명사 추출 (2글자 이상만)
                    nouns = okt.nouns(ko_text)
                    words = [n for n in nouns if len(n) > 1]
                    
                    if len(words) > 0:
                        word_str = " ".join(words)
                        
                        # 리눅스 환경에 기본 내장된 맑은고딕/나눔고딕 계열 폰트 경로 지정 (스트림릿 클라우드 대응)
                        # 보통 리눅스 서버에는 폰트가 없을 수 있으므로 font_path를 지정하지 않거나 기본값 사용 시 에러 예방을 위해 정의
                        try:
                            # 스트림릿 클라우드(Debian 기반)의 기본 나눔폰트 경로 적용 시도
                            font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'
                            wc = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate(word_str)
                        except:
                            # 폰트 로드 실패시 기본 폰트 적용 (네모 깨짐이 발생할 수 있으므로, 가급적 폰트 설치 권장)
                            wc = WordCloud(width=800, height=400, background_color='white').generate(word_str)
                            
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wc, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    else:
                        st.warning("분석할 만한 한글 명사 단어가 부족합니다.")
            else:
                st.error("댓글을 가져오지 못했거나 댓글이 없는 영상입니다.")
