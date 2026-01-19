import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. 称号システム・ロジック
# ==========================================
def get_honorary_title(scores):
    if not scores: return "期待の新星"
    
    # スコアの高い順にソート
    s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_skill = s[0][0]
    
    titles = {
        "calculation": "正確無比なロジカル・スター",
        "communication": "安心を届ける報告の達人",
        "writing": "想いを伝える文章クリエイター",
        "reading": "本質を見抜くインテリジェンス・リーダー"
    }
    return titles.get(top_skill, "オールマイティな期待の星")

# ==========================================
# 2. グラフ作成機能
# ==========================================
def create_radar_chart(scores):
    if not scores: return go.Figure()
    categories = ["読解", "文章", "計算", "報告"] # 日本語ラベルに変換
    skill_map = {"reading": "読解", "writing": "文章", "calculation": "計算", "communication": "報告"}
    values = [scores.get(k, 0) for k in ["reading", "writing", "calculation", "communication"]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False, title="📊 スキルバランス"
    )
    return fig

def create_job_match_chart(job_matches):
    if not job_matches: return go.Figure()
    df = pd.DataFrame([
        {'job_name': m['job'].get('name', '不明'), 'match_rate': m.get('match_rate', 0)}
        for m in job_matches
    ]).sort_values('match_rate', ascending=True)

    fig = px.bar(
        df, x='match_rate', y='job_name', orientation='h', 
        title="🎯 マッチング職種 Top 10",
        color='match_rate', color_continuous_scale='Blues', text='match_rate'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_range=[0, 115], showlegend=False, coloraxis_showscale=False)
    return fig

# ==========================================
# 3. 初期設定
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val']:
    if key not in st.session_state: st.session_state[key] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

text_responses = {}

# ==========================================
# 4. サイドバー
# ==========================================
with st.sidebar:
    st.header("📝 基本情報")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    st.divider()
    st.header("🏃 身体・環境条件")
    physical_mobility = st.selectbox("移動の状況", ["制限なし", "長距離は困難", "車椅子利用", "歩行補助が必要"])
    physical_lifting = st.selectbox("持ち上げ", ["10kg以上", "5kg程度", "重いものは不可"])
    env_preference = st.multiselect("避けるべき環境", options=["騒音", "人混み", "高所", "屋外", "強い光", "危険物"])

text_responses["user_profile"] = f"{age}歳/{gender}"
text_responses["environment_info"] = f"避けるべき:{', '.join(env_preference)}"
text_responses["physical_info"] = f"移動:{physical_mobility}/重量:{physical_lifting}"

# ==========================================
# 5. ワーク回答（ガイド機能強化版）
# ==========================================
st.header("✍️ テキスト課題")
st.info("💡 具体的な言葉で書くほど、AIがあなたの隠れた才能を見つけ出します。")

tab1, tab2, tab3, tab4 = st.tabs(["📖 読解力", "✏️ 文章力", "🔢 計算力", "💬 相談力"])

with tab1:
    st.subheader("読解・理解力")
    st.write("「働くことは、収入を得るだけでなく、社会とつながり、能力を発揮する場です。」")
    with st.expander("🔍 ヒントを表示"):
        st.write("文章の中に答えが隠れています。そのまま書き写すのではなく、自分の言葉に直すと高評価です。")
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は？", placeholder="例：社会の中で自分の役割を見つけること...", value=st.session_state['r_t_val'], key="r_t")

with tab2:
    st.subheader("文章作成力")
    with st.expander("🔍 ヒントを表示"):
        st.write("「いつ・どこで・どう感じたか」をセットで書くと、丁寧な報告能力として評価されます。")
    st.session_state['w_t_val'] = st.text_area("最近の「良いこと」を教えてください。", placeholder="例：公園を散歩した時に、青空がとても綺麗で心が癒されました。", value=st.session_state['w_t_val'], key="w_t")

with tab3:
    st.subheader("計算・論理力")
    st.write("時給1,200円、1日6時間、週5日。4週間（20日）の給与は？")
    with st.expander("🔍 ヒントを表示"):
        st.write("AIは『計算のプロセス』を重視します。式を省かずに書いてみましょう。")
    st.session_state['c_t_val'] = st.text_area("計算式と答えを書いてください。", placeholder="例：1200×6=7200。7200×20=144000。答えは144,000円です。", value=st.session_state['c_t_val'], key="c_t_new")

with tab4:
    st.subheader("報告・相談力")
    st.write("作業中に道具を壊しましたが、上司がいません。戻った上司へ何と言いますか？")
    with st.expander("🔍 ヒントを表示"):
        st.write("『謝罪 ＋ 状況報告 ＋ 次の指示を仰ぐ』の3点を入れるのがプロの伝え方です。")
    st.session_state['m_t_val'] = st.text_area("具体的なセリフを書いてください。", placeholder="例：申し訳ありません。作業中に道具を破損してしまいました。怪我はありません。今後の指示をお願いします。", value=st.session_state['m_t_val'], key="m_t")

# ==========================================
# 6. 実行・結果表示
# ==========================================
st.divider()
if st.button("🚀 AI評価を開始（お守りシートを作成）", type="primary"):
    if not st.session_state['name']:
        st.error("左側で「氏名」を入力してください")
    else:
        with st.spinner("AIがあなたの才能を分析中..."):
            try:
                analyzer = TextAnalyzer()
                text_scores = analyzer.analyze({**text_responses, "reading": st.session_state['r_t_val'], "writing": st.session_state['w_t_val'], "calculation": st.session_state['c_t_val'], "communication": st.session_state['m_t_val']})
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(text_scores)
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], job_db)
                st.session_state['evaluated'] = True
                st.rerun()
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

if st.session_state.get('evaluated'):
    title = get_honorary_title(st.session_state['scores'])
    st.balloons()
    
    # お守り風ヘッダー
    st.markdown(f"""
    <div style="background-color:#fff5f5; padding:20px; border-radius:15px; border:2px solid #ff4b4b; text-align:center;">
        <h2 style="color:#ff4b4b; margin:0;">🎊 {st.session_state['name']} さんの称号 🎊</h2>
        <h1 style="font-size:3em; margin:10px 0;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1: st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with col2: st.plotly_chart(create_job_match_chart(st.session_state['job_matches'][:10]), use_container_width=True)

    # AIアドバイス
    st.divider()
    m = st.session_state['job_matches'][0]
    st.subheader("🤖 AIキャリア・アドバイス")
    st.write(f"あなたの最大の強みは**「{title.split('な')[0]}」**です。")
    st.info(f"最も相性が良いのは「{m['job']['name']}」で、適合率は {m['match_rate']}% です。あなたの誠実な回答がこの高い数値に繋がりました。")
    
    # PDFダウンロード（模擬ボタン）
    st.button("📄 診断結果をお守りシートとして保存する（準備中）")
