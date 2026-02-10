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
    # モバイル用にマージンを最小化
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=350, margin=dict(l=30, r=30, t=30, b=30))
    return fig

# ==========================================
# 2. 初期設定 & モバイル用CSS
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="centered") # 携帯で見やすい中央寄せ

# スマホでのフォントサイズやボタンの調整
st.markdown("""
    <style>
    .stButton>button { width: 100% !important; height: 3em; font-size: 1.2em !important; border-radius: 10px; }
    .stTextArea textarea { font-size: 16px !important; } /* iOSのズーム防止 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

keys = ['name', 'gender', 'age', 'dis_type', 'dis_detail', 'qualifications', 'life_goal', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 3. 画面UI
# ==========================================
st.title("🎯 O-lys AI評価システム")
st.error("⚠️ **はじめにお読みください**\n簡易的な診断です。結果のみで決断せず、障害者枠での仕事選びのヒントとしてお使いください。")

# プロフィール入力（スマホでは縦並びが基本）
with st.expander("👤 プロフィール・障害情報（タップして入力）", expanded=True):
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['dis_type'] = st.selectbox("障害種別", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な障害の内容", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHD、障害者1級など")

st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖読解", "✏️関わり", "🔢計算", "💬相談"])

with tab1:
    st.write("Q. お金以外の「働く意味」は何ですか？")
    st.session_state['r_t_val'] = st.text_area("回答", value=st.session_state['r_t_val'], key="r_m", height=100)
with tab2:
    st.write("Q. 誰かと関わって「良かった」エピソードは？")
    st.session_state['w_t_val'] = st.text_area("回答", value=st.session_state['w_t_val'], key="w_m", height=100)
with tab3:
    st.info("💡 問題：時給1,000円、1日5時間、月20日間働いた時の合計給料は？")
    st.session_state['c_t_val'] = st.text_area("式と答え", value=st.session_state['c_t_val'], key="c_m", placeholder="例：1000×5×20＝")
with tab4:
    st.write("Q. 道具を壊したあと、戻ってきた上司への第一声は？")
    st.session_state['m_t_val'] = st.text_area("セリフ", value=st.session_state['m_t_val'], key="m_m", height=100)

st.header("🌈 未来について")
st.session_state['life_goal'] = st.text_input("人生の最終ゴール", value=st.session_state['life_goal'], placeholder="例：幸せな家庭、一人暮らしなど")
st.session_state['qualifications'] = st.text_input("役立つ資格・目指す資格", value=st.session_state['qualifications'], placeholder="例：運転免許、簿記など")

# ==========================================
# 4. 分析実行・表示
# ==========================================
st.divider()
if st.button("🚀 強みを発見する（診断開始）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください。")
    else:
        with st.spinner("分析中..."):
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
    st.markdown(f"""<div style="background-color:#FFF9E6; padding:20px; border-radius:10px; border:2px solid #FFD700; text-align:center;">
        <h3 style="margin:0;">{st.session_state['name']} さんの可能性</h3>
        <h2 style="color:#333;">✨ {title} ✨</h2></div>""", unsafe_allow_html=True)

    st.write("#### 📊 強みチャート")
    st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)

    st.write("#### 🎯 活かせるお仕事 TOP10")
    df = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in st.session_state['job_matches'][:10]])
    fig = px.bar(df, x='適合度', y='職種', orientation='h', color='適合度', color_continuous_scale='YlGnBu')
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**エール：** 「{st.session_state['life_goal']}」に向けて、強み「{top_3[0]}」を大切にしましょう！")
