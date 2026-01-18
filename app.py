# ==========================================
# 4. ワーク回答セクション（入力保持機能付き）
# ==========================================
st.header("✍️ テキスト課題")
tab1, tab2, tab3, tab4 = st.tabs(["📖 読解・理解", "✏️ 文章作成", "🔢 計算・論理", "💬 報告・相談"])

with tab1:
    st.subheader("読解・理解力")
    st.write("""
    **【文章】**
    「働くことは、収入を得るだけでなく、社会とつながり、自分の能力を発揮する場でもあります。」
    """)
    r_sel = st.selectbox("理解度は？", ["-- 選択 --", "完璧", "だいたい", "難しい", "不明"], key="r_s")
    # 入力値をセッションに保存し、リロードしても消えないように設定
    st.session_state['r_t_val'] = st.text_area("働くことの「お金」以外の意味は？", value=st.session_state['r_t_val'], key="r_t")
    text_responses['reading'] = f"自己評価:{r_sel} / 回答:{st.session_state['r_t_val']}"

with tab2:
    st.subheader("文章作成力")
    w_sel = st.selectbox("文章は得意？", ["得意", "普通", "苦手"], key="w_s")
    st.session_state['w_t_val'] = st.text_area("あなたが最近経験した「良いこと」について教えてください。", value=st.session_state['w_t_val'], key="w_t")
    text_responses["writing"] = f"自己評価:{w_sel} / 回答:{st.session_state['w_t_val']}"

with tab3:
    st.subheader("🔢 計算・論理力")
    st.write("""
    **課題：**
    時給1,200円で、1日6時間、週に5日間働きました。
    この働き方で4週間（合計20日間）働いた場合、給与の合計はいくらになりますか？
    """)
    c_sel = st.radio("自信は？", ["迷わず", "少し時間", "計算機希望", "困難"], key="c_s_new")
    st.session_state['c_t_val'] = st.text_area("答えと計算式を書いてください。", value=st.session_state['c_t_val'], key="c_t_new")
    text_responses["calculation"] = f"自己評価:{c_sel} / 回答:{st.session_state['c_t_val']}"

with tab4:
    st.subheader("💬 報告・相談")
    st.write("""
    **場面：**
    作業中に道具を壊してしまいましたが、周りに上司がいません。
    """)
    m_sel = st.selectbox("どう動く？", ["待つ", "同僚に相談", "自分で直す", "放置"], key="m_s")
    st.session_state['m_t_val'] = st.text_area("戻った上司へ何と言いますか？", value=st.session_state['m_t_val'], key="m_t")
    text_responses["communication"] = f"判断:{m_sel} / 発言:{st.session_state['m_t_val']}"

# ==========================================
# 5. 評価ボタンと実行
# ==========================================
st.divider()

if st.button("🚀 AI評価を開始", type="primary"):
    if not st.session_state.get('name'):
        st.error("左側のサイドバーで「氏名」を入力してください")
    else:
        with st.spinner("AI分析中..."):
            try:
                # 分析とマッチングの実行
                analyzer = TextAnalyzer()
                text_scores = analyzer.analyze(text_responses)
                final_scores = SamhallScorer.calculate_final_scores(text_scores)
                
                with open('data/job_database.json', 'r', encoding='utf-8') as f:
                    job_db = json.load(f)
                
                job_matches = SamhallScorer.match_jobs(final_scores, job_db)
                
                # 結果を保存
                st.session_state['scores'] = final_scores
                st.session_state['job_matches'] = job_matches
                st.session_state['evaluated'] = True
                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {
