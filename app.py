import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# --- 1. セッション状態の初期化（これを冒頭に置くのが重要） ---
if 'evaluated' not in st.session_state:
    st.session_state['evaluated'] = False
if 'scores' not in st.session_state:
    st.session_state['scores'] = {}
if 'job_matches' not in st.session_state:
    st.session_state['job_matches'] = []

# --- 2. 分析・グラフ作成用関数 ---
def create_radar_chart(scores):
    categories = ["読み取る力", "人との関わり", "計算する力", "相談する力"]
    # スコアが空の場合のデフォルト値
    keys = ["reading", "writing", "calculation", "communication"]
    values = [max(0.1, scores.get(k, 0.1)) for k in keys]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=400)
    return fig

def get_feedback_content(scores):
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算する力", "communication": "相談する力"}
    if not scores: return "期待のプロフェッショナル", ["分析中", "分析中", "分析中"]
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return f"{top_3[0]}に優れた実務の星", top_3

# --- 3. メイン画面レイアウト ---
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

# 個人情報の取り扱い（サイドバーに配置してメインをスッキリさせる）
with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state.get('name', ""))
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", value=st.session_state.get('disability', ""))
    st.divider()
    st.info("💡 入力データは保存されません。")

# ワーク入力エリア
st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算する力", "💬 相談する力"])
with tab1: r_val = st.text_area("Q. 働くことの「お金」以外の意味は？", key="r_t")
with tab2: w_val = st.text_area("Q. 誰かと関わって「良かった」エピソードは？", key="w_t")
with tab3: c_val = st.text_area("Q. 計算式と答えを書いてください。", key="c_t")
with tab4: m_val = st.text_area("Q. 上司への最初のセリフは？", key="m_t")

# --- 4. 実行ボタン ---
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("24職種のデータと照合中..."):
            try:
                # 分析ロジックの呼び出し（ダミーまたは実機）
                from evaluator.text_analyzer import TextAnalyzer
                from evaluator.scorer import SamhallScorer
                
                inputs = {"reading": r_val, "writing": w_val, "calculation": c_val, "communication": m_val}
                raw = TextAnalyzer().analyze(inputs)
                
                # スコアとマッチングをセッションに保存
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw)
                
                db_path = 'data/job_database.json'
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        db = json.load(f)
                    st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], db)
                    st.session_state['evaluated'] = True # ここでフラグを立てる
                else:
                    st.error("職種データ(job_database.json)が見つかりません。")
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

# --- 5. 結果表示エリア（ evaluated が True のときだけ表示） ---
if st.session_state['evaluated']:
    st.divider()
    st.balloons()
    
    scores = st.session_state['scores']
    job_matches = st.session_state['job_matches']
    title, top_3 = get_feedback_content(scores)

    st.markdown(f"### 🎊 {st.session_state['name']} さんの分析結果: **{title}**")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("#### 📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(scores), use_container_width=True)

    with col2:
        st.write("#### 🎯 適性の高いお仕事")
        if job_matches:
            match_df = pd.DataFrame([{'職種': m['job']['name'], 'マッチ率': m['match_rate']} for m in job_matches[:10]])
            fig_match = px.bar(match_df, x='マッチ率', y='職種', orientation='h', color='マッチ率', color_continuous_scale='Blues')
            fig_match.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig_match, use_container_width=True)
        else:
            st.warning("職種データとの照合に失敗しました。")

    st.divider()
    st.subheader("🤖 AIキャリア・アドバイス")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**強み①: {top_3[0]}**")
    c2.info(f"**強み②: {top_3[1]}**")
    c3.info(f"**強み③: {top_3[2]}**")
    
    st.write(f"あなたの「{top_3[0]}」は、現場で非常に重宝される力です。自信を持って取り組んでください。")
