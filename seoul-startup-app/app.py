import streamlit as st
import pandas as pd
import folium
import json
from pathlib import Path
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("서울시 창업 입지 추천 시스템")
st.markdown("### 머신러닝 기반 업종별 행정동 추천 서비스")

# ----------------------------
# 데이터 로드
# ----------------------------
@st.cache_data
def load_data():
    base_path = Path(__file__).resolve().parent

    csv_path = base_path / "top5_2.csv"
    geo_path = base_path / "hangjeongdong.geojson"

    df = pd.read_csv(csv_path)

    with open(geo_path, encoding="utf-8") as f:
        geo = json.load(f)

    return df, geo

df, geo_data = load_data()

# ----------------------------
# 업종 선택
# ----------------------------
industry = st.selectbox(
    "창업할 업종을 선택하세요",
    df["업종"].unique()
)

filtered = df[df["업종"] == industry]
# 서울 평균 대비 매출지수 기준으로 정렬하여 순위 부여
top5 = filtered.sort_values("서울 평균 대비 매출지수", ascending=False).head(5)
top5 = top5.copy()
top5['순위'] = range(1, len(top5) + 1)

# ----------------------------
# 레이아웃 분할 (지도 | 리포트)
# ----------------------------
col1, col2 = st.columns([2, 1])

# ----------------------------
# 지도 영역
# ----------------------------
with col1:
    st.subheader("서울시 추천 행정동 TOP5")

    # geojson 복사 (Streamlit 재실행 버그 방지)
    geo_copy = json.loads(json.dumps(geo_data))

    m = folium.Map(location=[37.55, 126.98], zoom_start=11)

    color_map = {
        1: '#CC0000',
        2: '#E67E22',
        3: '#F1C40F',
        4: '#3498DB',
        5: '#2980B9'
    }

    top5_dict = top5.set_index('행정동').to_dict('index')

    # GeoJSON 데이터 병합
    for feature in geo_copy['features']:
        props = feature['properties']
        # adm_nm에서 동 이름만 추출 (예: "서울특별시 강남구 삼성1동" -> "삼성1동")
        dong_name = props.get('adm_nm', '').split()[-1] if props.get('adm_nm', '') else ''

        if dong_name in top5_dict:
            data = top5_dict[dong_name]

            props['is_top5'] = True
            props['rank'] = int(data['순위'])
            props['sales'] = int(data['예상매출(점포당)'])
            props['stores'] = int(data['점포_수'])

        else:
            props['is_top5'] = False
            props['rank'] = None
            props['sales'] = None
            props['stores'] = None

    # 스타일 함수
    def style_function(feature):
        props = feature['properties']

        if props.get('is_top5'):
            rank = props.get('rank')
            return {
                'fillColor': color_map.get(rank, '#CC0000'),
                'color': 'black',
                'weight': 1.5,
                'fillOpacity': 0.7
            }
        else:
            return {
                'fillColor': '#f0f0f0',
                'color': 'gray',
                'weight': 0.5,
                'fillOpacity': 0.2
            }

    folium.GeoJson(
        geo_copy,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['adm_nm'],
            aliases=['행정동:']
        ),
        popup=folium.GeoJsonPopup(
            fields=['adm_nm', 'rank', 'sales', 'stores'],
            aliases=['행정동:', '순위:', '예상매출:', '점포수:'],
            localize=True
        )
    ).add_to(m)

    st_folium(m, width=900, height=650)

