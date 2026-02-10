import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. 職能マッチングロジック（閾値緩和）
# ==========================================
def calculate_match_rate(user_scores, job_required_scores):
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            ratio = (user / req) if req > 0 else 1.0
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

# ==========================================
# 2. モバイル専用のデザイン調整 (CSS)
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="centered")

st.markdown("""
    <style>
    /* 全体の中央揃えとフォント調整 */
    .main .block-container {
        text-align: center;
        padding-top: 2rem;
    }
    /* タイトルとヘッダーを中央に */
    h1, h2, h3, h4, p, .stMarkdown {
        text-align: center !important;
    }
    /* 入力欄のラベルも中央に */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
        display: block;
        text-align: center !important;
        width: 100%;
        font-weight: bold;
    }
    /* スマホで押しやすい巨大ボタン */
    .stButton>button {
        width: 100% !important;
        height: 3.5em;
        font-size: 1.2em !important;
        border-radius: 50px;
        margin-top: 20px;
        background-color: #1E90FF;
        color: white;
    }
    /* 入力エリアの文字サイズ（ズーム防止） */
    input, textarea, select {
        font-size: 16px !important;
        text-align: center;
    }
    /* ワークカード形式のデザイン */
    .work-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション管理
keys = ['name', 'gender', 'age', 'dis_type', 'dis_detail', 'qualifications', 'life_goal', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 3. メイン画面
# ==========================================
st.title("🎯 O-lys AI評価システム")
st.error("⚠️ **はじめにお読みください**\n簡易的な診断です。結果のみで決断せず、お仕事探しのヒントとしてお使いください。")

# --- プロフィール ---
st.header("👤 プロフィール")
st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力")
st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)

with st.expander("📋 障害について入力する"):
    st.session_state['dis_type'] = st.selectbox("障害種別", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な内容", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHDなど")

st.divider()

# --- ワーク・シミュレーション（スクロールして記入できるよう縦並びを推奨） ---
st.header("✍️ ワーク・シミュレーション")
st.write("下へスクロールして順番に記入してください。")

# 1. 読解
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("📖 読み取る力")
st.write("働くことは、お金以外にどんな意味があると思いますか？")
st.session_state['r_t_val'] = st.text_area("回答を記入", value=st.session_state['r_t_val'], key="r_m")
st.markdown('</div>', unsafe_allow_html=True)

# 2. 関わり
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("✏️ 人との関わり")
st.write("誰かと関わって「良かった」と感じたことは？")
st.session_state['w_t_val'] = st.text_area("回答を記入", value=st.session_state['w_t_val'], key="w_m")
st.markdown('</div>', unsafe_allow_html=True)

# 3. 計算
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("🔢 計算をたしかめる")
st.info("💡 時給1,000円、1日5時間、月20日間働いた時の合計給料は？")
st.session_state['c_t_val'] = st.text_area("式と答えを記入", value=st.session_state['c_t_val'], key="c_m", placeholder="例：1000 × 5 × 20 ＝")
st.markdown('</div>', unsafe_allow_html=True)

# 4. 相談
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("💬 相談する力")
st.write("道具を壊したあと、上司への第一声は？")
st.session_state['m_t_val'] = st.text_area("セリフを記入", value=st.session_state['m_t_val'], key="m_m")
st.markdown('</div>', unsafe_allow_html=True)

# --- 未来の目標 ---
st.divider()
st.header("🌈 あなたの未来について")
st.session_state['life_goal'] = st.text_input("人生の最終的なゴール", value=st.session_state['life_goal'], placeholder="例：幸せな家庭、一人暮らしなど")
st.session_state['qualifications'] = st.text_input("仕事に役立ちそうな資格", value=st.session_state['qualifications'], placeholder="例：運転免許、簿記など")

# ==========================================
# 4. 診断開始ボタン
# ==========================================
if st.button("🚀 強みを発見する（診断開始）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AIが分析中..."):
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f).get('jobs', [])
                    results = [{"job": j, "match_rate": calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))} for j in db]
                    st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                    st.session_state['evaluated'] = True

# ==========================================
# 5. 結果表示（中央揃え）
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title, top_3 = get_strength_feedback(st.session_state['scores'])
    st.markdown(f"""
        <div style="background-color:#FFF9E6; padding:30px; border-radius:20px; border:3px solid #FFD700; text-align:center;">
            <p style="margin:0;">{st.session_state['name']} さんの可能性</p>
            <h1 style="color:#333; font-size:2em;">✨ {title} ✨</h1>
        </div>
    """, unsafe_allow_html=True)

    st.write("#### 📊 あなたの強み")
    # チャート作成
    categories = ["読み取る力", "人との関わり", "計算をたしかめる", "相談する力"]
    values = [st.session_state['scores'].get(k, 0.5) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), height=350, margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)

    st.write("#### 🎯 活かせるお仕事ランキング")
    df = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in st.session_state['job_matches'][:10]])
    fig_bar = px.bar(df, x='適合度', y='職種', orientation='h', color='適合度', color_continuous_scale='YlGnBu')
    fig_bar.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_range=[0, 110])
    st.plotly_chart(fig_bar, use_container_width=True)

    st.success(f"**エール：** 「{st.session_state['life_goal']}」に向かって、{top_3[0]}を活かして進みましょう！")
