import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import calendar
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple


COLOR_PALETTE = [
    '#2E86AB', '#A23B72', '#F18F01', '#C73E1D',
    '#3B1F2B', '#6A994E', '#577590', '#F94144'
]

WEEKDAY_NAMES = ['一', '二', '三', '四', '五', '六', '日']


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
            group_df = df[df[group_col] == group]
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
        sorted_df = df
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
            group_df = df[df[group_col] == group]
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
        sorted_df = df
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
            group_df = df[df[group_col] == group]
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
            group_df = df[df[group_col] == group]
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
        sorted_df = df
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
    sorted_df = df.copy()
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


def create_activity_calendar(
    activity_data: Dict[str, Any],
    year: int,
    month: int,
    highlight_date: Optional[str] = None
) -> go.Figure:
    fig = go.Figure()

    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    weeks = []
    current_week = []
    for i, d in enumerate(month_days):
        current_week.append(d)
        if (i + 1) % 7 == 0:
            weeks.append(current_week)
            current_week = []
    if current_week:
        weeks.append(current_week)

    n_rows = len(weeks)
    n_cols = 7

    date_activity_map = activity_data.get('date_activity_map', {}) if activity_data else {}
    activity_colors = activity_data.get('activity_colors', {}) if activity_data else {}

    for row_idx, week in enumerate(weeks):
        for col_idx, day_date in enumerate(week):
            is_current_month = day_date.month == month and day_date.year == year
            date_str = day_date.strftime('%Y-%m-%d')

            if is_current_month:
                activities = date_activity_map.get(date_str, [])
            else:
                activities = []

            if activities:
                if len(activities) == 1:
                    bg_color = activity_colors.get(activities[0], '#2E86AB')
                else:
                    bg_color = '#F18F01'
                text_color = 'white'
                opacity = 0.85
            else:
                bg_color = '#f8f9fa' if is_current_month else '#ffffff'
                text_color = '#999' if not is_current_month else '#333'
                opacity = 1.0

            is_highlight = (highlight_date == date_str)

            border_color = '#2E86AB' if is_highlight else ('#e0e0e0' if is_current_month else '#f0f0f0')
            border_width = 3 if is_highlight else 1

            hover_text_parts = [f'日期: {date_str}']
            if activities:
                hover_text_parts.append('活动:')
                for act in activities:
                    hover_text_parts.append(f'  • {act}')
            else:
                hover_text_parts.append('无促销活动')
            hover_text = '<br>'.join(hover_text_parts)

            fig.add_trace(go.Scatter(
                x=[col_idx],
                y=[row_idx],
                mode='markers+text',
                marker=dict(
                    symbol='square',
                    size=42,
                    color=bg_color,
                    opacity=opacity,
                    line=dict(color=border_color, width=border_width)
                ),
                text=[str(day_date.day)],
                textfont=dict(color=text_color, size=13, family='Arial, sans-serif'),
                textposition='middle center',
                hoverinfo='text',
                hovertext=hover_text,
                customdata=[date_str],
                showlegend=False,
                name=''
            ))

    for col_idx, wd_name in enumerate(WEEKDAY_NAMES):
        fig.add_trace(go.Scatter(
            x=[col_idx],
            y=[-0.6],
            mode='text',
            text=[wd_name],
            textfont=dict(color='#666', size=13, family='Arial, sans-serif'),
            textposition='middle center',
            hoverinfo='skip',
            showlegend=False,
            name=''
        ))

    fig.update_xaxes(
        range=[-0.6, n_cols - 0.4],
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
        fixedrange=True
    )
    fig.update_yaxes(
        range=[n_rows - 0.4, -1.1],
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
        autorange='reversed',
        fixedrange=True
    )

    month_title = f'{year}年{month}月'
    fig.update_layout(
        title=dict(
            text=f'📅 活动日历 — {month_title}',
            x=0.5,
            xanchor='center',
            font=dict(size=17, color='#333')
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=420,
        height=300 + n_rows * 10,
        margin=dict(l=15, r=15, t=60, b=15),
        dragmode=False,
        clickmode='event+select'
    )

    return fig


def create_calendar_legend(activity_data: Dict[str, Any]) -> List[Dict[str, str]]:
    legend_items = []
    if not activity_data or not activity_data.get('available', False):
        return legend_items

    activity_colors = activity_data.get('activity_colors', {})
    activity_dates = activity_data.get('activity_dates', {})

    for activity, color in activity_colors.items():
        days_count = len(activity_dates.get(activity, []))
        legend_items.append({
            'name': activity,
            'color': color,
            'days': days_count
        })

    return legend_items
