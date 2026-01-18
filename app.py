import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. グラフ作成機能
# ==========================================
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False)
    return fig

def create_job_match_chart(job_matches):
    chart_data = []
    for m in job_matches:
        chart_data.append({
            'job_name': m['job']['name'],
            'match_rate': m['match_rate']
        })
    df = pd.DataFrame(chart_data)
    fig = px.bar(df, x='match_rate', y='job_name', orientation='h', title="職種マッチング率")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

# ==========================================
# 2. 初期設定・セッション状態の初期化
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム（24職種対応）")

# 各入力値を保持するための初期化
if 'name' not in st.session_state: st.session_state['name'] = ""
if 'r_t_val' not in st.session_state: st.session_state['r_t_val'] = ""
if 'w_t_val' not in st.session_state: st.session_state['w_t_val'] = ""
if 'c_t_val' not in st.session_state: st.session_state['c_t_val'] = ""
if 'm_t_val' not in st.session_state: st.session_state['m_t_val'] = ""

text_responses = {}

# ==========================================
# 3. サイドバー
# ==========================================
with st.sidebar:
    st.header("📝 基本情報")
    # 氏名を保持
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability_type = st.text_input("障害種別", value="", placeholder="例：精神障害、知的障害など")
    
    st.divider()
    st.header("🏃 身体力・環境条件")
    physical_mobility = st.selectbox("移動・歩行の状況", ["制限なし（階段・長距離OK）", "長距離は困難", "車椅子利用", "歩行補助が必要"], key="phys_mob")
    physical_lifting = st.selectbox("持ち上げられる重さ", ["10kg以上（重労働OK）", "5kg程度（軽作業）", "重いものは不可"], key="phys_lift")
    env_options = ["騒音", "人混み", "高所", "屋外（暑さ・寒さ）", "強い光", "刃物・危険物", "その他"]
    env_preference = st.multiselect("避けるべき環境（配慮事項）", options=env_options, key="env_pref")
    
    other_env_text = ""
    if "その他" in env_preference:
        other_env_text = st.text_input("具体的な配慮事項を入力してください")

env_list = [item for item in env_preference if item != "その他"]
if other_env_text: env_list.append(other_env_text)

text_responses["user_profile"] = f"【基本】{age}歳/{gender} 【障害】:{disability_type}"
text_responses["environment_info"] = f"【避けるべき環境】:{', '.join(env_list) if env_list else '特になし'}"
text_responses["physical_info"] = f"【身体】移動:{physical_mobility} / 重量物:{physical_lifting}"

# ==========================================
# 4. ワーク回答セクション（入力を保持するように設定）
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

with tab1:
    st.subheader("読解・理解力")
    st.write("**【文章】**\n「働くことは、
