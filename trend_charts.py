import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional, List, Dict


COLOR_PALETTE = [
    '#2E86AB', '#A23B72', '#F18F01', '#C73E1D',
    '#3B1F2B', '#6A994E', '#577590', '#F94144'
]


def create_line_chart(
    df: pd.DataFrame,
    time_col: str = '时间',
    value_col: str = '销售额',
    group_col: Optional[str] = None,
    title: str = '销售趋势折线图'
) -> go.Figure:
    fig = go.Figure()

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        for i, group in enumerate(groups):
            group_df = df[df[group_col] == group].sort_values(time_col)
            color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
            fig.add_trace(go.Scatter(
                x=group_df[time_col],
                y=group_df[value_col],
                mode='lines+markers',
                name=str(group),
                line=dict(color=color, width=2),
                marker=dict(color=color, size=6),
                hovertemplate=f'<b>{group}</b><br>时间: %{{x}}<br>销售额: %{{y:,.0f}}<extra></extra>'
            ))
    else:
        sorted_df = df.sort_values(time_col)
        fig.add_trace(go.Scatter(
            x=sorted_df[time_col],
            y=sorted_df[value_col],
            mode='lines+markers',
            name='销售额',
            line=dict(color='#2E86AB', width=3),
            marker=dict(color='#2E86AB', size=8),
            hovertemplate='时间: %{x}<br>销售额: %{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18)),
        xaxis_title='时间',
        yaxis_title='销售额',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=80, b=60),
        font=dict(size=12)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')

    return fig


def create_area_chart(
    df: pd.DataFrame,
    time_col: str = '时间',
    value_col: str = '销售额',
    group_col: Optional[str] = None,
    title: str = '销售趋势面积图'
) -> go.Figure:
    fig = go.Figure()

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        for i, group in enumerate(groups):
            group_df = df[df[group_col] == group].sort_values(time_col)
            color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
            fig.add_trace(go.Scatter(
                x=group_df[time_col],
                y=group_df[value_col],
                mode='lines',
                name=str(group),
                fill='tonexty' if i == 0 else 'tonexty',
                line=dict(color=color, width=2),
                fillcolor=f'rgba{tuple(int(color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4)) + (0.3,)}',
                hovertemplate=f'<b>{group}</b><br>时间: %{{x}}<br>销售额: %{{y:,.0f}}<extra></extra>'
            ))
    else:
        sorted_df = df.sort_values(time_col)
        fig.add_trace(go.Scatter(
            x=sorted_df[time_col],
            y=sorted_df[value_col],
            mode='lines',
            name='销售额',
            fill='tozeroy',
            line=dict(color='#2E86AB', width=3),
            fillcolor='rgba(46, 134, 171, 0.3)',
            hovertemplate='时间: %{x}<br>销售额: %{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18)),
        xaxis_title='时间',
        yaxis_title='销售额',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=80, b=60),
        font=dict(size=12)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')

    return fig


def create_combined_chart(
    df: pd.DataFrame,
    time_col: str = '时间',
    value_col: str = '销售额',
    group_col: Optional[str] = None,
    title: str = '销售趋势组合图（柱状+折线）'
) -> go.Figure:
    fig = go.Figure()

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        for i, group in enumerate(groups):
            group_df = df[df[group_col] == group].sort_values(time_col)
            color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
            fig.add_trace(go.Bar(
                x=group_df[time_col],
                y=group_df[value_col],
                name=f'{group}(柱状)',
                marker_color=color,
                opacity=0.7,
                hovertemplate=f'<b>{group}</b><br>时间: %{{x}}<br>销售额: %{{y:,.0f}}<extra></extra>'
            ))

        for i, group in enumerate(groups):
            group_df = df[df[group_col] == group].sort_values(time_col)
            color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
            fig.add_trace(go.Scatter(
                x=group_df[time_col],
                y=group_df[value_col],
                mode='lines+markers',
                name=f'{group}(趋势)',
                line=dict(color=color, width=2, dash='dash'),
                marker=dict(color=color, size=6),
                yaxis='y1',
                hovertemplate=f'<b>{group} 趋势</b><br>时间: %{{x}}<br>销售额: %{{y:,.0f}}<extra></extra>'
            ))
    else:
        sorted_df = df.sort_values(time_col)
        fig.add_trace(go.Bar(
            x=sorted_df[time_col],
            y=sorted_df[value_col],
            name='销售额(柱状)',
            marker_color='#2E86AB',
            opacity=0.7,
            hovertemplate='时间: %{x}<br>销售额: %{y:,.0f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=sorted_df[time_col],
            y=sorted_df[value_col],
            mode='lines+markers',
            name='销售额(趋势)',
            line=dict(color='#F18F01', width=3),
            marker=dict(color='#F18F01', size=8),
            hovertemplate='时间: %{x}<br>销售额: %{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18)),
        xaxis_title='时间',
        yaxis_title='销售额',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=100, b=60),
        font=dict(size=12)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')

    return fig


def create_moving_average_chart(
    df: pd.DataFrame,
    time_col: str = '时间',
    value_col: str = '销售额',
    window: int = 3,
    title: str = '销售额及移动平均趋势'
) -> go.Figure:
    sorted_df = df.sort_values(time_col).copy()
    sorted_df['移动平均'] = sorted_df[value_col].rolling(window=window, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=sorted_df[time_col],
        y=sorted_df[value_col],
        name='实际销售额',
        marker_color='#2E86AB',
        opacity=0.6,
        hovertemplate='时间: %{x}<br>销售额: %{y:,.0f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=sorted_df[time_col],
        y=sorted_df['移动平均'],
        mode='lines',
        name=f'{window}期移动平均',
        line=dict(color='#F18F01', width=3),
        hovertemplate=f'{window}期移动平均: %{{y:,.0f}}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18)),
        xaxis_title='时间',
        yaxis_title='销售额',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=80, b=60),
        font=dict(size=12)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')

    return fig
