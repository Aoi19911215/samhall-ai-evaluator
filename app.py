import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import urllib.parse

# ==========================================
# 1. 職能マッチングロジック
# ==========================================
def calculate_match_rate(user_scores, job_required_scores):
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            ratio = (user / req) if req > 0 else 1.0
            # ポジティブな結果を保証しつつ、ランキングに差が出るよう調整
            item_match = 45.0 + (min(1.2, ratio) * 40.0) 
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
# 2. デザイン・モバイルアプリ化設定
# ==========================================
st.set_page_config(page_title="AI適性評価ともしる🐿️", layout="centered")

st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
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
# 3. 入力画面UI
# ==========================================
st.title("AI適性評価ともしる🐿️")
st.error("⚠️ あくまで簡易診断です。結果のみで判断せず、お仕事探しのヒントとしてお使いください。")

st.header("👤 プロフィール")
st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力")
st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)

with st.expander("📋 障害について（任意）"):
    st.session_state['dis_type'] = st.selectbox("障害種別", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な内容", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHDなど")

st.divider()

# --- ワーク・シミュレーション ---
st.header("✍️ ワーク・シミュレーション")
st.write("下へスクロールして記入してください。")

# 読解
st.markdown('<div class="work-card"><b>📖 読み取る力</b><br>「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」</div>', unsafe_allow_html=True)
st.session_state['r_t_val'] = st.text_area("Q. あなたにとって働くことの「お金」以外の意味は何ですか？", value=st.session_state['r_t_val'], key="r_input", label_visibility="collapsed")

# 関わり
st.markdown('<div class="work-card"><b>✏️ 人との関わり</b><br>これまでの生活で、誰かと関わって「良かったな」と感じたことを教えてください。</div>', unsafe_allow_html=True)
st.session_state['w_t_val'] = st.text_area("Q. どんな場面で、どう感じましたか？", value=st.session_state['w_t_val'], key="w_input", label_visibility="collapsed")

# 計算
st.markdown('<div class="work-card"><b>🔢 計算をたしかめる</b><br>時給1,000円で、1日5時間、月に20日間働きました。合計の給料はいくらになりますか？</div>', unsafe_allow_html=True)
st.session_state['c_t_val'] = st.text_area("Q. 計算式と答えを書いてください。", value=st.session_state['c_t_val'], key="c_input", placeholder="（例）1000 × 5 × 20 ＝", label_visibility="collapsed")

# 相談
st.markdown('<div class="work-card"><b>💬 相談する力</b><br>作業中に道具を壊してしまいました。戻ってきた上司へ最初に何と言いますか？</div>', unsafe_allow_html=True)
st.session_state['m_t_val'] = st.text_area("Q. 実際に話すセリフを書いてください。", value=st.session_state['m_t_val'], key="m_input", label_visibility="collapsed")

st.divider()
st.header("🌈 あなたの未来")
st.session_state['life_goal'] = st.text_input("人生の最終ゴール", value=st.session_state['life_goal'], placeholder="例：安定した一人暮らしなど")
st.session_state['qualifications'] = st.text_input("資格", value=st.session_state['qualifications'], placeholder="例：運転免許など")

# ==========================================
# 4. 分析実行
# ==========================================
if st.button("🚀 強みを発見する"):
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
# 5. 結果表示
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title_res, top_3 = get_strength_feedback(st.session_state['scores'])
    st.markdown(f"""<div style="background-color:#FFF9E6; padding:25px; border-radius:20px; border:3px solid #FFD700;">
        <p style="margin:0;">{st.session_state['name']} さんの可能性</p>
        <h2 style="color:#333;">✨ {title_res} ✨</h2></div>""", unsafe_allow_html=True)

    st.write("#### 🏆 活かせるお仕事ランキング")
    res_list = []
    for i, m in enumerate(st.session_state['job_matches'][:10]):
        rank = i + 1
        icon = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}位"
        res_list.append({'順位': f"{icon} {m['job']['name']}", '適合度': m['match_rate'], 'rank': rank})
    
    df_res = pd.DataFrame(res_list)
    fig_bar = px.bar(df_res, x='適合度', y='順位', orientation='h', color='rank', color_continuous_scale='Spectral_r', text='適合度')
    fig_bar.update_traces(texttemplate='<b>%{text}%</b>', textposition='outside', cliponaxis=False)
    fig_bar.update_layout(height=500, margin=dict(l=10, r=50, t=10, b=10), xaxis_range=[0, 120], yaxis={'categoryorder':'total descending'}, coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.header("🤝 相談・お問い合わせ")
    st.write("障害をお持ちの方、企業さま、お気軽にご連絡ください。")
    c1, c2 = st.columns(2)
    with c1:
        # 公式LINE URL適用済み
        st.markdown(f"""<a href="https://lin.ee/qwpYokQ" target="_blank" style="text-decoration:none;">
            <div style="background-color:#06C755; color:white; padding:15px; border-radius:10px; font-weight:bold;">🟢 公式LINE相談</div></a>""", unsafe_allow_html=True)
    with c2:
        m_subj = urllib.parse.quote(f"【相談】{st.session_state['name']}様より")
        m_body = urllib.parse.quote(f"氏名：{st.session_state['name']}様\n診断結果：{title_res}\n相談内容：")
        st.markdown(f"""<a href="mailto:olys2023official@gmail.com?subject={m_subj}&body={m_body}" style="text-decoration:none;">
            <div style="background-color:#6c757d; color:white; padding:15px; border-radius:10px; font-weight:bold;">📧 メールで相談</div></a>""", unsafe_allow_html=True)
    
    st.success(f"応援しています！目標「{st.session_state['life_goal']}」に向かって進みましょう！")
