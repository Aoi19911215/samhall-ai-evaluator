import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. ロジック・グラフ関数（省略なし）
# ==========================================
def get_feedback_content(scores):
    if not scores: return "期待の新星", ["分析中", "分析中", "分析中"]
    labels = {"reading": "読解力", "writing": "文章力", "calculation": "計算力", "communication": "報告・相談"}
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    titles = {
        "calculation": "正確無比なロジカル・スター", "communication": "安心を届ける報告の達人",
        "writing": "想いを伝える文章クリエイター", "reading": "本質を見抜くインテリジェンス・リーダー"
    }
    title = titles.get(top_key, "期待の星")
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

def create_radar_chart(scores):
    categories = ["読解", "文章", "計算", "報告"]
    values = [max(0.1, scores.get(k, 0)) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False)
    return fig

def create_job_match_chart(job_matches):
    if not job_matches: return go.Figure()
    df = pd.DataFrame([{'職種': m['job']['name'], 'マッチ率': m['match_rate']} for m in job_matches[:10]]).sort_values('マッチ率', ascending=True)
    fig = px.bar(df, x='マッチ率', y='職種', orientation='h', title="🎯 マッチするお仕事 Top 10", color='マッチ率', color_continuous_scale='Blues', text='マッチ率')
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_range=[0, 115], coloraxis_showscale=False)
    return fig

# ==========================================
# 2. 初期設定・セッション
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

# --- 【重要】プライバシーと利用規約の説明セクション ---
with st.expander("🛡️ はじめる前に（プライバシーとデータの取り扱いについて）", expanded=True):
    st.write("""
    本システムは、AI（LLM）を活用してあなたの強みを発見するための支援ツールです。
    - **データの保護**: 入力された内容は評価の生成にのみ使用され、AIの学習に利用されることはありません。
    - **個人情報の扱い**: 氏名はレポート表示のみに使用し、サーバー側には保存されません。
    - **結果の解釈**: AIによる推定評価です。就労の採否を決定するものではなく、自分を知るヒントとしてご活用ください。
    """)
    st.info("※ ページを更新（リロード）すると入力内容は消去されますのでご注意ください。")

for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val']:
    if key not in st.session_state: st.session_state[key] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False
# ==========================================
# URLパラメータから値を復元 / 保存する関数
# ==========================================
def sync_url_params():
    # URLから既存の値を取得
    params = st.query_params
    
    # セッション状態にURLの値を反映（初回アクセス時など）
    for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val']:
        if key in params and not st.session_state.get(key):
            st.session_state[key] = params[key]

    # 入力があるたびにURLパラメータを更新
    st.query_params.update({
        "name": st.session_state.get('name', ""),
        "r_t_val": st.session_state.get('r_t_val', ""),
        "w_t_val": st.session_state.get('w_t_val', ""),
        "c_t_val": st.session_state.get('c_t_val', ""),
        "m_t_val": st.session_state.get('m_t_val', "")
    })

# app.py の冒頭（st.set_page_configの直後）で呼び出す
sync_url_params()
# ==========================================
# 3. 入力セクション（サイドバー・課題）
# ==========================================
with st.sidebar:
    st.header("📝 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    st.divider()
    st.header("🏃 身体・環境条件")
    phys_mob = st.selectbox("移動状況", ["制限なし", "長距離は困難", "車椅子利用", "歩行補助が必要"])
    phys_lift = st.selectbox("重量物", ["10kg以上OK", "5kg程度", "不可"])
    env_pref = st.multiselect("避けるべき環境", ["騒音", "人混み", "高所", "屋外", "強い光", "危険物"])

st.header("✍️ テキスト課題")
tabs = st.tabs(["📖 読解", "✏️ 文章", "🔢 計算", "💬 相談"])
with tabs[0]:
    st.write("課題：働くことのお金以外の意味は？")
    st.session_state['r_t_val'] = st.text_area("回答", value=st.session_state['r_t_val'], key="r_t", placeholder="例：社会とつながること。")
with tabs[1]:
    st.write("課題：最近あった「良いこと」は？")
    st.session_state['w_t_val'] = st.text_area("回答", value=st.session_state['w_t_val'], key="w_t", placeholder="例：天気が良くて気持ちよかったです。")
with tabs[2]:
    st.write("課題：時給1200円×6時間×20日の給与は？")
    st.session_state['c_t_val'] = st.text_area("回答", value=st.session_state['c_t_val'], key="c_t_new", placeholder="例：1200×6×20=144000")
with tabs[3]:
    st.write("課題：道具を壊した際、上司に何と言いますか？")
    st.session_state['m_t_val'] = st.text_area("回答", value=st.session_state['m_t_val'], key="m_t", placeholder="例：すみません、道具を壊しました。")

# ==========================================
# 4. 実行・結果表示
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始（お守りシート作成）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AIが分析中..."):
            try:
                inputs = {"reading": st.session_state['r_t_val'], "writing": st.session_state['w_t_val'],
                          "calculation": st.session_state['c_t_val'], "communication": st.session_state['m_t_val'],
                          "physical_info": f"{phys_mob}/{phys_lift}", "environment_info": ",".join(env_pref)}
                analyzer = TextAnalyzer()
                raw_scores = analyzer.analyze(inputs)
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw_scores)
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], job_db)
                st.session_state['evaluated'] = True
            except Exception as e:
                st.error(f"分析エラー: {e}")

if st.session_state.get('evaluated'):
    title, top_3 = get_feedback_content(st.session_state['scores'])
    job_matches = st.session_state.get('job_matches', [])
    st.balloons()
    st.markdown(f"""<div style="background-color:#fff5f5; padding:20px; border-radius:15px; border:2px solid #ff4b4b; text-align:center;">
        <h2 style="color:#ff4b4b;">🎊 {st.session_state['name']} さんの分析結果 🎊</h2>
        <h1 style="font-size:2.8em;">{title}</h1></div>""", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with col2: st.plotly_chart(create_job_match_chart(job_matches), use_container_width=True)
    st.divider()
    st.subheader("🤖 AIキャリア・アドバイス")
    cols = st.columns(3)
    for i, s in enumerate(top_3): cols[i].info(f"**強み: {s}**")
    if job_matches:
        best = job_matches[0]
        st.markdown(f"**【AI分析コメント】**\n{st.session_state['name']}さんの誠実さが伝わりました。**「{best['job']['name']}」**（マッチ率 {best['match_rate']}%）は特におすすめです。")
    st.button("📄 診断結果をお守りシートとして保存する（準備中）")
