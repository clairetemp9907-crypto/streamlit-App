import streamlit as st
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

# ==========================================
# 🛡️ [사전 준비] 웹페이지 레이아웃 설정
# ==========================================
st.set_page_config(
    page_title="스마트 처방 가이드 시스템",
    page_icon="🏥",
    layout="centered"
)

# ==========================================
# 📊 [데이터 로드 및 AI 모델 학습 파트]
# ==========================================
@st.cache_data
def load_data_and_train_model():
    # 1. 국내 공공데이터 로드 (한글 인코딩 및 양끝 공백 전처리 완료)
    try:
        public_data = pd.read_csv('한국의약품안전관리원_용량주의약물_20240501.csv', encoding='cp949')
    except FileNotFoundError:
        # 파일이 없을 때를 대비한 백업 예외 데이터 (테스트용)
        data_placeholder = {
            '성분명': ['Acetaminophen', 'Propacetamol', 'Enalapril', 'Carvedilol', 'Atorvastatin', 'Ibuprofen'],
            '1일최대 투여기준량': [4000.0, 8000.0, 40.0, 100.0, 20.0, 3200.0]
        }
        public_data = pd.DataFrame(data_placeholder)
        
    # 💡 성분명 글자 자체의 대소문자를 완전히 소문자로 통일하고, 보이지 않는 앞뒤 공백을 완벽하게 제거합니다.
    public_data['성분명_정제'] = public_data['성분명'].astype(str).str.strip().str.lower()
    
    # 2. 캐글 약물 분류 기준 데이터 임의 학습 (데모용 무중단 모델)
    data_demo = {
        'Age': [23, 47, 56, 34, 18, 62, 73, 42],
        'Sex': ['F', 'M', 'F', 'M', 'F', 'M', 'F', 'M'],
        'BP': ['HIGH', 'NORMAL', 'HIGH', 'LOW', 'NORMAL', 'HIGH', 'LOW', 'HIGH'],
        'Cholesterol': ['HIGH', 'NORMAL', 'HIGH', 'HIGH', 'NORMAL', 'NORMAL', 'HIGH', 'NORMAL'],
        'Na_to_K': [25.3, 11.2, 8.4, 14.5, 31.2, 9.1, 7.8, 13.2],
        'Drug': ['DrugY', 'drugA', 'drugB', 'drugC', 'drugX', 'drugB', 'drugC', 'drugA']
    }
    df_demo = pd.DataFrame(data_demo)
    
    le_sex = LabelEncoder().fit(['F', 'M'])
    le_bp = LabelEncoder().fit(['HIGH', 'NORMAL', 'LOW'])
    le_chol = LabelEncoder().fit(['HIGH', 'NORMAL'])
    
    df_demo['Sex'] = le_sex.transform(df_demo['Sex'])
    df_demo['BP'] = le_bp.transform(df_demo['BP'])
    df_demo['Cholesterol'] = le_chol.transform(df_demo['Cholesterol'])
    
    X = df_demo[['Age', 'Sex', 'BP', 'Cholesterol', 'Na_to_K']]
    y = df_demo['Drug']
    
    ml_model = DecisionTreeClassifier(random_state=42)
    ml_model.fit(X, y)
    
    return public_data, ml_model, le_sex, le_bp, le_chol

public_data_cleaned, ml_model, le_sex, le_bp, le_chol = load_data_and_train_model()

# ==========================================
# 💊 [약물 매칭 가이드라인 정의]
# ==========================================
drug_multimapping = {
    'DrugY': ['acetaminophen', 'propacetamol', 'acetaminophen/pamabrom'],
    'drugA': ['enalapril', 'captopril', 'ramipril', 'alacepril'],
    'drugB': ['carvedilol', 'amlodipine', 'nifedipine', 'felodipine', 'atenolol', 'bisoprolol', 'losartan', 'valsartan', 'irbesartan'],
    'drugC': ['atorvastatin', 'rosuvastatin', 'fluvastatin', 'lovastatin', 'pitavastatin'],
    'drugX': ['ibuprofen', 'naproxen', 'dexibuprofen', 'loxoprofen', 'diclofenac']
}

# ==========================================
# 🖥️ [Streamlit 웹 화면 UI 구성]
# ==========================================
st.title("🏥 실시간 스마트 처방 가이드 시스템")
st.markdown("환자의 생체 정보 데이터를 기반으로 안전한 추천 의약품 목록과 식약처 기준 맞춤형 적정 용량을 자동 계산합니다.")
st.write("---")
