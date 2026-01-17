import plotly.graph_objects as go

def create_radar_chart(scores, title="スキル評価レーダーチャート"):
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
