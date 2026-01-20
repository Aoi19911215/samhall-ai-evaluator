import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. 強み・称号・マッチングロジック
# ==========================================
def get_strength_feedback(scores):
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算する力", "communication": "相談する力"}
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
    categories = ["読み取る力", "人との関わり", "計算する力", "相談する力"]
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=400)
    return fig

# ==========================================
# 2. 初期設定 & セッション管理（個人情報保護の核）
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

# 入力情報を保持。ページを閉じるとここにある情報はすべて消去されます。
keys = ['name', 'gender', 'age', 'disability', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches', 'evaluated']
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

# ==========================================
# 3. 画面レイアウト
# ==========================================
st.title("🎯 O-lys AI評価システム")

# --- 個人情報の取り扱い（冒頭に配置） ---
st.warning("🔒 **個人情報の保護について**：入力された「氏名」「性別」「障害特性」や回答内容は、この画面を表示している間のみ一時的に使用されます。外部のサーバーに保存されたり、AIの学習に利用されたりすることはありません。")

with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'], placeholder="お名前を入力")
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", value=st.session_state['disability'], placeholder="例：精神障害など")
    
    st.divider()
    st.header("🏃 身体・環境条件")
    st.selectbox("歩く・移動", ["制限なし", "長距離は困難", "車椅子利用"])
    st.multiselect("にがてな環境", ["騒音", "人混み", "高い場所", "外（暑さ・寒さ）"])

st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算する力", "💬 相談する力"])

with tab1:
    st.write("**【メッセージ】**\n「働くことは、お金を得るだけでなく、社会とつながったり、自分の力を発揮する場でもあります。」")
    st.session_state['r_t_val'] = st.text_area("Q. あなたにとって、働くことの「お金」以外の意味は何だと思いますか？", key="r_t")
with tab2:
    st.write("**【エピソード】**\n誰かと関わって「良かったな」「助かったな」と感じたことを教えてください。")
    st.session_state['w_t_val'] = st.text_area("Q. どんな場面で、相手とどう関わり、どう感じましたか？", key="w_t")
with tab3:
    st.write("**【計算】**\n時給1,200円で、1日6時間、月に20日間働きました。合計の給料はいくらになりますか？")
    st.session_state['c_t_val'] = st.text_area("Q. 計算式と答えを書いてください。", key="c_t")
with tab4:
    st.write("**【場面】**\n作業中に道具を壊してしまいました。しばらくして、上司（スタッフ）が戻ってきました。")
    st.session_state['m_t_val'] = st.text_area("Q. 戻ってきた上司へ、最初に何と言いますか？", key="m_t")

# ==========================================
# 4. 分析実行 & 結果表示
# ==========================================
st.divider()
if st.button("🚀 AI診断を開始（あなたの強みを発見する）", type="primary"):
    if not st.session_state['name']:
        st.error("プロフィール欄に「氏名」を入力してください。")
    else:
        with st.spinner("あなたの回答から「強み」を分析中..."):
            # デモ用スコア生成
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.1, "calculation": 1.5, "communication": 1.3}
            
            # JSON読み込みとマッチング
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    db_data = json.load(f)
                    st.session_state['job_matches'] = [{"job": j, "match_rate": 80.0} for j in db_data.get('jobs', [])]
                    st.session_state['evaluated'] = True
            else:
                st.error("job_database.json が見つかりません。")

if st.session_state['evaluated']:
    st.balloons()
    main_title, top_3 = get_strength_feedback(st.session_state['scores'])
    
    st.markdown(f"""
    <div style="background-color:#F0F8FF; padding:30px; border-radius:15px; border:3px solid #1E90FF; text-align:center;">
        <h2 style="color:#1E90FF; margin:0;">{st.session_state['name']} さんの分析結果</h2>
        <h1 style="font-size:2.8em; margin:15px 0;">✨ {main_title} ✨</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 📊 強みチャート")
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
        

    with col2:
        st.write("#### 🎯 適性の高いお仕事")
        df = pd.DataFrame([{'職種': m['job']['name'], '率': m['match_rate']} for m in st.session_state['job_matches'][:10]])
        fig = px.bar(df, x='率', y='職種', orientation='h', color='率', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

    st.info(f"**強みベスト3:** ①{top_3[0]}  ②{top_3[1]}  ③{top_3[2]}")
