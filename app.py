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
        xaxis_range=[0, 115],
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

# 入力内容を保持するためのセッション管理
if 'name' not in st.session_state: st.session_state['name'] = ""
if 'r_t_val' not in st.session_state: st.session_state['r_t_val'] = ""
if 'w_t_val' not in st.session_state: st.session_state['w_t_val'] = ""
if 'c_t_val' not in st.session_state: st.session_state['c_t_val'] = ""
if 'm_t_val' not in st.session_state: st.session_state['m_t_val'] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

text_responses = {}

# ==========================================
# 3. サイドバー（基本情報・身体条件）
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

# プロフィール情報の集約
text_responses["user_profile"] = f"【基本】{age}歳/{gender} 【障害】:{disability_type}"
text_responses["environment_info"] = f"【避けるべき環境】:{', '.join(env_list) if env_list else '特になし'}"
text_responses["physical_info"] = f"【身体】移動:{physical_mobility} / 重量物:{physical_lifting}"

# ==========================================
# 4. ワーク回答セクション
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

with tab1:
    st.subheader("読解・理解力")
    st.write("「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」")
    r_sel = st.selectbox("理解度は？", ["-- 選択 --", "完璧", "だいたい", "難しい", "不明"], key="r_s")
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は？", value=st.session_state['r_t_val'], key="r_t")
    text_responses['reading'] = f"自己評価:{r_sel} / 回答:{st.session_state['r_t_val']}"

with tab2:
    st.subheader("文章作成力")
    w_sel = st.selectbox("文章は得意？", ["得意", "普通", "苦手"], key="w_s")
    st.session_state['w_t_val'] = st.text_area("あなたが最近経験した「良いこと」について教えてください。", value=st.session_state['w_t_val'], key="w_t")
    text_responses["writing"] = f"自己評価:{w_sel} / 回答:{st.session_state['w_t_val']}"

with tab3:
    st.subheader("🔢 計算・論理力")
    st.write("時給1,200円、1日6時間、週5日（計20日）の給与は？")
    c_sel = st.radio("自信は？", ["迷わず", "少し時間", "計算機希望", "困難"], key="c_s_new")
    st.session_state['c_t_val'] = st.text_area("答えと計算式を書いてください。", value=st.session_state['c_t_val'], key="c_t_new")
    text_responses["calculation"] = f"自己評価:{c_sel} / 回答:{st.session_state['c_t_val']}"

with tab4:
    st.subheader("💬 報告・相談")
    st.write("""
    **場面：**
    作業中に道具を壊してしまいましたが、周りに上司がいません。
    """)
    m_sel = st.selectbox("どう動く？", ["待つ", "同僚に相談", "自分で直す", "放置"], key="m_s")
    # ここが修正箇所です：最後に ')' が必要です
    st.session_state['m_t_val'] = st.text_area("戻った上司へ何と言いますか？", value=st.session_state['m_t_val'], key="m_t")
    text_responses["communication"] = f"判断:{m_sel} / 発言:{st.session_state['m_t_val']}"
