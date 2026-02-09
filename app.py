import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. 強み分析・称号生成ロジック
# ==========================================
def get_strength_feedback(scores):
    """高いスコアに基づいた称号と強みラベルを返す"""
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算をたしかめる", "communication": "相談する力"}
    if not scores: return "期待のプロフェッショナル", ["分析中"] * 3
    
    # スコア順にソート
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    
    # 強みを引き出すためのポジティブな称号
    titles = {
        "calculation": "正確な仕事で信頼を築く実務の星",
        "communication": "周囲と協力して進める相談の達人",
        "writing": "相手の気持ちに寄り添う表現者",
        "reading": "大切な情報を的確に捉える理解のリーダー"
    }
    main_title = titles.get(top_key, "期待のプロフェッショナル")
    top_3_labels = [labels.get(k, k) for k, v in sorted_s[:3]]
    
    return main_title, top_3_labels

def create_radar_chart(scores):
    """強みチャート（レーダーチャート）の生成"""
    categories = ["読み取る力", "人との関わり", "計算をたしかめる", "相談する力"]
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself', 
        fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])), 
        showlegend=False, height=400, margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def calculate_match_rate(user_scores, job_required_scores):
    """ユーザー指標と職種データの必要スコアを照合"""
    mapping = {"読解力": "reading", "文書作成力": "writing", "計算力": "calculation", "コミュニケーション力": "communication"}
    match_sum, count = 0, 0
    for jp_key, en_key in mapping.items():
        if jp_key in job_required_scores:
            req = job_required_scores[jp_key]
            user = user_scores.get(en_key, 0)
            # 達成率を算出（最大1.2倍まで評価）
            match_sum += min(1.2, user / req if req > 0 else 1.0)
            count += 1
    return round((match_sum / count) * 100, 1) if count > 0 else 0

# ==========================================
# 2. 初期設定 & セッション管理（個人情報保護）
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

# 入力情報を保持（ページを閉じると消去されるブラウザメモリを使用）
keys = ['name', 'gender', 'age', 'disability', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 3. 画面UI：説明文とプロフィール
# ==========================================
st.title("🎯 O-lys AI評価システム")

st.markdown("""
### ✨ あなたの「できる」を見つける診断
このシステムは、単にスキルを測るためのものではありません。
日々のワークを通じて、**あなたの中に眠っている「個人の強み」を引き出し、活かせる場所を見つけるため**のものです。
""")

st.info("🔒 **個人情報の保護**: 入力された氏名、性別、配慮事項等は保存されず、ページを閉じると消去されます。AIの学習にも利用されません。")

with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", value=st.session_state['disability'], placeholder="例：精神障害など")
    
    st.divider()
    st.header("🏃 身体・環境条件")
    st.selectbox("歩く・移動", ["制限なし", "長距離は困難", "車椅子利用"])
    st.multiselect("にがてな環境", ["騒音", "人混み", "高い場所", "外（暑さ・寒さ）"])

# ==========================================
# 4. 画面UI：ワーク・シミュレーション
# ==========================================
st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算をたしかめる", "💬 相談する力"])

with tab1:
    st.write("**【メッセージ】**\n「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」")
    st.session_state['r_t_val'] = st.text_area("Q. あなたにとって、働くことの「お金」以外の意味は何だと思いますか？", value=st.session_state['r_t_val'], key="r_t")
with tab2:
    st.write("**【エピソード】**\nこれまでの生活の中で、誰かと関わって「良かったな」と感じたことを教えてください。")
    st.session_state['w_t_val'] = st.text_area("Q. どんな場面で、相手とどう関わり、どう感じましたか？", value=st.session_state['w_t_val'], key="w_t")
with tab3:
    st.write("**【計算】**\n時給1,200円で、1日6時間、月に20日間働きました。合計の給料はいくらになりますか？")
    st.session_state['c_t_val'] = st.text_area("Q. 計算式と答えを書いてください。", value=st.session_state['c_t_val'], key="c_t")
with tab4:
    st.write("**【場面】**\n作業中に道具を壊してしまいました。しばらくして、上司があなたのところへ戻ってきました。")
    st.session_state['m_t_val'] = st.text_area("Q. 戻ってきた上司へ、最初に何と言いますか？", value=st.session_state['m_t_val'], key="m_t")

# ==========================================
# 5. 分析実行
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("プロフィール欄に「氏名」を入力してください。")
    else:
        with st.spinner("あなたの「強み」を分析中..."):
            try:
                # 分析スコア（本来はTextAnalyzerを使用。ここではデモ用の動的な値を想定）
                st.session_state['scores'] = {"reading": 1.2, "writing": 1.1, "calculation": 1.5, "communication": 1.3}
                
                db_path = 'data/job_database.json'
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        db_data = json.load(f)
                        jobs = db_data.get('jobs', [])
                        results = []
                        for j in jobs:
                            rate = calculate_match_rate(st.session_state['scores'], j.get('required_scores', {}))
                            results.append({"job": j, "match_rate": rate})
                        
                        st.session_state['job_matches'] = sorted(results, key=lambda x: x['match_rate'], reverse=True)
                        st.session_state['evaluated'] = True
                else:
                    st.error("job_database.json が見つかりません。")
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

# ==========================================
# 6. 結果表示（強み引き出しセクション）
# ==========================================
if st.session_state['evaluated']:
    st.balloons()
    main_title, top_3 = get_strength_feedback(st.session_state['scores'])
    
    st.markdown(f"""
    <div style="background-color:#FFF9E6; padding:30px; border-radius:15px; border:3px solid #FFD700; text-align:center; margin-bottom:25px;">
        <h2 style="color:#B8860B; margin:0;">AIが見つけた {st.session_state['name']} さんの可能性</h2>
        <h1 style="font-size:3em; margin:15px 0; color:#333;">✨ {main_title} ✨</h1>
        <p style="font-size:1.2em; color:#666;">この診断は、あなたの新しい一歩を応援するためのものです。</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)

    with col2:
        st.subheader("💡 引き出された3つの強み")
        st.info(f"**1. {top_3[0]}**\n現場で最も頼りにされるあなたの核となる力です。")
        st.info(f"**2. {top_3[1]}**\n周囲との円滑な関係や、丁寧な仕事につながる力です。")
        st.info(f"**3. {top_3[2]}**\nこれからの成長を支える、素晴らしいポテンシャルです。")

    st.divider()
    st.subheader("🎯 力を発揮しやすいお仕事（24職種から選定）")
    matches = st.session_state['job_matches']
    if matches:
        df = pd.DataFrame([{'職種': m['job']['name'], '適合度': m['match_rate']} for m in matches[:10]])
        if not df.empty:
            fig = px.bar(df, x='適合度', y='職種', orientation='h', color='適合度', color_continuous_scale='YlGnBu')
            fig.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    best_job = matches[0]['job']
    st.success(f"**{st.session_state['name']}さんへのアドバイス**\n\n最も適性が高いのは **{best_job['name']}** です。\n{best_job['support']}などのサポートを受けながら、あなたの「{top_3[0]}」を存分に活かしてください。")
