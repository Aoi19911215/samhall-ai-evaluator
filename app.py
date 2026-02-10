import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(page_title="AI適性評価ともしる🐿️", layout="centered")

st.markdown("""
    <style>
    .main .block-container { text-align: center; padding-top: 1rem; }
    h1, h2, h3, h4, p, .stMarkdown { text-align: center !important; }
    input, textarea, select { font-size: 16px !important; text-align: center; border-radius: 12px !important; }
    .stButton>button {
        width: 100% !important; height: 4em; font-size: 1.2em !important;
        border-radius: 50px; background-color: #1E90FF; color: white; font-weight: bold;
    }
    .work-card {
        background-color: #f8f9fa; padding: 20px; border-radius: 15px;
        margin-bottom: 20px; border: 1px solid #eee; text-align: left;
    }
    .top3-card {
        background-color: #fffceb; padding: 15px; border: 2px solid #ffd700;
        border-radius: 15px; margin-bottom: 10px;
    }
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# セッション管理
keys = ['name', 'gender', 'age', 'dis_type', 'dis_detail', 'qualifications', 'life_goal', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 2. ロジック
# ==========================================
def calculate_match_rate(user_scores, job_required_scores):
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            ratio = (user / req) if req > 0 else 1.0
            item_match = 45.0 + (min(1.2, ratio) * 40.0) 
            match_sum += item_match
            count += 1
    return round(min(98.0, (match_sum / count) if count > 0 else 60.0), 1)

def get_strength_feedback(scores):
    titles = {
        "calculation": "正確な仕事で信頼を築く実務の星",
        "communication": "周囲と協力して進める相談の達人",
        "writing": "相手の気持ちに寄り添う表現者",
        "reading": "大切な情報を的確に捉える理解のリーダー"
    }
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return titles.get(sorted_s[0][0], "期待のプロフェッショナル")

# ==========================================
# 3. 入力画面UI
# ==========================================
st.title("AI適性評価ともしる🐿️")

st.header("👤 プロフィール")
st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力")

with st.expander("📋 障害について（任意）"):
    st.session_state['dis_type'] = st.selectbox("障害種別", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な内容", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHDなど")

st.divider()

# --- ワーク・シミュレーション (問いを明示) ---
st.header("✍️ ワーク・シミュレーション")

# 1. 読解
st.markdown('<div class="work-card"><b>📖 ワーク1：読み取る力</b><br>「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」</div>', unsafe_allow_html=True)
st.session_state['r_t_val'] = st.text_area("【問い】あなたにとって働くことの「お金」以外の意味は何ですか？", value=st.session_state['r_t_val'], key="q1")

# 2. 関わり
st.markdown('<div class="work-card"><b>✏️ ワーク2：人との関わり</b><br>これまでの生活で、誰かと関わって「良かったな」と感じたことを教えてください。</div>', unsafe_allow_html=True)
st.session_state['w_t_val'] = st.text_area("【問い】どんな場面で、どう感じましたか？", value=st.session_state['w_t_val'], key="q2")

# 3. 計算
st.markdown('<div class="work-card"><b>🔢 ワーク3：計算をたしかめる</b><br>時給1,000円、1日5時間、月に20日間働きました。</div>', unsafe_allow_html=True)
st.session_state['c_t_val'] = st.text_area("【問い】合計の給料はいくらになりますか？計算式と答えを書いてください。", value=st.session_state['c_t_val'], key="q3")

# 4. 相談
st.markdown('<div class="work-card"><b>💬 ワーク4：相談する力</b><br>作業中に道具を壊してしまいました。戻ってきた上司へ最初に何と言いますか？</div>', unsafe_allow_html=True)
st.session_state['m_t_val'] = st.text_area("【問い】実際に話すセリフを書いてください。", value=st.session_state['m_t_val'], key="q4")

st.divider()
st.session_state['life_goal'] = st.text_input("🌈 人生の最終ゴール", value=st.session_state['life_goal'], placeholder="例：自分らしく自立した生活")

# ==========================================
# 4. 実行 & データ蓄積
# ==========================================
if st.button("🚀 強みを発見する"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AI分析中..."):
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f).get('jobs', [])
                    # 「清掃スタッフ」を除外してマッチング
                    results = [
                        {"job": j, "match_rate": calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))} 
                        for j in db if "清掃" not in j['name']
                    ]
                    st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                    st.session_state['evaluated'] = True
            
            # データ蓄積 (スプレッドシート)
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                existing_data = conn.read(worksheet="診断ログ")
                new_row = pd.DataFrame([{
                    "日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "氏名": st.session_state['name'],
                    "疾患タイプ": st.session_state['dis_type'],
                    "強み": get_strength_feedback(st.session_state['scores']),
                    "適性1位": st.session_state['job_matches'][0]['job']['name']
                }])
                conn.update(worksheet="診断ログ", data=pd.concat([existing_data, new_row]))
            except: pass

# ==========================================
# 5. 結果表示 (Top3形式)
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title_res = get_strength_feedback(st.session_state['scores'])
    st.success(f"### ✨ {st.session_state['name']}さんの診断結果\n## {title_res}")

    st.write("### 🏆 活かせるお仕事 TOP3")
    for i, m in enumerate(st.session_state['job_matches'][:3]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        st.markdown(f"""<div class="top3-card">
            <span style="font-size:1.5em;">{medal} {m['job']['name']}</span><br>
            <b>適合度: {m['match_rate']}%</b>
        </div>""", unsafe_allow_html=True)

    # お問い合わせ
    st.divider()
    st.write("障害をお持ちの方、企業さま、お気軽にお問い合わせください。")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="https://lin.ee/qwpYokQ" target="_blank" style="text-decoration:none;"><div style="background-color:#06C755; color:white; padding:15px; border-radius:10px; font-weight:bold;">🟢 公式LINE相談</div></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="mailto:olys2023official@gmail.com" style="text-decoration:none;"><div style="background-color:#6c757d; color:white; padding:15px; border-radius:10px; font-weight:bold;">📧 メールで相談</div></a>', unsafe_allow_html=True)
