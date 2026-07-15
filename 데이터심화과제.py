import streamlit as st
import pandas as pd
import numpy as np
# 학습된 모델과 라벨인코더를 불러오기 위한 라이브러리 (기존 모델 로드 코드 유지 가정)
# 만약 코랩에서 모델을 파일로 저장하지 않았다면, 여기서는 간결한 데모를 위해 임시 추론 객체나 규칙 기반 매칭을 활용하도록 설계했습니다.
# (발표 장소 및 배포의 용이성을 위해 학습된 Decision Tree의 논리를 그대로 재현한 가벼운 룰 엔진을 기본 내장했습니다.)

# Page 설정
st.set_page_config(
    page_title="스마트 투약 모니터링 시스템",
    page_icon="🏥",
    layout="centered"
)

# 1. 실제 임상 약학 데이터베이스 구축
clinical_drug_db = {
    'DrugY': {
        'class': '루프 이뇨제 (전해질 배출 조절 및 체액량 감소)',
        'primary': {
            'name': 'Furosemide (푸로세미드)',
            'adult_limit': 80.0,
            'pediatric_limit': 40.0,
            'feature': '신속한 전해질 배출 효과가 우수하여 응급 처방에 다수 활용됨.'
        },
        'alternative': {
            'name': 'Torsemide (토르세미드)',
            'adult_limit': 20.0,
            'pediatric_limit': 10.0,
            'feature': '푸로세미드 대비 작용 시간이 길고 생체 이용률이 일정하여 장기 복용에 유리함.'
        }
    },
    'drugA': {
        'class': 'ACE 억제제 계열 고혈압 치료제 (호르몬성 고혈압 타겟)',
        'primary': {
            'name': 'Enalapril (에날라프릴)',
            'adult_limit': 40.0,
            'pediatric_limit': 20.0,
            'feature': '젊은 층의 본태성 고혈압 및 심부전 보호에 우수한 임상 데이터 보유.'
        },
        'alternative': {
            'name': 'Lisinopril (리시노프릴)',
            'adult_limit': 40.0,
            'pediatric_limit': 20.0,
            'feature': '간 대사(First-pass metabolism)를 거치지 않아 간 기능 저하 환자에게 안전함.'
        }
    },
    'drugB': {
        'class': '칼슘채널차단제(CCB) 계열 고혈압 치료제 (노화된 혈관 확장 타겟)',
        'primary': {
            'name': 'Amlodipine (암로디핀)',
            'adult_limit': 10.0,
            'pediatric_limit': 5.0,
            'feature': '가장 보편적인 고혈압 약으로, 반감기가 길어 1일 1회 복용으로 혈압이 안정됨.'
        },
        'alternative': {
            'name': 'Nifedipine (니페디핀)',
            'adult_limit': 90.0,
            'pediatric_limit': 45.0,
            'feature': '강력한 평활근 이완 작용을 유도하나, 부작용으로 두통이나 발목 부종이 발생할 수 있음.'
        }
    },
    'drugC': {
        'class': '스타틴 계열 고지혈증 치료제 (간 내 콜레스테롤 합성 억제)',
        'primary': {
            'name': 'Atorvastatin (아토르바스타틴)',
            'adult_limit': 80.0,
            'pediatric_limit': 40.0,
            'feature': '전 세계에서 가장 널리 검증된 고지혈증 치료제로 심혈관 질환 예방율이 높음.'
        },
        'alternative': {
            'name': 'Rosuvastatin (로수바스타틴)',
            'adult_limit': 20.0,
            'pediatric_limit': 10.0,
            'feature': '약효 강도(Potency)가 매우 강해 저용량으로도 강력한 LDL-C 강하 효과를 보임.'
        }
    },
    'drugX': {
        'class': 'NSAIDs 계열 소염진통제 (염증 반응 및 통증 차단)',
        'primary': {
            'name': 'Ibuprofen (이부프로펜)',
            'adult_limit': 3200.0,
            'pediatric_limit': 1600.0,
            'feature': '해열 및 소염진통 효과가 조화로워 감기몸살, 관절염 등 범용적으로 처방됨.'
        },
        'alternative': {
            'name': 'Naproxen (나프록센)',
            'adult_limit': 1250.0,
            'pediatric_limit': 625.0,
            'feature': '약효 지속시간이 최대 12시간으로 매우 길어 만성 염증이나 치통, 생리통에 강점이 있음.'
        }
    }
}

# Decision Tree 분류 규칙 재현 엔진 (배포용 경량화 로직)
def predict_drug_label(age, bp, cholesterol, na_to_k):
    if na_to_k > 15.0:
        return 'DrugY'
    else:
        if bp == 'HIGH':
            if age < 50:
                return 'drugA'
            else:
                return 'drugB'
        elif bp == 'NORMAL' or bp == 'LOW':
            if cholesterol == 'HIGH':
                return 'drugC'
            else:
                return 'drugX'
    return 'drugX'

# --- UI 화면 디자인 ---

