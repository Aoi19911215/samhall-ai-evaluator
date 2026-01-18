import streamlit as st
import json
import os
from evaluator.text_analyzer import TextAnalyzer
from evaluator.scorer import SamhallScorer
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
def create_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='スキル評価'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])),
        showlegend=False
    )
    return fig

def create_job_match_chart(job_matches):
    # マッチング率上位をグラフ化
    df = pd.DataFrame(job_matches)
    fig = px.bar(df, x='match_rate', y='job_name', orientation='h',
                 title="職種マッチング率",
                 labels={'match_rate': 'マッチング率 (%)', 'job_name': '職種'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig
from utils.database import save_evaluation, load_evaluations

st.set_page_config(page_title="Samhall AI評価システム", layout="wide")

st.title("🎯 Samhall AI評価システム（24職種対応）")

st.markdown("""
### 📌 免責事項
本システムはSamhall（スウェーデン）の16項目評価の枠組みを参考にしていますが、
16項目の具体的内容は公式に公開されていないため、推測に基づいています。
正式な評価には、Samhall社への直接確認をお勧めします。
""")

with st.sidebar:
    st.header("📝 基本情報")
    name = st.text_input("氏名", value="")
    age = st.number_input("年齢", min_value=15, max_value=100, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    disability_type = st.text_input("障害種別", value="")

st.header("✍️ テキスト課題")

tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 コミュニケーション"])

text_responses = {}

with tab1:
    st.subheader("読解・理解力")
    text_responses['reading'] = st.text_area(
        "以下の文章を読んで、内容を簡単に説明してください：\n\n「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」",
        height=150
    )

with tab2:
    st.subheader("文章作成力")
    text_responses['writing'] = st.text_area(
        "あなたが最近経験した良いことについて、3〜5文で書いてください。",
        height=150
    )

with tab3:
    st.subheader("計算・論理力")
    text_responses['calculation'] = st.text_area(
        "時給1,200円で1日6時間、週5日働いた場合の月収（4週間）を計算してください。計算過程も書いてください。",
        height=150
    )

with tab4:
    st.subheader("コミュニケーション")
    text_responses['communication'] = st.text_area(
        "職場で困ったことがあった時、どのように周りの人に相談しますか？",
        height=150
    )

if st.button("🚀 AI評価を開始", type="primary"):
    if not name:
        st.error("氏名を入力してください")
    elif not any(text_responses.values()):
        st.error("少なくとも1つの課題に回答してください")
    else:
        with st.spinner("AI評価中...（10〜30秒かかります）"):
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
                
                st.success("✅ 評価完了！下記の結果をご確認ください。")
                
            except Exception as e:
                st.error(f"評価中にエラーが発生しました: {e}")

if 'evaluated' in st.session_state and st.session_state['evaluated']:
    st.header("📊 評価結果")
    
    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs(["📈 総合評価", "🔍 詳細分析", "💼 推奨職務（24職種）", "📄 レポート"])
    
    with res_tab1:
        st.subheader("総合スコア")
        scores = st.session_state['scores']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.plotly_chart(create_radar_chart(scores), use_container_width=True)
        
        with col2:
            st.markdown("#### スコア一覧")
            for skill, score in scores.items():
                if score >= 1.5:
                    level = "🟢 高い"
                elif score >= 0.6:
                    level = "🟡 良好"
                else:
                    level = "🔴 限定的"
                st.markdown(f"**{skill}**: {score:.2f} {level}")
    
    with res_tab2:
        st.subheader("カテゴリ別分析")
        
        with open('data/evaluation_criteria.json', 'r', encoding='utf-8') as f:
            criteria = json.load(f)
        
        for category, info in criteria['categories'].items():
            st.markdown(f"### {category}")
            st.caption(info['description'])
            
            category_scores = {skill: scores[skill] for skill in info['skills'] if skill in scores}
            avg_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0
            
            st.metric(label="カテゴリ平均", value=f"{avg_score:.2f}")
            
            for skill, score in category_scores.items():
                st.progress(score / 2.0, text=f"{skill}: {score:.2f}")
            
            st.divider()
    
    with res_tab3:
        st.subheader("推奨職務マッチング（24職種対応）")
        
        job_matches = st.session_state['job_matches']
        
        with open('data/job_database.json', 'r', encoding='utf-8') as f:
            job_db = json.load(f)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### フィルタ")
            
            all_categories = ["全て"] + list(job_db['job_categories'].values())
            selected_category = st.selectbox("職種カテゴリ", all_categories)
            
            min_match = st.slider("最低マッチング率 (%)", 0, 100, 50, 5)
        
        filtered_matches = job_matches
        
        if selected_category != "全て":
            category_key = [k for k, v in job_db['job_categories'].items() if v == selected_category][0]
            filtered_matches = [m for m in filtered_matches if m['job']['category'] == category_key]
        
        filtered_matches = [m for m in filtered_matches if m['match_rate'] >= min_match]
        
        with col2:
            if filtered_matches:
                st.markdown(f"#### マッチング上位職種（{len(filtered_matches)}件）")
                
                top_10 = filtered_matches[:10]
                
                for i, match in enumerate(top_10, 1):
                    job = match['job']
                    match_rate = match['match_rate']
                    
                    with st.expander(f"{i}. {job['name']} - {match_rate:.1f}% マッチ"):
                        st.markdown(f"**カテゴリ**: {job_db['job_categories'][job['category']]}")
                        st.markdown(f"**説明**: {job['description']}")
                        st.markdown(f"**想定給与**: {job['salary']}")
                        st.markdown(f"**マッチング率**: {match_rate:.1f}%")
                        st.markdown(f"**充足スキル**: {match['matched_skills']}/{match['total_skills']}")
                        
                        st.markdown("##### 必要スキルと評価")
                        for skill, req_score in job['required_scores'].items():
                            user_score = scores.get(skill, 1.0)
                            status = "✅" if user_score >= req_score else "⚠️"
                            st.markdown(f"{status} {skill}: 必要{req_score:.1f} / 評価{user_score:.2f}")
                        
                        st.markdown(f"**サポート体制**: {job['support']}")
            else:
                st.warning("条件に一致する職種がありません。フィルタを調整してください。")
        
        st.markdown("---")
        st.markdown("#### カテゴリ別集計")
        
        category_stats = {}
        for match in job_matches:
            cat = job_db['job_categories'][match['job']['category']]
            if cat not in category_stats:
                category_stats[cat] = {'count': 0, 'avg_match': 0}
            category_stats[cat]['count'] += 1
            category_stats[cat]['avg_match'] += match['match_rate']
        
        for cat in category_stats:
            category_stats[cat]['avg_match'] /= category_stats[cat]['count']
        
        col1, col2, col3 = st.columns(3)
        
        for i, (cat, stats) in enumerate(category_stats.items()):
            with [col1, col2, col3][i % 3]:
                st.metric(
                    label=cat,
                    value=f"{stats['count']}職種",
                    delta=f"平均 {stats['avg_match']:.1f}%"
                )
    
    with res_tab4:
        st.subheader("評価レポート")
        
        st.markdown(f"""
        ### 評価対象者情報
        - **氏名**: {name}
        - **年齢**: {age}
        - **性別**: {gender}
        - **障害種別**: {disability_type}
        
        ### 総合評価サマリー
        - **評価項目数**: 15項目
        - **平均スコア**: {sum(scores.values()) / len(scores):.2f}
        - **最高スコア**: {max(scores.values()):.2f} ({max(scores, key=scores.get)})
        - **最低スコア**: {min(scores.values()):.2f} ({min(scores, key=scores.get)})
        
        ### 推奨職種 Top 5
        """)
        
        for i, match in enumerate(job_matches[:5], 1):
            st.markdown(f"{i}. **{match['job']['name']}** - {match['match_rate']:.1f}% マッチ")
        
        if st.button("📥 レポートをダウンロード（JSON）"):
            report_data = {
                'name': name,
                'age': age,
                'gender': gender,
                'disability_type': disability_type,
                'scores': scores,
                'top_jobs': [
                    {
                        'name': m['job']['name'],
                        'match_rate': m['match_rate']
                    }
                    for m in job_matches[:10]
                ]
            }
            st.download_button(
                label="ダウンロード",
                data=json.dumps(report_data, ensure_ascii=False, indent=2),
                file_name=f"evaluation_{name}.json",
                mime="application/json"
            )

st.markdown("---")
st.caption("© 2024 Samhall AI評価システム（24職種対応版）")