# ----------------------------
# 오른쪽 리포트 영역
# ----------------------------
with col2:
    st.subheader("업종 분석 리포트")

    st.markdown(f"### 📌 선택 업종: {industry}")

    st.markdown("#### 추천 행정동")
    
    # 순위별 색상 표시
    rank_colors_display = {
        1: "#d73027",
        2: "#fc8d59",
        3: "#fee090",
        4: "#91bfdb",
        5: "#4575b4"
    }

    for i, row in top5.iterrows():
        color = rank_colors_display[row['순위']]
        st.markdown(f"""
        <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 2px solid black;">
        <strong style="font-size: 16px; color: {'white' if row['순위'] in [1,5] else 'black'};">{row['순위']}위 | {row['행정동']}</strong><br>
        <span style="color: {'white' if row['순위'] in [1,5] else 'black'};">
        • 예상 매출: {row['예상매출(점포당)']:,.0f}원<br>
        • 서울 대비 매출: {row['서울 평균 대비 매출지수']:.2f}배<br>
        • 점포 수: {row['점포_수']:,}개<br>
        • 총 직장인구: {row['총_직장_인구_수']:,}명<br>
        • 총 유동인구: {row['총_유동인구_수']:,}명
        </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 창업 인사이트")

    # 업종별 특화 인사이트
    if industry == "한식음식점":
        st.markdown("#### 🥇 삼성1동을 추천하는 이유")
        st.markdown("""
        - **압도적인 매출 규모:** 삼성1동의 점포당 실제 매출은 약 1억 7,567만 원으로, 서울시 평균(약 7,651만 원)의 **2.25배**에 달하는 압도적인 1위 상권입니다.
        - **추천 포인트:** 코엑스와 테헤란로를 중심으로 한 거대 오피스 상권으로, 직장인들의 평일 점심 수요와 저녁 회식 수요가 끊이지 않는 탄탄한 배후 수요를 자랑합니다. 271개라는 많은 점포가 있음에도 불구하고 점포당 매출이 1위라는 것은, 그만큼 상권 전체에서 소비되는 '한식 파이' 자체가 거대하다는 것을 의미합니다.
        """)
        
        st.markdown("#### 💡 TOP 5 입지 데이터 인사이트")
        st.markdown("""
        - **강남권 오피스/학원가의 강세:** 삼성1동, 대치4동, 수서동 등 강남권 상권이 TOP 3를 휩쓸었습니다. 창업 시 초기 임대료 등 고정비 부담이 클 수 있으나, **서울 평균 대비 2배에 가까운 높은 매출 잠재력을 보유하고 있어 장기적인 ROI(투자 대비 수익률) 측면에서 매우 유리**한 입지입니다.
        - **수서동의 숨은 잠재력:** 수서동의 경우 점포 수가 67개로 비교적 적음에도 불구하고 점포당 매출이 1억 5천만 원을 훌쩍 넘습니다. 경쟁 점포 수가 적어 신규 진입 시 안정적인 시장 점유율을 확보할 수 있는 '알짜 상권'으로 분석됩니다.
        """)
    
    elif industry == "커피-음료":
        st.markdown("#### 🥇 소공동을 추천하는 이유")
        st.markdown("""
        - **초격차의 매출 퍼포먼스:** 소공동의 점포당 실제 매출은 약 1억 6,056만 원으로, 서울시 카페 평균(약 3,796만 원)의 무려 **4.13배**를 기록하고 있습니다.
        - **추천 포인트:** 서울의 핵심 중심업무지구(CBD)로, 대기업 본사와 관공서가 밀집해 있어 아침 출근 시간과 점심시간의 테이크아웃 커피 회전율이 극도로 높습니다. 테이크아웃 위주의 소형 평수 매장으로 창업할 경우, 평당 매출 효율을 극대화할 수 있는 최적의 입지입니다.
        """)
        
        st.markdown("#### 💡 TOP 5 입지 데이터 인사이트")
        st.markdown("""
        - **'점포 수'와 '매출'의 반비례가 만드는 기회:** 2위 잠실2동(28개), 3위 수서동(19개)은 점포 수가 매우 적은 데 반해 서울시 평균의 3.4~4배에 달하는 경이로운 매출을 보입니다. 이는 해당 지역에 대형 복합시설(역사, 쇼핑몰 등) 내부 입점 매장이 많거나, 진입 장벽이 높아 소수 매장이 수요를 독식하고 있음을 시사합니다. 상가 매물이 나온다면 권리금을 감수하더라도 최우선으로 선점해야 할 '하이리턴' 상권입니다.
        - **수서동의 크로스오버:** 수서동은 한식음식점에 이어 커피-음료 업종에서도 TOP 3에 올랐습니다. SRT 역사 및 주변 오피스 개발로 인한 유동 인구 증가가 F&B 전반의 매출을 강하게 견인하고 있으므로, 식음료 창업을 고려하는 분들이라면 가장 눈여겨봐야 할 행정동입니다.
        """)
    
    elif industry == "제과점":
        st.markdown("#### 🥇 구로5동을 추천하는 이유")
        st.markdown("""
        - **안정적인 고수익 창출:** 구로5동의 예상 점포당 매출은 약 1억 7,518만 원으로, 서울시 제과점 평균(약 4,804만 원)을 훌쩍 뛰어넘는 **3.64배**의 압도적인 성과를 보여줍니다.
        - **추천 포인트:** 구로5동은 직장인 유동 인구가 많은 상업/업무지구와 대규모 주거단지가 혼합된 복합 상권입니다. 출퇴근길 식사 대용 빵 소비와 주말 가족 단위의 디저트 수요를 동시에 흡수할 수 있어, 주중과 주말의 매출 편차가 적고 안정적인 고수익을 기대할 수 있는 최적의 입지입니다.
        """)
        
        st.markdown("#### 💡 TOP 5 입지 데이터 인사이트")
        st.markdown("""
        - **소수 정예가 이끄는 '과점형' 하이리턴 상권:** 제과점 TOP 5 지역의 가장 큰 특징은 **점포 수가 7~16개로 매우 적다는 점**입니다. 반면 매출은 서울 평균의 3.4배 이상을 기록하고 있습니다. 이는 제과점 업종 특성상 초기 설비(오븐, 제빵 공간 등) 투자비용이 커 진입 장벽이 높지만, 일단 상권 내에 자리 잡으면 경쟁 심화 없이 해당 지역의 수요를 독식할 수 있다는 것을 의미합니다.
        - **확실한 배후 수요를 낀 상권의 강세:** 건대입구역이라는 거대 대학/유흥 상권을 낀 2위 화양동, 탄탄한 학원가와 구매력 높은 주거지를 갖춘 3위 대치1동, 전형적인 대단지 아파트 밀집 지역인 4위 창4동 등 타겟 고객층이 명확한 곳이 상위권을 차지했습니다. 제과점 창업 시에는 유동 인구의 단순 수치보다는 '빵을 소비할 확실한 목적을 가진 배후 세대(학생, 가족, 1인 가구 등)'가 얼마나 탄탄한지 파악하는 것이 핵심입니다.
        """)
    
    else:
        st.markdown("""
        - 상위 5개 행정동은 모두 유동인구와 소비지수가 높은 지역으로 나타났습니다.
        - 특히 1위 지역은 서울 평균 대비 매출이 높게 분석되었습니다.
        - 이는 상권 집중도와 접근성이 영향을 준 것으로 판단됩니다.
        - 창업 시 초기 고정비를 고려하되, 매출 잠재력이 높아 ROI 측면에서 유리합니다.
        """)

st.markdown("---")
st.markdown("모델 기반: XGBoost + Lag Feature 활용 매출 예측")
