import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. グラフ作成機能
# ==========================================
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False,
        title="📊 スキルバランス"
    )
    return fig

def create_job_match_chart(job_matches):
    if not job_matches:
        return go.Figure().update_layout(title="マッチするデータがありません")
    
    chart_data = []
    for m in job_matches:
        if isinstance(m, dict) and 'job' in m:
            chart_data.append({
                'job_name': m['job'].get('name', '不明な職種'),
                'match_rate': m.get('match_rate', 0)
            })
    
    df = pd.DataFrame(chart_data)
    if df.empty:
        return go.Figure().update_layout(title="表示できるデータがありません")

    df = df.sort_values('match_rate', ascending=True)

    fig = px.bar(
        df, 
        x='match_rate', 
        y='job_name', 
        orientation='h', 
        title="🎯 あなたにマッチする職種 Top 10",
        color='match_rate',
        color_continuous_scale='Blues',
        text='match_rate',
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        xaxis_range=[0, 115],
        showlegend=False,
        coloraxis_showscale=False,
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# ==========================================
# 2. 初期設定・セッション状態の初期化
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")
st.title("🎯 O-lys AI評価システム")

# 各入力値を保持するための初期化（タブ移動しても消えないように設定）
if 'name' not in st.session_state: st.session_state['name'] = ""
if 'r_t_val' not in st.session_state: st.session_state['r_t_val'] = ""
if 'w_t_val' not in st.session_state: st.session_state['w_t_val'] = ""
if 'c_t_val' not in st.session_state: st.session_state['c_t_val'] = ""
if 'm_t_val' not in st.session_state: st.session_state['m_t_val'] = ""
if 'evaluated' not in st.session_state: st.session_state['evaluated'] = False
if 'scores' not in st.session_state: st.session_state['scores'] = {}
if 'job_matches' not in st.session_state: st.session_state['job_matches'] = []

text_responses = {}

# ==========================================
# 3. サイドバー（基本情報・身体力・環境条件）
# ==========================================
with st.sidebar:
    st.header("📝 基本情報")
    st.session_state['name'] = st.text_input("氏名", value=st.session_state['name'])
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability_type = st.text_input("障害種別", value="", placeholder="例：精神障害など")
    
    st.divider()
    st.header("🏃 身体力・環境条件")
    physical_mobility = st.selectbox("移動・歩行の状況", ["制限なし（階段・長距離OK）", "長距離は困難", "車椅子利用", "歩行補助が必要"], key="phys_mob")
    physical_lifting = st.selectbox("持ち上げられる重さ", ["10kg以上（重労働OK）", "5kg程度（軽作業）", "重いものは不可"], key="phys_lift")
    env_options = ["騒音", "人混み", "高所", "屋外（暑さ・寒さ）", "強い光", "刃物・危険物", "その他"]
    env_preference = st.multiselect("避けるべき環境（配慮事項）", options=env_options, key="env_pref")
    
    other_env_text = ""
    if "その他" in env_preference:
        other_env_text = st.text_input("具体的な配慮事項を入力してください")

env_list = [item for item in env_preference if item != "その他"]
if other_env_text: env_list.append(other_env_text)

# プロフィール情報を集約
text_responses["user_profile"] = f"【基本】{age}歳/{gender} 【障害】:{disability_type}"
text_responses["environment_info"] = f"【避けるべき環境】:{', '.join(env_list) if env_list else '特になし'}"
text_responses["physical_info"] = f"【身体】移動:{physical_mobility} / 重量物:{physical_lifting}"

# ==========================================
# 4. ワーク回答セクション（入力保持機能）
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

with tab1:
    st.subheader("読解・理解力")
    st.write("**【文章】**\n「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」")
    r_sel = st.selectbox("理解度は？", ["-- 選択 --", "完璧", "だいたい", "難しい", "不明"], key="r_s")
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は？", value=st.session_state['r_t_val'], key="r_t")
    text_responses['reading'] = f"自己評価:{r_sel} / 回答:{st.session_state['r_t_val']}"

with tab2:
    st.subheader("文章作成力")
    w_sel = st.selectbox("文章は得意？", ["得意", "普通", "苦手"], key="w_s")
    st.session_state['w_t_val'] = st.text_area("あなたが最近経験した「良いこと」について教えてください。", value=st.session_state['w_t_val'], key="w_t")
    text_responses["writing"] = f"自己評価:{w_sel} / 回答:{st.session_state['w_t_val']}"

with tab3:
    st.subheader("🔢 計算・論理力")
    st.write("**課題：**\n時給1,200円で、1日6時間、週に5日間働きました。合計20日間の給与は？")
    c_sel = st.radio("自信は？", ["迷わず", "少し時間", "計算機希望", "困難"], key="c_s_new")
    st.session_state['c_t_val'] = st.text_area("答えと計算式を書いてください。", value=st.session_state['c_t_val'], key="c_t_new")
    text_responses["calculation"] = f"自己評価:{c_sel} / 回答:{st.session_state['c_t_val']}"

with tab4:
    st.subheader("💬 報告・相談")
    st.write("**場面：**\n作業中に道具を壊してしまいましたが、周りに上司がいません。")
    m_sel = st.selectbox("どう動く？", ["待つ", "同僚に相談", "自分で直す", "放置"], key="m_s")
    st.session_state['m_t_val'] = st.text_area("戻った上司へ何と言いますか？", value=st.session_state['m_t_val'], key="m_t")
    text_responses["communication"] = f"判断:{m_sel} / 発言:{st.session_state['m_t_val']}"

# ==========================================
# 5. 評価ボタンと実行処理
# ==========================================
st.divider()

if st.button("🚀 AI評価を開始", type="primary"):
    if not st.session_state['name']:
        st.error("左側のサイドバーで「氏名」を入力してください")
    else:
        with st.spinner("AI分析中..."):
            try:
                analyzer = TextAnalyzer()
                text_scores = analyzer.analyze(text_responses)
                final_scores = SamhallScorer.calculate_final_scores(text_scores)
                
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                
                job_matches = SamhallScorer.match_jobs(final_scores, job_db)
                
                st.session_state['scores'] = final_scores
                st.session_state['job_matches'] = job_matches
                st.session_state['evaluated'] = True
                st.rerun()
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# ==========================================
# 6. 結果表示・AIフィードバック
# ==========================================
if st.session_state.get('evaluated'):
    st.success(f"✨ {st.session_state['name']} さんの分析が完了しました！")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(create_radar_chart(st.session_state['scores']), use_container_width=True)
    with col2:
        st.plotly_chart(create_job_match_chart(st.session_state['job_matches'][:10]), use_container_width=True)

    st.divider()
    st.subheader("🤖 AIキャリア・フィードバック")
    
    scores = st.session_state.get('scores', {})
    job_matches = st.session_state.get('job_matches', [])
    
    with st.container():
        st.markdown(f"### 🌟 {st.session_state['name']} さんの「強み」と「可能性」")
        
        # 強みバッジ（1.5以上）
        strengths = [skill for skill, val in scores.items() if isinstance(val, (int, float)) and val >= 1.5]
        if strengths:
            cols = st.columns(min(len(strengths), 4))
            for i, s in enumerate(strengths[:4]):
                cols[i].info(f"**{s}**")
        
        # マッチング職種の安全な表示
        if job_matches:
            top_1 = job_matches[0]['job'].get('name', '適性の高い業務')
            top_2 = job_matches[1]['job'].get('name', '関連業務') if len(job_matches) > 1 else "その他の業務"
            
            st.markdown(f"""
            **【AI分析コメント】**
            診断結果から、{st.session_state['name']}さんは非常に誠実な業務遂行能力をお持ちであることが分かりました。
            
            特にマッチ率が高かった**「{top_1}」**や**「{top_2}」**は、
            あなたの現在のスキルセットを活かしやすい環境です。

            **【今後のアドバイス】**
            今の回答に基づくと、これらの職種で高い適合性が期待できます。
            避けるべき環境条件を考慮しても、自信を持って取り組める可能性が高いです。次の一歩を検討してみてください。
            """)
        else:
            st.info("さらに詳しく診断するために、各課題の回答をもっと書き込んでみてください。")
