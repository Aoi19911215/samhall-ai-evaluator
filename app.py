import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. グラフ作成機能（ビジュアル改善版）
# ==========================================
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False,
        title="📊 スキルバランス"
    )
    return fig

def create_job_match_chart(job_matches):
    chart_data = []
    for m in job_matches:
        chart_data.append({
            'job_name': m['job']['name'],
            'match_rate': m['match_rate']
        })
    df = pd.DataFrame(chart_data)
    
    # マッチ率に応じたグラデーションと数値表示
    fig = px.bar(
        df, 
        x='match_rate', 
        y='job_name', 
        orientation='h', 
        title="🎯 あなたにマッチする職種 Top 10",
        color='match_rate',
        color_continuous_scale='Blues',
        text='match_rate',
    )
    
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_range=[0, 115], # 数値が見切れないよう調整
        showlegend=False,
        coloraxis_showscale=False,
        height=500
    )
    return fig

# ==========================================
# 2. 初期設定・セッション状態の初期化
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

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
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability_type = st.text_input("障害種別", value="", placeholder="例：精神障害など")
    
    st.divider()
    st.header("🏃 身体力・環境条件")
    physical_mobility = st.selectbox("移動・歩行の状況", ["制限なし（階段・長距離OK）", "長距離は困難", "車椅子利用", "歩行補助が必要"], key="phys_mob")
    physical_lifting = st.selectbox("持ち上げられる重さ", ["10kg以上（重労働OK）", "5kg程度（軽作業）", "重いものは不可"], key="phys_lift")
    env_options = ["騒音", "人混み", "高所", "屋外（暑さ・寒さ）", "強い光", "刃物・危険物", "その他"]
    env_preference = st.multiselect("避けるべき環境", options=env_options, key="env_pref")
    
    other_env_text = ""
    if "その他" in env_preference:
        other_env_text = st.text_input("具体的な配慮事項を入力してください")

env_list = [item for item in env_preference if item != "その他"]
if other_env_text: env_list.append(other_env_text)

text_responses["user_profile"] = f"【基本】{age}歳/{gender} 【障害】:{disability_type}"
text_responses["environment_info"] = f
