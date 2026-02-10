import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. 職能マッチングロジック（閾値緩和・加点方式）
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

# ==========================================
# 2. デザインカスタマイズ (モバイル・アプリ化設定)
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="centered")

st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
    <style>
    /* 全体の中央揃え */
    .main .block-container { text-align: center; padding-top: 1.5rem; }
    h1, h2, h3, h4, p, .stMarkdown { text-align: center !important; }
    
    /* 入力エリアの調整 */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
        display: block; text-align: center !important; width: 100%; font-weight: bold;
    }
    input, textarea, select { font-size: 16px !important; text-align: center; border-radius: 8px !important; }
    
    /* 巨大な診断ボタン */
    .stButton>button {
        width: 100% !important; height: 3.8em; font-size: 1.3em !important;
        border-radius: 50px; margin-top: 25px; background-color: #1E90FF; color: white;
        font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* ワークカード形式（スクロールしやすく） */
    .work-card {
        background-color: #f8f9fa; padding: 25px; border-radius: 20px;
        margin-bottom: 25px; border: 1px solid #eee; text-align: left;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* ヘッダー等を隠してアプリ感を出す */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
st.error("⚠️ **はじめにお読みください**\nあくまで簡易的な診断のため、今回の結果のみで決断・行動にうつさないようにお気を付けください。このページでは「あなたが障害者枠でどんな仕事が向いているか」をアドバイスします。")

st.info("🔒 **個人情報の保護**: 入力内容は保存されず、ページを閉じると消去されます。")

# --- プロフィール ---
st.header("👤 プロフィール")
st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力してください")
st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)

with st.expander("📋 障害について入力する（任意）"):
    st.session_state['dis_type'] = st.selectbox("障害種別は何ですか？", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("具体的な障害の内容", value=st.session_state['dis_detail'], placeholder="例：ASD、ADHD、障害者1級など")

st.divider()

# --- ワーク・シミュレーション (縦にスクロールして記入) ---
st.header("✍️ ワーク・シミュレーション")
st.write("下へスクロールしながら順番に記入してください。")

# 1. 読解
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("📖 読み取る力")
st.write("「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」")
st.session_state['r_t_val'] = st.text_area("Q. あなたにとって働くことの「お金」以外の意味は何ですか？", value=st.session_state['r_t_val'], key="r_final_f")
st.markdown('</div>', unsafe_allow_html=True)

# 2. 関わり
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("✏️ 人との関わり")
st.write("これまでの生活で、誰かと関わって「良かったな」と感じたことを教えてください。")
st.session_state['w_t_val'] = st.text_area("Q. どんな場面で、どう感じましたか？", value=st.session_state['w_t_val'], key="w_final_f")
st.markdown('</div>', unsafe_allow_html=True)

# 3. 計算 (暗算しやすい問題)
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("🔢 計算をたしかめる")
st.info("💡 問題：時給1,000円で、1日5時間、月に20日間働きました。合計の給料はいくらになりますか？")
st.session_state['c_t_val'] = st.text_area("Q. 計算式と答えを書いてください。", value=st.session_state['c_t_val'], key="c_final_f", placeholder="（書き方の例）時給 × 時間 × 日数 ＝ 合計金額")
st.markdown('</div>', unsafe_allow_html=True)

# 4. 相談
st.markdown('<div class="work-card">', unsafe_allow_html=True)
st.subheader("💬 相談する力")
st.write("作業中に道具を壊してしまいました。戻ってきた上司へ最初に何と言いますか？")
st.session_state['m_t_val'] = st.text_area("Q. 実際に話すセリフを書いてください。", value=st.session_state['m_t_val'], key="m_final_f")
st.markdown('</div>', unsafe_allow_html=True)

# --- 未来の目標 ---
st.divider()
st.header("🌈 あなたの未来について")
st.session_state['life_goal'] = st.text_input("人生の最終的なゴール", value=st.session_state['life_goal'], placeholder="例：幸せな家庭、安定した一人暮らしなど")
st.session_state['qualifications'] = st.text_input("仕事に役立ちそうな資格", value=st.session_state['qualifications'], placeholder="例：運転免許、英検2級、簿記など")

# ==========================================
# 4. 分析実行
# ==========================================
st.divider()
if st.button("🚀 強みを発見する（診断開始）", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("AIが24職種から分析中..."):
            # シミュレーション用スコア
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f).get('jobs', [])
                    results = [{"job": j, "match_rate": calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))} for j in db]
                    st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                    st.session_state['evaluated'] = True
            else:
                st.error("職種データベースが見つかりません。")

# ==========================================
# 5. 結果表示 (多色・中央揃え)
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title, top_3 = get_strength_feedback(st.session_state['scores'])
    st.markdown(f"""
        <div style="background-color:#FFF9E6; padding:30px; border-radius:20px; border:3px solid #FFD700; text-align:center;">
            <p style="margin:0; font-weight:bold; color:#B8860B;">{st.session_state['name']} さんの可能性</p>
            <h1 style="color:#333; font-size:2.2em; margin-top:10px;">✨ {title} ✨</h1>
        </div>
    """, unsafe_allow_html=True)

    st.write("#### 📊 あなたの強み分析")
    
    categories = ["読み取る力", "人との関わり", "計算をたしかめる", "相談する力"]
    values = [st.session_state['scores'].get(k, 0.5) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), height=350, margin=dict(l=45, r=45, t=45, b=45))
    st.plotly_chart(fig, use_container_width=True)

    st.write("#### 🎯 活かせるお仕事ランキング TOP10")
    df_res = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in st.session_state['job_matches'][:10]])
    
    # 多色ランキンググラフ
    fig_bar = px.bar(
        df_res, x='適合度', y='職種', orientation='h', color='適合度',
        color_continuous_scale='Spectral_r', text='適合度'
    )
    fig_bar.update_traces(texttemplate='<b>%{text}%</b>', textposition='inside', marker_line_color='rgb(8,48,107)', marker_line_width=1.2)
    fig_bar.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10), xaxis_range=[0, 115], yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

    st.success(f"**未来へのエール：**\n目標である「{st.session_state['life_goal']}」に向けて、あなたの最大の強みである「{top_3[0]}」を自信に変えていきましょう！応援しています！")
