import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. グラフ作成・保存機能
# ==========================================
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False
    )
    return fig

def create_job_match_chart(job_matches):
    df = pd.DataFrame(job_matches)
    fig = px.bar(df, x='match_rate', y='job_name', orientation='h',
                 title="職種マッチング率",
                 labels={'match_rate': 'マッチング率 (%)', 'job_name': '職種'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

# ==========================================
# 2. 初期設定・説明文
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム（24職種対応）")

st.markdown("""
### 📌 本システムについて
本アプリは、労働能力評価メソッド**「O-lys（オーリス）」**の指標に基づき、個人の「できること」を可視化するシミュレーターです。
""")

# ==========================================
# 3. サイドバー（基本情報入力）
# ==========================================
with st.sidebar:
    st.header("📝 基本情報")
    name = st.text_input("氏名", value="")
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    
    st.divider()
    
    st.header("🏃 身体的・環境条件")
    st.caption("マッチングの精度を高めるために使用します")
    
    physical_mobility = st.selectbox(
        "移動・歩行の状況", 
        ["制限なし（階段・長距離OK）", "長距離は困難", "車椅子利用", "歩行補助が必要"],
        key="phys_mob"
    )
    
    physical_lifting = st.selectbox(
        "持ち上げられる重さ", 
        ["10kg以上（重労働OK）", "5kg程度（軽作業）", "重いものは不可"],
        key="phys_lift"
    )

# ==========================================
# 4. ワーク回答セクション
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

# ここで辞書を初期化
text_responses = {}

with tab1:
    st.subheader("読解・理解力")
    st.write("**【文章】**\n「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」")
    r_sel = st.selectbox("理解度は？", ["-- 選択 --", "完璧", "だいたい", "難しい", "不明"], key="r_s")
    r_txt = st.text_area("働くことの「お金」以外の意味は？", key="r_t")
    text_responses['reading'] = f"自己評価:{r_sel} / 回答:{r_txt}"

with tab2:
    st.subheader("文章作成力")
    w_sel = st.selectbox("文章は得意？", ["得意", "普通", "苦手"], key="w_s")
    w_txt = st.text_area("最近の「良いこと」を教えてください。", key="w_t")
    text_responses["writing"] = f"自己評価:{w_sel} / 回答:{w_txt}"

with tab3:
    st.subheader("🔢 計算・論理力")
    st.write("**課題：** 時給1,200円、1日6時間、週5日（計20日）の給与は？")
    c_sel = st.radio("自信は？", ["迷わず", "少し時間", "計算機希望", "困難"], key="c_s_new")
    c_txt = st.text_area("答えと計算式を書いてください。", key="c_t_new")
    text_responses["calculation"] = f"自己評価:{c_sel} / 回答:{c_txt}"

with tab4:
    st.subheader("💬 報告・相談")
    st.write("**場面：** 作業中に道具を壊したが、上司が不在。")
    m_sel = st.selectbox("どう動く？", ["待つ", "同僚に相談", "自分で直す", "放置"], key="m_s")
    m_txt = st.text_area("戻った上司へ何と言いますか？", key="m_t")
    text_responses["communication"] = f"判断:{m_sel} / 発言:{m_txt}"

# 全ての入力が終わった後で身体情報を追加する（重要！）
text_responses["physical_info"] = f"【身体条件】移動:{physical_mobility} / 重量物:{physical_lifting}"

# ==========================================
# 5. 評価ボタンと実行
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始", type="primary"):
    if not name:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AI分析中..."):
            analyzer = TextAnalyzer()
            scores = analyzer.analyze(text_responses)
            
            scorer = SamhallScorer()
            job_matches = scorer.calculate_matches(scores)
            
            st.session_state['scores'] = scores
            st.session_state['job_matches'] = job_matches
            st.session_state['evaluated'] = True

if st.session_state.get('evaluated'):
    st.success("分析完了！")
    st.plotly_chart(create_radar_chart(st.session_state['scores']))
    st.plotly_chart(create_job_match_chart(st.session_state['job_matches'][:10]))
