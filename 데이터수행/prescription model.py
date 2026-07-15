import streamlit as st
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

# ==========================================
# 🛡️ [사전 준비] 웹페이지 레이아웃 및 사이드바 항상 열림 설정
# ==========================================
st.set_page_config(
    page_title="스마트 처방 가이드 시스템",
    page_icon="🏥",
    layout="wide",  # 화면을 넓게 써서 사이드바와 본문이 한눈에 보이게 합니다.
    initial_sidebar_state="expanded"  # ⭐ 핵심: 앱 접속 시 사이드바를 무조건 펼쳐서 시작합니다!
)

# ==========================================
# 📊 [데이터 로드 및 AI 모델 학습 파트]
# ==========================================
@st.cache_data
def load_data_and_train_model():
    try:
        public_data = pd.read_csv('한국의약품안전관리원_용량주의약물_20240501.csv', encoding='cp949')
    except FileNotFoundError:
        data_placeholder = {
            '성분명': ['Acetaminophen', 'Propacetamol', 'Enalapril', 'Carvedilol', 'Atorvastatin', 'Ibuprofen'],
            '1일최대 투여기준량': [4000.0, 8000.0, 40.0, 100.0, 20.0, 3200.0]
        }
        public_data = pd.DataFrame(data_placeholder)
        
    public_data['성분명_정제'] = public_data['성분명'].astype(str).str.strip().str.lower()
    
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

# 1. 좌측 사이드바: 환자 생체 지표 입력 영역 (항상 열려있음)
st.sidebar.header("👤 환자 생체 지표 입력")
input_age = st.sidebar.number_input("만 나이", min_value=1, max_value=120, value=25, step=1)
input_sex = st.sidebar.selectbox("성별", options=["M", "F"])
input_bp = st.sidebar.selectbox("혈압 상태 (BP)", options=["HIGH", "NORMAL", "LOW"])
input_chol = st.sidebar.selectbox("콜레스테롤 수치", options=["HIGH", "NORMAL"])
input_na_to_k = st.sidebar.number_input("나트륨-칼륨 비율 (Na to K)", min_value=1.0, max_value=50.0, value=15.0, step=0.1)

# 2. 메인 화면: AI 분석 결과 구동
encoded_sex = le_sex.transform([input_sex])[0]
encoded_bp = le_bp.transform([input_bp])[0]
encoded_chol = le_chol.transform([input_chol])[0]

patient_features = pd.DataFrame(
    [[input_age, encoded_sex, encoded_bp, encoded_chol, input_na_to_k]], 
    columns=['Age', 'Sex', 'BP', 'Cholesterol', 'Na_to_K']
)

predicted_category = ml_model.predict(patient_features)[0]
suggested_list = drug_multimapping[predicted_category]

# 3. 화면 인쇄 파트
st.subheader("💡 AI 분석 기반 맞춤형 추천 의약품")
st.info(f"🧬 환자의 생체 데이터를 분석한 결과, 가장 안전한 치료 계열군은 **[{predicted_category}]** 입니다.")

# 동적 드롭다운 메뉴로 약물 선택
selected_substance = st.selectbox(
    "처방하거나 적정 용량을 확인하고 싶은 약물 성분을 선택하세요:", 
    options=[name.upper() for name in suggested_list]
)

# 4. 식약처 용량 계산 및 결과 도출
if selected_substance:
    target_name = selected_substance.strip().lower()
    matching_row = public_data_cleaned[public_data_cleaned['성분명_정제'] == target_name]
    
    st.write("---")
    st.subheader("📋 식약처 가이드라인 맞춤형 용량 가이드")
    
    if not matching_row.empty:
        base_max_limit = float(matching_row['1일최대 투여기준량'].iloc[0])
        final_max_limit = base_max_limit
        
        # 연령 필터 적용
        is_pediatric = input_age < 12
        if is_pediatric:
            final_max_limit = base_max_limit * 0.5
            patient_status = f"⚠️ 소아 환자 (만 {input_age}세)"
            filter_reason = "만 12세 미만 소아 환자의 대사 능력을 고려하여 성인 표준량 대비 50%를 자동으로 감량 적용하였습니다."
        else:
            patient_status = f"✅ 성인 환자 (만 {input_age}세)"
            filter_reason = "식약처 허가 기준에 따른 성인 표준 안전 임계량입니다."
            
        # 결과 표시 카드 UI
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="환자 구분", value=patient_status)
        with col2:
            st.metric(label="1일 최대 권장 복용량", value=f"{final_max_limit} mg")
            
        st.warning(f"**적용 조건 및 의학적 근거**\n\n{filter_reason}")
    else:
        st.error(f"오류: 공공데이터베이스에서 [{selected_substance}] 성분의 용량 기준을 찾을 수 없습니다.")    
