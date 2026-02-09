import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. ロジック：強み分析・マッチング（閾値緩和版）
# ==========================================
def calculate_match_rate(user_scores, job_required_scores):
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            ratio = (user / req) if req > 0 else 1.0
            # どんなに低くても40%からスタートし、ポジティブな結果が出るよう調整
            item_match = 40.0 + (min(1.3, ratio) * 50.0) 
            match_sum += item_match
            count += 1
    final_rate = (match_sum / count) if count > 0 else 60.0
    return round(min(98.0, final_rate), 1)

def get_strength_feedback(scores):
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算をたしかめる", "communication": "相談する力"}
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    titles = {
        "calculation": "正確な仕事で信頼を築く実務の星",
        "communication": "周囲と協力して進める相談の達人",
        "writing": "相手の気持ちに寄り添う表現者",
        "reading": "大切な情報を的確に捉える理解のリーダー"
    }
    return titles.get(top_key, "期待のプロフェッショナル"), [labels.get(k, k) for k, v in sorted_s[:3]]

def create_radar_chart(scores):
    categories = ["読み取る力", "人との関わり", "計算をたしかめる", "相談する力"]
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=400)
    return fig

# ==========================================
# 2. 初期設定 & セッション管理
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

keys = [
    'name', 'gender', 'age', 'dis_type', 'dis_detail', 'qualifications', 'life_goal',
    'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated'
]
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 3. 画面UI：冒頭・注意書き
# ==========================================
st.title("🎯 O-lys AI評価システム")
st.error("⚠️ **はじめにお読みください**\n\nあくまで簡易的な診断のため、今回の結果のみで決断・行動にうつさないようにお気を付けください。このページでは「あなたが障害者枠でどんな仕事が向いているか」をアドバイスします。")

st.markdown("### ✨ あなたの「強み」を引き出す診断")
st.info("🔒 **個人情報の保護**: 入力内容は保存されず、ページを閉じると消去されます。")

# ==========================================
# 4. サイドバー：プロフィール・障害特性
# ==========================================
with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    
    st.divider()
    st.header("📋 障害について")
    st.session_state['dis_type'] = st.selectbox("障害種別は何ですか？", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("どんな障害かをおしえてください", value=st.session_state['dis_detail'], placeholder="例：障害者1級を持っています。障害の内容はASD、ADHDです。")

# ==========================================
# 5. UI：ワーク・シミュレーション
# ==========================================
st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算をたしかめる", "💬 相談する力"])

with tab1:
    st.write("**【メッセージ】**\n「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」")
    st.session_state['r_t_val'] = st.text_area("Q. あなたにとって、働くことの「お金」以外の意味は何だと思いますか？", value=st.session_state['r_t_val'], key="r_t_final")

with tab2:
    st.write("**【エピソード】**\nこれまでの生活の中で、誰かと関わって「良かったな」「助かったな」と感じたことを教えてください。")
    st.session_state['w_t_val'] = st.text_area("Q. どんな場面で、相手とどう関わり、どう感じましたか？", value=st.session_state['w_t_val'], key="w_t_final")

with tab3:
    st.write("**【計算】**")
    st.info("💡 問題：時給1,000円で、1日5時間、月に20日間働きました。合計の給料はいくらになりますか？")
    # --- 修正箇所：ヒントから答え（100,000）を削除しました ---
    st.session_state['c_t_val'] = st.text_area(
        "Q. 計算式と答えを書いてください。", 
        value=st.session_state['c_t_val'], 
        key="c_t_final", 
        placeholder="（書き方の例）時給 × 時間 × 日数 ＝ 合計金額"
    )

with tab4:
    st.write("**【場面】**\n作業中に道具を壊してしまいました。しばらくして、上司があなたのところへ戻ってきました。")
    st.session_state['m_t_val'] = st.text_area("Q. 戻ってきた上司へ、最初に何と言いますか？", value=st.session_state['m_t_val'], key="m_t_final")

# ==========================================
# 6. UI：未来のゴール・資格
# ==========================================
st.divider()
st.header("🌈 あなたの未来について")
col1, col2 = st.columns(2)
with col1:
    st.write("**人生の最終的なゴール**")
    st.session_state['life_goal'] = st.text_input("あなたの将来の目標を教えてください", value=st.session_state['life_goal'], placeholder="例：幸せな家庭、安定した一人暮らしなど")
with col2:
    st.write("**仕事に役立ちそうな資格**")
    st.session_state['qualifications'] = st.text_input("持っている、または興味のある資格を教えてください", value=st.session_state['qualifications'], placeholder="例：運転免許、英検、MOS（Excel）など")

# ==========================================
# 7. 分析実行・結果表示
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("「氏名」を入力してください。")
    else:
        with st.spinner("分析中..."):
            # デモ用スコア生成
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f).get('jobs', [])
                    results = [{"job": j, "match_rate": calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))} for j in db]
                    st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                    st.session_state['evaluated'] = True

if st.session_state['evaluated']:
    st.balloons()
    title, top_3 = get_strength_feedback(st.session_state['scores'])
    
    st.markdown(f"""
    <div style="background-color:#FFF9E6; padding:30px; border-radius:15px; border:3px solid #FFD700; text-align:center;">
        <h2 style="color:#B8860B; margin:0;">AIが見つけた {st.session_state['name']} さんの可能性</h2>
        <h1 style="font-size:3em;">✨ {title} ✨</h1>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.write("#### 📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with c2:
        st.write("#### 🎯 あなたの個性を活かせるお仕事")
        df = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in st.session_state['job_matches'][:10]])
        fig = px.bar(df, x='適合度', y='職種', orientation='h', color='適合度', color_continuous_scale='YlGnBu')
        fig.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    st.success(f"**未来へのエール：** 目標「{st.session_state['life_goal']}」に向けて、強み「{top_3[0]}」を活かして進みましょう！")
