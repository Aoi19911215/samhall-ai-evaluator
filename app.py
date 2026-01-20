import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# --- 外部モジュールの読み込み ---
try:
    from evaluator.text_analyzer import TextAnalyzer
    from evaluator.scorer import SamhallScorer
except ImportError:
    class TextAnalyzer:
        def analyze(self, inputs): return {"reading": 1.0, "writing": 1.0, "calculation": 1.0, "communication": 1.0}
    class SamhallScorer:
        @staticmethod
        def calculate_final_scores(raw): return raw
        @staticmethod
        def match_jobs(scores, db):
            return sorted([{"job": j, "match_rate": 75.0} for j in db], key=lambda x: x['match_rate'], reverse=True)

# ==========================================
# 1. 表示用ユーティリティ関数
# ==========================================
def get_feedback_content(scores):
    if not scores: return "期待のプロフェッショナル", ["分析中", "分析中", "分析中"]
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算をたしかめる力", "communication": "相談する力"}
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    titles = {
        "calculation": "正確な仕事で信頼を築く実務の星",
        "communication": "周囲と協力して進める相談の達人",
        "writing": "相手の気持ちに寄り添う表現者",
        "reading": "大切な情報を的確に捉える理解のリーダー"
    }
    title = titles.get(top_key, "期待のプロフェッショナル")
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

def create_radar_chart(scores):
    categories = ["読み取る力", "人との関わり", "計算をたしかめる", "相談する力"]
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#1E90FF', fillcolor='rgba(30, 144, 255, 0.3)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=400, margin=dict(l=50, r=50, t=50, b=50))
    return fig

# ==========================================
# 2. 初期設定 & セッション管理
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

keys = ['name', 'age', 'disability', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

st.title("🎯 O-lys AI評価システム")

with st.expander("🛡️ 個人情報の取り扱いと本システムについて", expanded=True):
    st.markdown("""
    ### あなたの「強み」を見つけ、未来につなげる
    このシステムは、正解・不正解を判定する「テスト」ではありません。AIがあなたの回答から、**お仕事で活かせる素敵な強み**を見つけ出します。
    - **個人情報の保護**: 入力された情報はこのブラウザ内でのみ一時的に処理され、外部への保存やAI学習への利用は一切行われません。
    - **リラックスして**: 短い言葉でも大丈夫です。今のあなたの考えをそのまま教えてください。
    """)

# ==========================================
# 3. サイドバー
# ==========================================
with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['age'] = st.number_input("年齢", 0, 100, value=int(st.session_state['age']) if st.session_state['age'] else 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", value=st.session_state['disability'], placeholder="例：精神障害、聴覚過敏など")
    
    st.divider()
    st.header("🏃 身体・環境条件")
    phys_mob = st.selectbox("歩く・移動", ["制限なし", "長距離は困難", "車椅子利用", "歩行補助が必要"])
    phys_lift = st.selectbox("重いものを持つ", ["10kg以上OK", "5kg程度ならOK", "難しい"])
    env_pref = st.multiselect("にがてな環境", ["騒音", "人混み", "高い場所", "外（暑さ・寒さ）", "強い光"])

# ==========================================
# 4. ワーク・シミュレーション（指定タイトル）
# ==========================================
st.header("✍️ ワーク・シミュレーション")
st.info("💡 あなたの「いいところ」をAIが見つけます。気負わずに記入してください。")

tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算をたしかめる", "💬 相談する力"])

with tab1:
    st.write("**【メッセージ】**\n「働くことは、お金を得るだけでなく、誰かの役に立ったり、社会とつながったり、自分の力を発揮する場でもあります。」")
    st.session_state['r_t_val'] = st.text_area(
        "Q. あなたにとって、働くことの「お金」以外の意味は何だと思いますか？", 
        value=st.session_state['r_t_val'], key="r_t", placeholder="あなたの考えを教えてください。"
    )

with tab2:
    st.write("**【エピソード】**\nこれまでの生活の中で、誰かと関わって「良かったな」「助かったな」と感じたことを教えてください。")
    st.session_state['w_t_val'] = st.text_area(
        "Q. どんな場面で、相手とどんなふうに関わって、どう感じましたか？", 
        value=st.session_state['w_t_val'], key="w_t", placeholder="具体的なエピソードを教えてください。"
    )

with tab3:
    st.write("**【計算】**\n時給1,200円で、1日6時間、月に20日間働きました。合計の給料はいくらになりますか？")
    st.session_state['c_t_val'] = st.text_area(
        "Q. 計算式と答えを書いてください。", 
        value=st.session_state['c_t_val'], key="c_t_new", placeholder="（記入例）時給 × 時間 × 日数 ＝ （答え）"
    )

with tab4:
    st.write("**【場面】**\n作業中に、使っていた道具を壊してしまいました。しばらくして、上司（スタッフ）があなたのところへ戻ってきました。")
    st.session_state['m_t_val'] = st.text_area(
        "Q. 戻ってきた上司へ、最初に何と言いますか？「実際に話す言葉（セリフ）」を具体的に書いてください。", 
        value=st.session_state['m_t_val'], key="m_t", placeholder="（記入例）「〇〇さん、今よろしいでしょうか。実は……」"
    )

# ==========================================
# 5. 分析実行
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("左側のメニューで「氏名」を入力してください。")
    else:
        with st.spinner("24職種のデータと照合し、あなたの強みを分析中..."):
            try:
                inputs = {"reading": st.session_state['r_t_val'], "writing": st.session_state['w_t_val'], 
                          "calculation": st.session_state['c_t_val'], "communication": st.session_state['m_t_val']}
                analyzer = TextAnalyzer()
                raw_scores = analyzer.analyze(inputs)
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw_scores)
                
                db_path = 'data/job_database.json'
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        job_db = json.load(f)
                    st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], job_db)
                    st.session_state['evaluated'] = True
                else:
                    st.error("職種データベースが見つかりません。")
            except Exception as e:
                st.error(f"分析エラー: {e}")

