import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer

# ==========================================
# 1. グラフ作成・保存機能
# ==========================================
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='スキル評価'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False
    )
    return fig

def create_job_match_chart(job_matches):
    df = pd.DataFrame(job_matches)
    fig = px.bar(df, x='match_rate', y='job_name', orientation='h',
                 title="職種マッチング率",
                 labels={'match_rate': 'マッチング率 (%)', 'job_name': '職種'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

# ==========================================
# 2. 初期設定・説明文
# ==========================================
st.set_page_config(page_title="O-lys AI評価システム", layout="wide")

st.title("🎯 O-lys AI評価システム（24職種対応）")

st.markdown("""
### 📌 本システムについて
本アプリは、労働能力評価メソッド**「O-lys（オーリス）」**の指標に基づき、個人の「できること」を可視化するシミュレーターです。

* **ヒントを見つける**: 15の評価項目から、24職種とのマッチングを予測します。
* **参考指標**: 独自開発のテストモデルです。支援の方向性を検討するための参考としてご活用ください。

### 🔒 安心・安全への取り組み
* **匿名で分析**: 氏名などの個人情報は分析に使用しません。
* **回答文のみを判定**: 課題の「回答内容」だけを安全にスコア化します。
* **データの保護**: 入力内容が外部のAI学習に利用されることはありません。
""")

# ==========================================
# 3. サイドバー（基本情報入力）
# ==========================================
with  st.sidebar:
    st.header("📝 基本情報")
    name = st.text_input("氏名", value="")
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    
    st.divider()
    
    st.header("🏃 身体的・環境条件")
    st.caption("マッチングの精度を高めるために使用します")
    
    physical_mobility = st.selectbox(
        "移動・歩行の状況", 
        ["制限なし（階段・長距離OK）", "長距離は困難", "車椅子利用", "歩行補助が必要"],
        key="phys_mob"
    )
    
    physical_lifting = st.selectbox(
        "持ち上げられる重さ", 
        ["10kg以上（重労働OK）", "5kg程度（軽作業）", "重いものは不可"],
        key="phys_lift"
    )


    # AIへ送るデータに身体情報も混ぜる
    text_responses["calculation"] = f"【計算回答】:{c_txt} (自己評価:{c_sel})"
    text_responses["physical_info"] = f"【身体条件】移動:{physical_mobility} / 重量物:{physical_lifting}"
# ==========================================
# 4. ワーク回答セクション（選択肢＋記述のハイブリッド）
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

text_responses = {}

with  tab1:
    st.subheader("読解・理解力")
    st.info("以下の文章を読んで、あとの設問に答えてください。")
    st.write("""
    **【文章】**
    「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」
    """)
    
    r_sel = st.selectbox("文章の内容はどのくらい理解できましたか？", 
                           ["-- 選択してください --", "完璧に理解した", "だいたい理解した", "少し難しい", "全くわからなかった"], key="r_s")
    
    r_txt = st.text_area("【記述】この文章は、働くことには「お金」以外にどのような意味があると言っていますか？", 
                         placeholder="例：社会との関わりや、自分の力を出すこと、など。", 
                         key="r_t")
    
    text_responses['reading'] = f"自己評価:{r_sel} / 回答:{r_txt}"

with tab2:
    st.subheader("文章作成力")
    w_sel = st.selectbox("自分の考えを文章にするのは得意ですか？", 
                           ["得意", "普通", "少し苦手", "非常に苦手"], key="w_s")
    w_txt = st.text_area("あなたが最近経験した「良いこと」について教えてください。", placeholder="3〜5文程度で記入してください。", key="w_t")
    text_responses["writing"] = f"自己評価:{w_sel} / 回答:{w_txt}"

with tab3:
    st.subheader("🔢 計算・論理力")
    st.info("【実務課題：給与の計算】")
    st.write("""
    **課題：**
    時給1,200円で、1日6時間、週に5日間働きました。
    この働き方で4週間（合計20日間）働いた場合、給与の合計はいくらになりますか？
    """)
    
    c_sel = st.radio(
        "計算に自信はありますか？", 
        ["迷わず計算できた", "少し時間がかかった", "計算機がほしい", "難しかった"], 
        key="c_s_new"
    )
    
    c_txt = st.text_area(
        "答えと、その答えを出した計算の順序を書いてください。", 
        placeholder="例：〇〇円。計算式：時給 × 時間 × 日数 = 〇〇", 
        key="c_t_new"
    )
    
