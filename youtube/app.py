
    import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import re

# --- 스트림릿 페이지 설정 및 한글 폰트 설정 ---
st.set_page_config(page_title="유튜브 댓글 종합 분석기", layout="wide")

# 리눅스(스트림릿 클라우드) 환경에서 한글 깨짐 방지를 위한 matplotlib 설정
plt.rcParams['font.family'] = 'NanumBarunGothic' 
plt.rcParams['axes.unicode_minus'] = False

# --- Secrets에서 API 키 자동 가져오기 ---
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("⚠️ 스트림릿 클라우드의 Secrets 설정에 'YOUTUBE_API_KEY'를 등록해주세요.")
    st.stop()

# --- 유튜브 API 관련 함수 ---
def get_video_id(url):
    """유튜브 URL에서 Video ID 추출"""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_video_details(video_id):
    """영상의 기본 정보(조회수, 좋아요 수, 제목 등) 가져오기"""
    youtube = build("youtube", "v3", developerKey=API_KEY)
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        if response['items']:
            item = response['items'][0]
            return {
                'title': item['snippet']['title'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0)),
                'channel': item['snippet']['channelTitle']
            }
    except Exception as e:
        st.error(f"영상 정보를 가져오는 중 오류 발생: {e}")
    return None

def get_youtube_comments(video_id, max_count):
    """유튜브 댓글 가져오기"""
    youtube = build("youtube", "v3", developerKey=API_KEY)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_count, 100),
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
        st.error(f"댓글을 가져오는 중 오류가 발생했습니다: {e}")
        return None

# --- 간이 감성 분석 함수 ---
def analyze_sentiment(text):
    """간단한 규칙 기반 긍정/부정 감성 분석"""
    # 긍정/부정 단어 사전 정의
    pos_words = ['좋다', '최고', '대박', '재밌다', '유익', '감사', '사랑', '응원', '짱', '존멋', '꿀잼', '추천', '화이팅', '👍', '❤️']
    neg_words = ['싫다', '노잼', '실망', '최악', '짜증', '불편', '삭제', '지루', '노답', '에휴', '별로', '안좋다', '👎', '아쉽']
    
    pos_score = sum(1 for word in pos_words if word in text)
    neg_score = sum(1 for word in neg_words if word in text)
    
    if pos_score > neg_score:
        return '긍정'
    elif neg_score > pos_score:
        return '부정'
    else:
        return '중립'

# --- 메인 앱 UI ---
st.title("📊 유튜브 댓글 및 영상 종합 분석기")
st.markdown("API 키가 자동으로 연결되었습니다. 유튜브 영상 링크를 입력하고 분석을 시작하세요!")
st.markdown("---")

# 사이드바 설정 (API 키 입력창 제거)
st.sidebar.header("⚙️ 설정")
video_url = st.sidebar.text_input("유튜브 영상 링크(URL)를 입력하세요")
max_comments = st.sidebar.slider("분석할 댓글 개수 설정", min_value=10, max_value=500, value=100, step=10)