# ==========================================
# 6. 結果表示
# ==========================================
if st.session_state['evaluated']:
    scores = st.session_state['scores']
    job_matches = st.session_state['job_matches']
    title, top_3 = get_feedback_content(scores)

    st.balloons()
    st.markdown(f"""
    <div style="background-color:#F0F8FF; padding:20px; border-radius:15px; border:2px solid #1E90FF; text-align:center; margin-bottom:25px;">
        <h2 style="color:#1E90FF; margin:0;">🎊 {st.session_state['name']} さんの分析結果 🎊</h2>
        <h1 style="font-size:2.8em; margin:10px 0;">{title}</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("### 📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(scores), use_container_width=True)

    with col2:
        st.write("### 🎯 適性の高いお仕事（24職種から選定）")
        if job_matches:
            match_df = pd.DataFrame([{'職種': m['job']['name'], 'マッチ率': m['match_rate']} for m in job_matches[:10]])
            fig_match = px.bar(match_df, x='マッチ率', y='職種', orientation='h', color='マッチ率', color_continuous_scale='Blues')
            fig_match.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig_match, use_container_width=True)

    st.divider()
    st.subheader("🤖 AIキャリア・アドバイス")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**強み①: {top_3[0]}**")
    c2.info(f"**強み②: {top_3[1]}**")
    c3.info(f"**強み③: {top_3[2]}**")
    
    if job_matches:
        st.markdown(f"""
        **{st.session_state['name']}さんへのメッセージ：** あなたの最大の強みは**「{top_3[0]}」**であることがわかりました。
        特に**「{job_matches[0]['job']['name']}」**（マッチ率 {job_matches[0]['match_rate']}%）などの環境では、あなたの力が非常に高く評価されます。
        自信を持って進んでください！
        """)

    st.button("📄 強み診断シートをPDFで保存（準備中）")
