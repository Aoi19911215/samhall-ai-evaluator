import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# --- モジュール読み込み（エラー回避用） ---
try:
    from evaluator.text_analyzer import TextAnalyzer
    from evaluator.scorer import SamhallScorer
except:
    # ローカル環境などでファイルがない場合のためのダミー
    class TextAnalyzer:
        def analyze(self, x): return {"reading": 1, "writing": 1, "calculation": 1, "communication": 1}
    class SamhallScorer:
        @staticmethod
        def calculate_final_scores(x): return x
        @staticmethod
        def match_jobs(s, db): return [{"job": {"name": "軽作業"}, "match_rate": 80}]

# ==========================================
# 1. グラフ・フィードバック関数
# ==========================================
def get_feedback_content(scores):
    # スコアが空またはALL 0の場合のデフォルト
    if not scores or sum(scores.values()) == 0:
        scores = {"reading": 0.5, "writing": 0.5, "calculation": 0.5, "communication": 0.5}
    
    labels = {"reading": "理解力", "writing": "対人表現力", "calculation": "正確性", "communication": "つながる力"}
    sorted_s = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key = sorted_s[0][0]
    
    titles = {
        "calculation": "確かな正確さを持つ実務の星",
        "communication": "周囲を安心させる相談の達人",
        "writing": "人の気持ちを大切にする表現者",
        "reading": "本質を深く捉える理解のリーダー"
    }
    title = titles.get(top_key, "期待のプロフェッショナル")
    top_3 = [labels.get(k, k) for k, v in sorted_s[:3]]
    return title, top_3

def create_radar_chart(scores):
    categories = ["理解力", "対人表現力", "正確性", "つながる力"]
    # グラフが消えないよう最小値 0.1 を保証
    values = [max(0.1, scores.get(k, 0.1)) for k in ["reading", "writing", "calculation", "communication"]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='あなたの強み'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False
    )
    return fig

# ==========================================
# 2. 初期設定
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

# セッションの初期化
for key in ['name', 'r_t_val', 'w_t_val', 'c_t_val', 'm_t_val', 'scores', 'job_matches']:
    if key not in st.session_state: st.session_state[key] = "" if 'val' in key else {}

if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False

st.title("🎯 O-lys AI評価システム")

# ==========================================
# 3. 入力セクション（中略：サイドバー等は維持）
# ==========================================
with st.sidebar:
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    st.session_state['age'] = st.number_input("年齢", 0, 100, 25)
    st.session_state['disability'] = st.text_input("障害特性・配慮事項")

st.header("✍️ ワーク・シミュレーション")
tab1, tab2, tab3, tab4 = st.tabs(["📖 理解", "✏️ 関わり", "🔢 数字", "💬 相談"])
with tab1: st.session_state['r_t_val'] = st.text_area("働く意味", key="r_t")
with tab2: st.session_state['w_t_val'] = st.text_area("良かったこと", key="w_t")
with tab3: st.session_state['c_t_val'] = st.text_area("計算", key="c_t")
with tab4: st.session_state['m_t_val'] = st.text_area("相談のセリフ", key="m_t")

# ==========================================
# 4. 実行ボタン
# ==========================================
if st.button("🚀 AI診断を開始", type="primary"):
    if not st.session_state['name']:
        st.error("氏名を入力してください")
    else:
        with st.spinner("分析中..."):
            # ダミーデータでも動くように try-except
            try:
                analyzer = TextAnalyzer()
                raw = analyzer.analyze({"reading": st.session_state['r_t_val'], "writing": st.session_state['w_t_val'], "calculation": st.session_state['c_t_val'], "communication": st.session_state['m_t_val']})
                st.session_state['scores'] = SamhallScorer.calculate_final_scores(raw)
                
                # 職種DBの読み込み
                db_path = 'data/job_database.json'
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        db = json.load(f)
                else:
                    db = [] # 空でも動くように
                
                st.session_state['job_matches'] = SamhallScorer.match_jobs(st.session_state['scores'], db)
                st.session_state['evaluated'] = True
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# ==========================================
# 5. 【重要】表示ロジックの修正
# ==========================================
if st.session_state['evaluated']:
    # 結果を取得
    scores = st.session_state['scores']
    job_matches = st.session_state['job_matches']
    title, top_3 = get_feedback_content(scores)

    st.balloons()
    st.success(f"### {st.session_state['name']} さんの分析が完了しました！")
    
    # グラフと職種を横並びに表示
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 📊 あなたの強みチャート")
        st.plotly_chart(create_radar_chart(scores), use_container_width=True)
    
    with col2:
        st.write("#### 🎯 マッチするお仕事")
        if job_matches:
            # グラフ化
            df = pd.DataFrame([{'職種': m['job']['name'], '率': m['match_rate']} for m in job_matches[:5]])
            fig = px.bar(df, x='率', y='職種', orientation='h', range_x=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("マッチする職種が見つかりませんでした。回答をもう少し詳しく書いてみてください。")

    st.divider()
    st.write(f"### 🤖 AIアドバイス: **{title}**")
    c1, c2, c3 = st.columns(3)
    c1.info(f"💪 **{top_3[0]}**")
    c2.info(f"✨ **{top_3[1]}**")
    c3.info(f"🌱 **{top_3[2]}**")
    
    st.write(f"あなたの「{top_3[0]}」は素晴らしい強みです。この力を活かせる職場を一緒に探しましょう。")
