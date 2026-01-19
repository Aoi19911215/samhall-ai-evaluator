import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. 称号・強み抽出ロジック（一言回答でも必ず表示）
# ==========================================
def get_feedback_content(scores):
    if not scores:
        return "期待の新星", ["分析中", "分析中", "分析中"]
    
    # 日本語変換マップ
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
    title = titles.get(top_key, "オールマイティな期待の星")
    
    # 強み（上位3つを強制抽出）
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

# ==========================================
# 2. グラフ作成機能
# ==========================================
def create_radar_chart(scores):
    categories = ["読解", "文章", "計算", "報告"]
    # 0だとグラフが消えるため最小値0.1を確保
    values = [
        max(0.1, scores.get("reading", 0)), 
        max(0.1, scores.get("writing", 0)), 
        max(0.1, scores.get("calculation", 0)), 
        max(0.1, scores.get("communication", 0))
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

def create_job_match_chart(job_matches):
    if not job_matches:
        return go.Figure().update_layout(title="職種データがありません")
    
    df = pd.DataFrame([
        {'職種': m['job'].get('name', '不明'), 'マッチ率': m.get('match_rate', 0)}
        for m in job_matches[:10]
    ]).sort_values('マッチ率', ascending=True)

    fig = px.bar(
        df, x='マッチ率', y='職種', orientation='h',
        title="🎯 あなたにマッチするお仕事 Top 10",
        color='マッチ率', color_continuous_scale='Blues', text='マッチ率'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_range=[0, 115], coloraxis_showscale=False, height=450)
    return fig

# ==========================================
# 3. 初期設定・セッション管理
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

# 各入力値を保持（リロード対策）
for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val']:
    if key not in st.session_state: st.session_state[key] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

# ==========================================
# 4. サイドバー（基本情報・配慮事項）
# ==========================================
with st.sidebar:
    st.header("📝 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability = st.text_input("障害種別", placeholder="例：精神障害など")
    
    st.divider()
    st.header("🏃 身体・環境条件")
    phys_mob = st.selectbox("移動状況", ["制限なし", "長距離は困難", "車椅子利用", "歩行補助が必要"])
    phys_lift = st.selectbox("重量物", ["10kg以上OK", "5kg程度", "不可"])
    env_pref = st.multiselect("避けるべき環境", ["騒音", "人混み", "高所", "屋外", "強い光", "危険物"])

# ==========================================
# 5. ワーク回答セクション（ガイド機能）
# ==========================================
st.header("✍️ テキスト課題")
st.info("💡 一言の回答でもAIがあなたの強みを分析します。詳しく書くと精度がさらに上がります！")

tabs = st.tabs(["📖 読解", "✏️ 文章", "🔢 計算", "💬 相談"])

with tabs[0]:
    st.write("**【課題】** 働くことは、お金以外に「社会とのつながり」や「能力の発揮」の意味があります。")
    with st.expander("🔍 ヒントを表示"):
        st.write("文章の中から「お金以外」のキーワードを抜き出して書いてみましょう。")
    st.session_state['r_t_val'] = st.text_area("お金以外の意味は？", placeholder="（例）社会とつながること。", value=st.session_state['r_t_val'], key="r_t")

with tabs[1]:
    with st.expander("🔍 ヒントを表示"):
        st.write("「散歩をした」「花を見た」など、日常の小さなことでOKです。")
    st.session_state['w_t_val'] = st.text_area("最近の「良いこと」は？", placeholder="（例）天気が良くて気持ちよかったです。", value=st.session_state['w_t_val'], key="w_t")

with tabs[2]:
    st.write("**【課題】** 時給1,200円×6時間×20日間の給与は？")
    with st.expander("🔍 ヒントを表示"):
        st.write("計算式（1200×6×...）も書くと「論理力」が高く評価されます。")
    st.session_state['c_t_val'] = st.text_area("答えと計算式", placeholder="（例）1200×6×20=144000", value=st.session_state['c_t_val'], key="c_t_new")

with tabs[3]:
    st.write("**【課題】** 道具を壊してしまった時、戻ってきた上司になんと伝えますか？")
    with st.expander("🔍 ヒントを表示"):
        st.write("「すみません」などの実際のセリフを書くのがポイントです。")
    st.session_state['m_t_val'] = st.text_area("具体的なセリフ", placeholder="（例）すみません、道具を壊しました。どうすればいいですか？", value=st.session_state['m_t_val'], key="m_t")

# ==========================================
# 6. 評価実行
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始（お守りシート作成）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AIが才能を掘り起こしています..."):
            try:
                # データの集約
                inputs = {
                    "reading": st.session_state['r_t_val'], 
                    "writing": st.session_state['w_t_val'],
                    "calculation": st.session_state['c_t_val'], 
                    "communication": st.session_state['m_t_val'],
                    "physical_info": f"{phys_mob}/{phys_lift}",
                    "environment_info": ",".join(env_pref)
                }
                
                analyzer = TextAnalyzer()
                raw_scores = analyzer.analyze(inputs)
                
                final_scores = SamhallScorer.calculate_final_scores(raw_scores)
                
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                
                st.session_state['scores'] = final_scores
                st.session_state['job_matches'] = SamhallScorer.match_jobs(final_scores, job_db)
                st.session_state['evaluated'] = True
            except Exception as e:
                st.error(f"分析エラー: {e}")

# ==========================================
# 7. 結果表示エリア
# ==========================================
if st.session_state.get('evaluated'):
    title, top_3 = get_feedback_content(st.session_state['scores'])
    job_matches = st.session_state['job_matches']
    
    st.balloons()
    st.markdown(f"""
    <div style="background-color:#fff5f5; padding:20px; border-radius:15px; border:3px solid #ff4b4b; text-align:center; margin-bottom:20px;">
        <h2 style="color:#ff4b4b; margin:0;">🎊 {st.session_state['name']} さんの分析結果 🎊</h2>
        <h1 style="font-size:2.8em; margin:10px 0;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_
