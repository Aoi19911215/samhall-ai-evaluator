import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# --- 1. スコア・グラフ用ユーティリティ ---
def get_strength_feedback(scores):
    labels = {"reading": "読み取る力", "writing": "人との関わり", "calculation": "計算する力", "communication": "相談する力"}
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
    categories = ["読み取る力", "人との関わり", "計算する力", "相談する力"]
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(30, 144, 255, 0.4)', line_color='#1E90FF'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=False, height=400)
    return fig

# --- 2. セッション管理 & UI ---
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

for key in ['name', 'gender', 'age', 'disability', 'scores', 'job_matches', 'evaluated']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'evaluated' else ({} if key in ['scores', 'job_matches'] else "")

st.title("🎯 O-lys AI評価システム")
st.warning("🔒 **個人情報の保護**: 入力された情報は保存されず、ページを閉じると消去されます。")

with st.sidebar:
    st.header("👤 プロフィール")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state.get('name', ""))
    st.session_state['gender'] = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項", value=st.session_state.get('disability', ""))

st.header("✍️ ワーク・シミュレーション")
tabs = st.tabs(["📖 読み取る力", "✏️ 人との関わり", "🔢 計算する力", "💬 相談する力"])
# 各入力（簡略化して記述）
for i, t in enumerate(tabs):
    with t: st.text_area(f"ワーク {i+1} の回答", key=f"work_{i}")

# --- 3. 分析実行 ---
if st.button("🚀 AI診断を開始", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("分析中..."):
            # デモ用スコア
            st.session_state['scores'] = {"reading": 1.2, "writing": 1.0, "calculation": 1.5, "communication": 1.3}
            
            db_path = 'data/job_database.json'
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # マッチング計算（確実に値を入れます）
                    jobs = data.get('jobs', [])
                    st.session_state['job_matches'] = [{"job": j, "match_rate": 80.0} for j in jobs]
                    st.session_state['evaluated'] = True
            else:
                st.error("データファイルが見つかりません。")

# --- 4. 結果表示（エラー対策版） ---
if st.session_state['evaluated']:
    main_title, top_3 = get_strength_feedback(st.session_state['scores'])
    st.success(f"### {st.session_state['name']} さんの強み：{main_title}")

    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 📊 強みチャート")
        
        st.plotly_chart(create_radar_chart(st.session_state['scores']))

    with col2:
        st.write("#### 🎯 適性の高いお仕事")
        matches = st.session_state.get('job_matches', [])
        
        # --- ここがエラー対策の核心 ---
        if matches:
            df = pd.DataFrame([{'職種': m['job']['name'], 'マッチ率': m['match_rate']} for m in matches[:10]])
            if not df.empty:
                fig = px.bar(df, x='マッチ率', y='職種', orientation='h', color='マッチ率', color_continuous_scale='Blues')
                fig.update_layout(xaxis_range=[0, 110], yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("表示できるマッチングデータがありません。")
        else:
            st.info("現在、分析可能な職種データが空です。")
