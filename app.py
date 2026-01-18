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
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False)
    return fig

def create_job_match_chart(job_matches):
    # match_jobsが返す「job辞書」を含んだリストをグラフ用データフレームに変換
    chart_data = []
    for m in job_matches:
        chart_data.append({
            'job_name': m['job']['name'],  # ネストされた名前を抽出
            'match_rate': m['match_rate']
        })
    
    df = pd.DataFrame(chart_data)
    fig = px.bar(df, x='match_rate', y='job_name', orientation='h', title="職種マッチング率")
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

# ==========================================
# 2. 初期設定・辞書の準備
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム（24職種対応）")

text_responses = {}

# ==========================================
# 3. サイドバー（基本情報入力）
# ==========================================
with st.sidebar:
    st.header("📝 基本情報")
    name = st.text_input("氏名", value="")
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability_type = st.text_input("障害種別", value="", placeholder="例：精神障害、知的障害など")
    
    st.divider()
    
    st.header("🏃 身体的・環境条件")
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

    env_options = ["騒音", "人混み", "高所", "屋外（暑さ・寒さ）", "強い光", "刃物・危険物", "その他"]
    env_preference = st.multiselect("避けるべき環境（配慮事項）", options=env_options, key="env_pref")

    other_env_text = ""
    if "その他" in env_preference:
        other_env_text = st.text_input("具体的な配慮事項を入力してください")

env_list = [item for item in env_preference if item != "その他"]
if other_env_text:
    env_list.append(other_env_text)

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

# ==========================================
# 5. 評価ボタンと実行
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始", type="primary"):
    if not name:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AI分析中..."):
            # 1. AI分析の実行
            analyzer = TextAnalyzer()
            text_scores = analyzer.analyze(text_responses)
            
            # 2. スコア計算
            final_scores = SamhallScorer.calculate_final_scores(text_scores)
            
            # 3. ジョブデータベースの読み込み（ここを修正）
            with open('data/job_database.json', 'r', encoding='utf-8') as f:
                job_db = json.load(f)  # ← ここが一段右に下がっている必要があります
            
            # 4. マッチング実行
            job_matches = SamhallScorer.match_jobs(final_scores, job_db)
            
            # セッション状態に保存
            st.session_state['scores'] = final_scores
            st.session_state['job_matches'] = job_matches
            st.session_state['evaluated'] = True