if st.sidebar.button("분석 시작 🚀"):
    if not video_url:
        st.warning("유튜브 영상 링크를 입력해주세요.")
    else:
        video_id = get_video_id(video_url)
        
        if not video_id:
            st.error("올바른 유튜브 URL이 아닙니다. 다시 확인해주세요.")
        else:
            # 1. 영상 기본 정보 가져오기 및 출력
            video_info = get_video_details(video_id)
            
            if video_info:
                st.subheader(f"📺 {video_info['title']}")
                st.caption(f"채널명: {video_info['channel']}")
                
                # 대시보드 지표 (조회수, 좋아요 등)
                col1, col2, col3 = st.columns(3)
                col1.metric("👀 총 조회수", f"{video_info['view_count']:,}회")
                col2.metric("❤️ 좋아요 수", f"{video_info['like_count']:,}개")
                col3.metric("💬 전체 댓글 수", f"{video_info['comment_count']:,}개")
                
                # 영상 임베드
                st.video(video_url)
                st.markdown("---")
            
            # 2. 댓글 데이터 로딩 및 분석
            with st.spinner("댓글을 불러오고 분석하는 중입니다... 잠시만 기다려주세요."):
                df = get_youtube_comments(video_id, max_comments)
                
            if df is not None and not df.empty:
                # 감성 분석 적용
                df['sentiment'] = df['text'].apply(analyze_sentiment)
                
                st.success(f"요청하신 {len(df)}개의 댓글을 성공적으로 분석했습니다!")
                
                # 데이터 탭 구성
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "💬 댓글 데이터", "📈 시간대별 작성 추이", "🎭 댓글 반응도 (긍정/부정)", "❤️ 인기 댓글", "☁️ 워드 클라우드"
                ])
                
                # Tab 1: 댓글 데이터 원본
                with tab1:
                    st.subheader("수집된 댓글 목록")
                    st.dataframe(df[['author', 'text', 'sentiment', 'like_count', 'published_at']], use_container_width=True)
                
                # Tab 2: 시간대별 작성 추이 (연월일시 단위로 시계열 시각화)
                with tab2:
                    st.subheader("📈 시간대별 댓글 작성 추이")
                    # 시간대별(Hour 단위) 데이터 분할
                    df['hour'] = df['published_at'].dt.strftime('%Y-%m-%d %H:00')
                    hour_counts = df.groupby('hour').size().reset_index(name='댓글 작성 수')
                    hour_counts = hour_counts.set_index('hour')
                    st.line_chart(hour_counts)
                
                # Tab 3: 댓글 반응도 (긍정/부정 비율)
                with tab3:
                    st.subheader("🎭 댓글 감성 반응도")
                    sentiment_counts = df['sentiment'].value_counts()
                    
                    # 스트림릿 내장 바차트로 시각화 (한글 깨짐 없음)
                    st.bar_chart(sentiment_counts)
                    
                    # 비율 출력
                    c1, c2, c3 = st.columns(3)
                    c1.metric("긍정 댓글", f"{sentiment_counts.get('긍정', 0)}개", f"{sentiment_counts.get('긍정', 0)/len(df)*100:.1f}%")
                    c2.metric("중립 댓글", f"{sentiment_counts.get('중립', 0)}개", f"{sentiment_counts.get('중립', 0)/len(df)*100:.1f}%")
                    c3.metric("부정 댓글", f"{sentiment_counts.get('부정', 0)}개", f"{sentiment_counts.get('부정', 0)/len(df)*100:.1f}%")
                
                # Tab 4: 좋아요 기준 인기 댓글
                with tab4:
                    st.subheader("❤️ 가장 반응이 좋은 댓글 (좋아요 순)")
                    top_liked = df.sort_values(by='like_count', ascending=False).head(10)
                    for idx, row in top_liked.iterrows():
                        # 감성에 따른 색상 태그 설정
                        sentiment_emoji = "🟢" if row['sentiment'] == '긍정' else "🔴" if row['sentiment'] == '부정' else "⚪"
                        st.markdown(f"**{row['author']}** (👍 {row['like_count']}개) {sentiment_emoji} [{row['sentiment']}]")
                        st.caption(f"작성일: {row['published_at']}")
                        st.info(row['text'])
                        st.markdown("---")
                
                # Tab 5: 한글 워드 클라우드
                with tab5:
                    st.subheader("☁️ 한글 키워드 워드 클라우드")
                    
                    okt = Okt()
                    all_text = " ".join(df['text'].astype(str))
                    ko_text = re.sub(r'[^가-힣\s]', '', all_text)
                    
                    nouns = okt.nouns(ko_text)
                    # 제외할 의미 없는 단어(불용어)가 있다면 리스트에 추가하세요
                    stop_words = ['영상', '진짜', '정말', '보고', '하나', '생각', '이거', '정말', '종합']
                    words = [n for n in nouns if len(n) > 1 and n not in stop_words]
                    
                    if len(words) > 0:
                        word_str = " ".join(words)
                        try:
                            # packages.txt를 통해 설치된 나눔바른고딕 폰트 경로 적용
                            font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'
                            wc = WordCloud(font_path=font_path, width=900, height=450, background_color='white').generate(word_str)
                        except:
                            # 로컬 테스트 환경 등 예외 상황용 기본 폰트 fallback
                            wc = WordCloud(width=900, height=450, background_color='white').generate(word_str)
                            
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.imshow(wc, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    else:
                        st.warning("분석할 만한 한글 명사 단어가 부족합니다.")
            else:
                st.error("댓글을 가져오지 못했거나 댓글 기능이 차단된 영상입니다.")