st.title("🏥 실시간 스마트 투약 모니터링 시스템")
st.markdown("환자의 생체 데이터와 약리학 데이터베이스를 연동하여 안전한 투약 가이드를 제시합니다.")
st.write("---")

# 1단계: 환자 생체정보 입력받기 (좌우 레이아웃 분할)
st.subheader("👤 1. 환자 생체 지표 입력")
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("만 나이 (Age)", min_value=1, max_value=120, value=25, step=1)
    sex = st.selectbox("성별 (Sex)", ["M", "F"])
    bp = st.selectbox("혈압 상태 (BP)", ["HIGH", "NORMAL", "LOW"])

with col2:
    cholesterol = st.selectbox("콜레스테롤 수치 (Cholesterol)", ["NORMAL", "HIGH"])
    na_to_k = st.number_input("나트륨-칼륨 비율 (Na to K Ratio)", min_value=1.0, max_value=50.0, value=11.5, step=0.1)

st.write("")

# 분석 및 추천 실행 버튼
if st.button("🩺 맞춤 약물 처방 진단하기"):
    st.session_state['processed'] = True
    # 예측 수행 및 결과를 세션 스테이트에 임시 저장
    predicted_label = predict_drug_label(age, bp, cholesterol, na_to_k)
    st.session_state['predicted_label'] = predicted_label
    st.session_state['patient_age'] = age

# 처방 진단이 실행되었을 때만 하단 추천창 활성화
if st.session_state.get('processed', False):
    st.write("---")
    st.subheader("▶ 2. AI 임상 약물 다중 추천 결과")
    
    label = st.session_state['predicted_label']
    drug_family = clinical_drug_db[label]
    
    st.info(f"**추천 약물 계열:** {drug_family['class']}")
    
    # 1순위 / 2순위 약물 선택지 제공
    primary_name = drug_family['primary']['name']
    alt_name = drug_family['alternative']['name']
    
    col_p, col_a = st.columns(2)
    with col_p:
        st.markdown(f"### ⭐️ 1순위 권장약\n**{primary_name}**")
        st.caption(drug_family['primary']['feature'])
    with col_a:
        st.markdown(f"### 🔄 2순위 대체약\n**{alt_name}**")
        st.caption(drug_family['alternative']['feature'])
        
    st.write("")
    st.write("---")
    st.subheader("▶ 3. 환자 맞춤형 투약량 실시간 검증")
    
    # 환자가 직접 약물 선택하기
    chosen_option = st.radio(
        "투약할 약물 성분을 하나 선택하세요:",
        options=[f"1순위: {primary_name}", f"2순위: {alt_name}"]
    )
    
    # 선택된 약동학 데이터 추출
    if "1순위" in chosen_option:
        selected_drug_info = drug_family['primary']
    else:
        selected_drug_info = drug_family['alternative']
        
    # 만 12세 미만 소아 감량선 계산
    patient_age = st.session_state['patient_age']
    is_pediatric = patient_age < 12
    
    if is_pediatric:
        final_limit = selected_drug_info['pediatric_limit']
        st.warning(f"⚠️ **소아 환자 보호 필터 활성화:** 만 {patient_age}세 소아 기준이 적용되어 안전 한계량이 50% 감량되었습니다.")
    else:
        final_limit = selected_drug_info['adult_limit']
        st.success(f"✅ **성인 표준 기준 적용:** 만 {patient_age}세 환자의 투약 기준입니다.")
        
    st.metric(label="이 환자의 하루 최대 안전 투약 한계량", value=f"{final_limit} mg")
    
    # 투약하려는 양 입력
    dosage_input = st.number_input(
        "하루 투약 예정량 (mg)을 입력해 주세요:", 
        min_value=0.0, 
        value=float(final_limit * 0.8), 
        step=1.0
    )
    
    # 최종 실시간 처방 가이드 판정
    if st.button("🛡️ 실시간 안전성 최종 승인"):
        if dosage_input > final_limit:
            over_mg = dosage_input - final_limit
            over_percent = (over_mg / final_limit) * 100
            st.error(f"""
            ### 🚨 [투약 불가 - 용량 초과 경고]
            - **투약 요청량:** {dosage_input} mg  
            - **안전 제한량:** {final_limit} mg (**{over_mg:.1f} mg 초과**, {over_percent:.1f}% 과다 투여)
            - **경고:** 해당 용량 복용 시 급성 신부전, 간 손상 및 혈역학적 부작용 위험이 매우 높으므로 처방을 승인하지 않습니다.
            """)
        else:
            safety_ratio = (dosage_input / final_limit) * 100
            st.success(f"""
            ### ✅ [투약 승인 - 안전]
            - **투약 요청량:** {dosage_input} mg  
            - **안전 제한량:** {final_limit} mg (안전 가이드라인 충족률 {safety_ratio:.1f}%)
            - 환자의 생체 조건 및 식약처 권장 가이드라인 이내로 확인되어 처방이 안전하게 완료되었습니다.
            """)
