import plotly.graph_objects as go

def create_radar_chart(scores, title="スキル評価レーダーチャート"):
    """
    スキル評価のレーダーチャートを作成
    
    Args:
        scores (dict): スキル名とスコアの辞書
        title (str): チャートのタイトル
    
    Returns:
        plotly.graph_objects.Figure: レーダーチャート
    """
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='評価スコア'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 2]
            )
        ),
        showlegend=True,
        title=title
    )
    
    return fig

def create_job_match_chart(matches, top_n=10):
    """
    職務マッチング率の横棒グラフを作成
    
    Args:
        matches (list): 職務マッチング情報のリスト
        top_n (int): 表示する上位職種の数
    
    Returns:
        plotly.graph_objects.Figure: 横棒グラフ
    """
    top_matches = matches[:top_n]
    
    job_names = [m['job']['name'] for m in top_matches]
    match_rates = [m['match_rate'] for m in top_matches]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=job_names,
        x=match_rates,
        orientation='h',
        marker=dict(
            color=match_rates,
            colorscale='Viridis'
        )
    ))
    
    fig.update_layout(
        title=f"職務マッチング率 Top {top_n}",
        xaxis_title="マッチング率 (%)",
        yaxis_title="職種",
        height=500
    )
    
    return fig
