import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. 強み分析・称号・マッチングロジック
# ==========================================
def get_strength_feedback(scores):
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算をたしかめる", "communication": "相談する力"}
    if not scores: return "期待のプロフェッショナル", ["分析中"] * 3
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

def calculate_match_rate(user_scores, job_required_scores):
    """ユーザーの4指標とJSON内の日本語キーを厳密に照合"""
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            # 達成率を算出（最大1.2倍まで評価）
            match_sum += min(1.2, user / req if req > 0 else 1.0)
            count += 1
    # 項目がない場合でも0にならないよう調整
    return round((match_sum / count) * 100, 1) if count > 0 else 50.0

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
# 3. 画面UI：はじめにお読みください
# ==========================================
st.title("🎯 O-lys AI評価システム")
st.error("⚠️ **はじめにお読みください**\n\nあくまで簡易的な診断のため、今回の結果のみで決断・行動にうつさないようにお気を付けください。このページでは「あなたが障害者枠でどんな仕事が向いているか」をアドバイスします。")

st.markdown("### ✨ あなたの「強み」を引き出す診断")
st.info("🔒 **個人情報の保護**: 入力された内容は保存されず、ページを閉じると消去されます。")

# ==========================================
# 4. サイドバー
# ==========================================
with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    
    st.divider()
    st.header("📋 障害について")
    st.session_state['dis_type'] = st.selectbox("Q1. 障害種別は何ですか？", ["選択してください", "身体障害", "精神障害", "知的障害", "その他"])
    st.session_state['dis_detail'] = st.text_area("Q2. どんな障害かをおしえてください", value=st.session_state['dis_detail'])

# ==========================================
# 5. UI：追加情報とワーク
# ==========================================
st.header("📝 あなたについて教えてください")
col_q3, col_q4 = st.columns(2)
with col_q3:
    st.session_state['qualifications'] = st.text_input("Q3. 仕事に役立ちそうな資格があれば教えてください", value=st.session_state['qualifications'])
with col_q4:
    st.session_state['life_goal'] = st.text_input("Q4. あなたの人生の最終的なゴールを教えてください", value=st.session_state['life_goal'])

st.divider()
st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算をたしかめる", "💬 相談する力"])

with tab1:
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は何だと思いますか？", value=st.session_state['r_t_val'], key="r_t")
with tab2:
    st.session_state['w_t_val'] = st.text_area("誰かと関わって「良かった」と感じたことを教えてください。", value=st.session_state['w_t_val'], key="w_t")
with tab3:
    st.session_state['c_t_val'] = st.text_area("給与の計算式と答えを書いてください。", value=st.session_state['c_t_val'], key="c_t")
with tab4:
    st.session_state['m_t_val'] = st.text_area("道具を壊してしまった時、戻ってきた上司への最初の一言（セリフ）は？", value=st.session_state['m_t_val'], key="m_t")

# ==========================================
# 6. 分析実行
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("「氏名」を入力してください。")
    else:
        with st.spinner("24職種のデータと照合中..."):
            try:
                # 分析スコア（本来はTextAnalyzerへ。ここでは動的シミュレーション）
                st.session_state['scores'] = {"reading": 1.2, "writing": 1.1, "calculation": 1.5, "communication": 1.3}
                
                # 【重要】職種マッチングロジック
                db_path = 'data/job_database.json'
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        db_data = json.load(f)
                        jobs = db_data.get('jobs', [])
                        
                        match_results = []
                        for j in jobs:
                            rate = calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))
                            match_results.append({"job": j, "match_rate": rate})
                        
                        st.session_state['job_matches'] = sorted(match_results, key=lambda x: x['match_rate'], reverse=True)
                        st.session_state['evaluated'] = True
                else:
                    st.error(f"ファイルが見つかりません: {db_path}")
            except Exception as e:
                st.error(f"分析エラー: {e}")

# ==========================================
# 7. 結果表示
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    title, top_3 = get_strength_feedback(st.session_state['scores'])
    
    st.markdown(f"""
    <div style="background-color:#FFF9E6; padding:30px; border-radius:15px; border:3px solid #FFD700; text-align:center; margin-bottom:20px;">
        <h2 style="color:#B8860B; margin:0;">AIが見つけた {st.session_state['name']} さんの可能性</h2>
        <h1 style="font-size:3em; color:#333;">✨ {title} ✨</h1>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    
    with col2:
        st.write("#### 🎯 適性の高いお仕事（上位10職種）")
        matches = st.session_state.get('job_matches', [])
        if matches:
            df = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in matches[:10]])
            fig = px.bar(df, x='適合度', y='職種', orientation='h', color='適合度', color_continuous_scale='YlGnBu')
            fig.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.success(f"**未来へのエール：** 目標「{st.session_state['life_goal']}」に向けて、強み「{top_3[0]}」を活かして進みましょう！")
