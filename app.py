import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. 称号と強みを抽出する関数（一言でも必ず出す）
# ==========================================
def get_feedback_content(scores):
    # 日本語変換用
    labels = {"reading": "読解力", "writing": "文章力", "calculation": "計算力", "communication": "報告・相談"}
    # スコア順にソート（一言でも必ず順位が出る）
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # 称号の決定
    top_key = sorted_s[0][0]
    titles = {
        "calculation": "正確無比なロジカル・スター",
        "communication": "安心を届ける報告の達人",
        "writing": "想いを伝える文章クリエイター",
        "reading": "本質を見抜くインテリジェンス・リーダー"
    }
    title = titles.get(top_key, "期待の新星")
    
    # 強み（上位3つを強制抽出）
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

# ==========================================
# 2. グラフ作成
# ==========================================
def create_radar_chart(scores):
    categories = ["読解", "文章", "計算", "報告"]
    # 確実にデータをリスト化
    values = [scores.get("reading", 0.1), scores.get("writing", 0.1), 
              scores.get("calculation", 0.1), scores.get("communication", 0.1)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False)
    return fig

# ==========================================
# 3. 初期設定
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

# セッション状態の管理
for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val']:
    if key not in st.session_state: st.session_state[key] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

# ==========================================
# 4. メイン入力エリア（サイドバー省略）
# ==========================================
with st.sidebar:
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.info("💡 短い回答でもAIがあなたの強みを分析します！")

st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解", "✏️ 文章", "🔢 計算", "💬 相談"])

with tab1:
    st.session_state['r_t_val'] = st.text_area("働くことの意味は？", value=st.session_state['r_t_val'], key="r_t")
with tab2:
    st.session_state['w_t_val'] = st.text_area("最近の「良いこと」は？", value=st.session_state['w_t_val'], key="w_t")
with tab3:
    st.session_state['c_t_val'] = st.text_area("給与計算の結果は？", value=st.session_state['c_t_val'], key="c_t_new")
with tab4:
    st.session_state['m_t_val'] = st.text_area("上司への報告は？", value=st.session_state['m_t_val'], key="m_t")

# ==========================================
# 5. 実行・結果表示
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("分析中..."):
            analyzer = TextAnalyzer()
            # 短い回答でもスコア化
            raw_scores = analyzer.analyze({
                "reading": st.session_state['r_t_val'], 
                "writing": st.session_state['w_t_val'],
                "calculation": st.session_state['c_t_val'], 
                "communication": st.session_state['m_t_val']
            })
            st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw_scores)
            
            with open('data/job_database.json', 'r', encoding='utf-8') as f:
                job_db = json.load(f)
            
            # Scorerのmatch_jobsを呼び出し
            st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], job_db)
            st.session_state['evaluated'] = True

if st.session_state.get('evaluated'):
    title, top_3 = get_feedback_content(st.session_state['scores'])
    job_matches = st.session_state['job_matches']
    
    # 称号の表示
    st.balloons()
    st.markdown(f"""
    <div style="background-color:#fff5f5; padding:20px; border-radius:15px; border:2px solid #ff4b4b; text-align:center;">
        <h2 style="color:#ff4b4b;">🎊 {st.session_state['name']} さんの分析結果 🎊</h2>
        <h1 style="font-size:2.5em;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1: st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with col2:
        if job_matches:
            # マッチング職種を表示（必ず表示）
            df = pd.DataFrame([{'職種': m['job']['name'], 'マッチ率': m['match_rate']} for m in job_matches[:5]])
            fig = px.bar(df, x='マッチ率', y='職種', orientation='h', title="🎯 マッチするお仕事")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🤖 AIアドバイス")
    
    # 強みバッジを必ず3つ出す
    cols = st.columns(3)
    for i, s in enumerate(top_3):
        cols[i].info(f"**{s}**")
        
    if job_matches:
        m = job_matches[0]
        st.markdown(f"""
        **【分析コメント】**
        短い回答の中にも、{st.session_state['name']}さんの誠実さが表れています。
        特に「{m['job']['name']}」との適合率は **{m['match_rate']}%** です。
        
        **【次のステップへのヒント】**
        さらに詳しく書く（理由や計算式を添える）と、この数値はもっと伸びる可能性があります。
        今のままでも、あなたの強みを活かせる職場はたくさんありますよ！
        """)
