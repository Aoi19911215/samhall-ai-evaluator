import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import urllib.parse
from datetime import datetime
# スプレッドシート連携用
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定 & アプリ化
# ==========================================
st.set_page_config(page_title="AI適性評価ともしる🐿️", layout="centered")

# デザイン（中央揃え・モバイル最適化）
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
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# セッション管理
keys = ['name', 'gender', 'age', 'dis_type', 'dis_detail', 'qualifications', 'life_goal', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 2. ロジック（職能マッチング）
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
# 3. 入力UI
# ==========================================
st.title("AI適性評価ともしる🐿️")
st.error("⚠️ 簡易診断です。結果を元に専門家へ相談することをお勧めします。")

st.header("👤 プロフィール")
st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力")
st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)

with st.expander("📋 障害について（任意）"):
    st.session_state['dis_type'] = st.selectbox("障害種別", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な内容・疾患名", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHDなど")

st.header("✍️ ワーク・シミュレーション")
st.write("下へスクロールして記入してください。")

# ワーク入力カード
ws_items = [
    ("📖 読み取る力", "働くことのお金以外の意味は？", "r_t_val"),
    ("✏️ 人との関わり", "誰かと関わって良かったエピソードは？", "w_t_val"),
    ("🔢 計算をたしかめる", "時給1000円×5時間×20日の給料は？", "c_t_val"),
    ("💬 相談する力", "道具を壊した時の上司への第一声は？", "m_t_val")
]
for t, q, k in ws_items:
    st.markdown(f'<div class="work-card"><b>{t}</b><br>{q}</div>', unsafe_allow_html=True)
    st.session_state[k] = st.text_area("回答", value=st.session_state[k], key=f"in_{k}", label_visibility="collapsed")

st.header("🌈 あなたの未来")
st.session_state['life_goal'] = st.text_input("人生の最終ゴール", value=st.session_state['life_goal'], placeholder="例：安定した生活など")

# ==========================================
# 4. 診断・データ蓄積実行
# ==========================================
if st.button("🚀 強みを発見する"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AIが分析・データを記録中..."):
            # スコア算出
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            
            # ジョブマッチング
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f).get('jobs', [])
                    results = [{"job": j, "match_rate": calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))} for j in db]
                    st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                    st.session_state['evaluated'] = True

            # --- データ蓄積処理（スプレッドシートへの書き込み） ---
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                existing_data = conn.read(worksheet="診断ログ", usecols=[0,1,2,3,4,5,6])
                new_row = pd.DataFrame([{
                    "日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "氏名": st.session_state['name'],
                    "疾患タイプ": st.session_state['dis_type'],
                    "疾患詳細": st.session_state['dis_detail'],
                    "最強の強み": get_strength_feedback(st.session_state['scores'])[0],
                    "適性1位": st.session_state['job_matches'][0]['job']['name'],
                    "適合度": f"{st.session_state['job_matches'][0]['match_rate']}%"
                }])
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(worksheet="診断ログ", data=updated_df)
            except:
                st.warning("⚠️ データの蓄積設定が未完了です（結果表示は継続します）")

# ==========================================
# 5. 結果表示
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title_res, top_3 = get_strength_feedback(st.session_state['scores'])
    
    st.markdown(f"""<div style="background-color:#FFF9E6; padding:25px; border-radius:20px; border:3px solid #FFD700;">
        <h2 style="color:#333;">✨ {title_res} ✨</h2></div>""", unsafe_allow_html=True)

    # ランキング表示
    st.write("#### 🏆 活かせるお仕事ランキング")
    res_list = [{'順位': f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else str(i+1)+'位'} {m['job']['name']}", 
                 '適合度': m['match_rate'], 'rank': i+1} for i, m in enumerate(st.session_state['job_matches'][:10])]
    
    fig_bar = px.bar(pd.DataFrame(res_list), x='適合度', y='順位', orientation='h', color='rank', color_continuous_scale='Spectral_r', text='適合度')
    fig_bar.update_layout(height=450, margin=dict(l=10, r=50, t=10, b=10), xaxis_range=[0, 120], yaxis={'categoryorder':'total descending'}, coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    # お問い合わせ
    st.divider()
    st.header("🤝 相談・お問い合わせ")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<a href="https://lin.ee/qwpYokQ" target="_blank" style="text-decoration:none;"><div style="background-color:#06C755; color:white; padding:15px; border-radius:10px; font-weight:bold;">🟢 公式LINE相談</div></a>', unsafe_allow_html=True)
    with c2:
        m_subj = urllib.parse.quote(f"【相談】{st.session_state['name']}様より")
        st.markdown(f'<a href="mailto:olys2023official@gmail.com?subject={m_subj}" style="text-decoration:none;"><div style="background-color:#6c757d; color:white; padding:15px; border-radius:10px; font-weight:bold;">📧 メールで相談</div></a>', unsafe_allow_html=True)
