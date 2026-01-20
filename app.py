import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. 称号・フィードバック生成
# ==========================================
def get_feedback_content(scores):
    if not scores: return "期待の新星", ["分析中", "分析中", "分析中"]
    labels = {"reading": "理解する力", "writing": "伝える力", "calculation": "たしかめる力", "communication": "つながる力"}
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    
    titles = {
        "calculation": "確かな正確さを持つ実務の星",
        "communication": "周囲を安心させる報告の達人",
        "writing": "想いを形にする表現クリエイター",
        "reading": "本質を深く捉える理解のリーダー"
    }
    title = titles.get(top_key, "期待のプロフェッショナル")
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

# ==========================================
# 2. グラフ作成
# ==========================================
def create_radar_chart(scores):
    categories = ["理解力", "表現力", "正確性", "報告・相談"]
    values = [
        max(0.1, scores.get("reading", 0)), 
        max(0.1, scores.get("writing", 0)), 
        max(0.1, scores.get("calculation", 0)), 
        max(0.1, scores.get("communication", 0))
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

def create_job_match_chart(job_matches):
    if not job_matches: return go.Figure()
    df = pd.DataFrame([
        {'職種': m['job'].get('name', '不明'), 'マッチ率': m.get('match_rate', 0)}
        for m in job_matches[:10]
    ]).sort_values('マッチ率', ascending=True)

    fig = px.bar(
        df, x='マッチ率', y='職種', orientation='h',
        title="🎯 あなたの強みが活きるお仕事",
        color='マッチ率', color_continuous_scale='Blues', text='マッチ率'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_range=[0, 115], coloraxis_showscale=False, height=450)
    return fig

# ==========================================
# 3. 初期設定
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

# セッション状態の維持
for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'age', 'disability']:
    if key not in st.session_state: st.session_state[key] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

st.title("🎯 O-lys AI評価システム")

# 強み発見のコンセプト説明
with st.expander("🛡️ はじめる前に（あなたの強みを見つけるために）", expanded=True):
    st.markdown("""
    ### このシステムは、あなたの「強み」を見つけるためのものです。
    正解・不正解を判定する「テスト」ではありません。AIがあなたの言葉から、**隠れた才能や、お仕事で活かせるポイント**を掘り起こします。
    - **安心してください**: 入力内容はAIの学習に使われることはありません。
    - **リラックスして**: 短い一言でも大丈夫です。今のあなたの考えをそのまま教えてください。
    """)

# ==========================================
# 4. サイドバー（プロフィール・身体条件 復活版）
# ==========================================
with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['age'] = st.number_input("年齢", min_value=0, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "回答しない"])
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", placeholder="例：精神障害、聴覚過敏など")
    
    st.divider()
    st.header("🏃 身体・環境条件")
    phys_mob = st.selectbox("移動状況", ["制限なし", "長距離は困難", "車椅子利用", "歩行補助が必要"])
    phys_lift = st.selectbox("重量物", ["10kg以上OK", "5kg程度", "不可"])
    env_pref = st.multiselect("避けるべき環境", ["騒音", "人混み", "高所", "屋外", "強い光", "危険物"])

# ==========================================
# 5. ワーク・セクション（シンプル問題）
# ==========================================
st.header("✍️ ワーク・シミュレーション")
st.info("💡 あなたの良さをAIが見つけます。気負わずに記入してください。")
tab1, tab2, tab3, tab4 = st.tabs(["📖 指示の理解", "✏️ 自分の言葉で書く", "🔢 数字をたしかめる", "💬 困った時の相談"])

with tab1:
    st.write("**【文章】**\n「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」")
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は何だと思いますか？", value=st.session_state['r_t_val'], key="r_t", placeholder="（例）社会とつながること。")

with tab2:
    st.session_state['w_t_val'] = st.text_area("あなたが最近経験した「ちょっと嬉しかったこと」を教えてください。", value=st.session_state['w_t_val'], key="w_t", placeholder="（例）散歩をしたら綺麗な花を見つけた。")

with tab3:
    st.write("**【課題】**\n時給1,200円で、1日6時間、月に20日間働きました。合計の給与はいくらになりますか？")
    st.session_state['c_t_val'] = st.text_area("答えと計算式を書いてください。", value=st.session_state['c_t_val'], key="c_t_new", placeholder="（例）1200 × 6 × 20 ＝ ◯◯円")

with tab4:
    st.write("**【場面】**\n作業中に道具を壊してしまいました。近くに上司がいません。")
    st.session_state['m_t_val'] = st.text_area("戻ってきた上司へ、最初に何と言いますか？", value=st.session_state['m_t_val'], key="m_t", placeholder="（例）すみません、道具を壊しました。どうすればいいですか？")

# ==========================================
# 6. 実行処理
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発掘する）", type="primary"):
    if not st.session_state['name']:
        st.error("「氏名」を入力してください")
    else:
        with st.spinner("AIがあなたの「強み」を分析中..."):
            try:
                inputs = {
                    "reading": st.session_state['r_t_val'], 
                    "writing": st.session_state['w_t_val'],
                    "calculation": st.session_state['c_t_val'], 
                    "communication": st.session_state['m_t_val'],
                    "age": st.session_state['age'],
                    "disability": st.session_state['disability'],
                    "physical_info": f"{phys_mob}/{phys_lift}",
                    "environment_info": ",".join(env_pref)
                }
                analyzer = TextAnalyzer()
                raw_scores = analyzer.analyze(inputs)
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw_scores)
                
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], job_db)
                st.session_state['evaluated'] = True
                st.query_params.update({"name": st.session_state['name']})
            except Exception as e:
                st.error(f"分析エラー: {e}")

# ==========================================
# 7. 結果表示
# ==========================================
if st.session_state.get('evaluated'):
    title, top_3 = get_feedback_content(st.session_state['scores'])
    job_matches = st.session_state.get('job_matches', [])
    
    st.balloons()
    st.markdown(f"""
    <div style="background-color:#fff5f5; padding:20px; border-radius:15px; border:3px solid #ff4b4b; text-align:center; margin-bottom:20px;">
        <h2 style="color:#ff4b4b; margin:0;">🎊 {st.session_state['name']} さんの強み 🎊</h2>
        <h1 style="font-size:2.8em; margin:10px 0;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with col2:
        st.plotly_chart(create_job_match_chart(job_matches), use_container_width=True)

    st.divider()
    st.subheader("🤖 AIキャリア・フィードバック")
    cols = st.columns(3)
    for i, s in enumerate(top_3):
        cols[i].info(f"**強み: {s}**")
        
    if job_matches:
        best_job = job_matches[0]
        st.markdown(f"""
        **【AI分析コメント】**
        {st.session_state['name']}さんの回答から、素晴らしい「{top_3[0]}」を見つけました。
        特におすすめしたいお仕事は**「{best_job['job']['name']}」**（マッチ率 {best_job['match_rate']}%）です。
        
        {st.session_state['disability']}などの特性も考慮しつつ、
        あなたの丁寧な姿勢を活かせる環境がきっと見つかります。
        """)

    st.button("📄 あなたの「強み」診断シートを保存する（準備中）")
