if __name__ == '__main__':
    app.run(debug=True, port=4050)  # 修改这里的 8050 为您想要的端口号import dashif __name__ == '__main__':
    app.run(debug=True, port=4050)  # 修改这里的 8050 为您想要的端口号
from dash import html, dcc
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

mock_data = {
    '期间': ['促销前', '促销中', '促销后', '非促销期 1', '非促销期 2', '非促销期 3'],
    '销售额 (万元)': [120, 380, 150, 110, 115, 105],
    '类型': ['促销期间', '促销期间', '促销期间', '非促销期间', '非促销期间', '非促销期间']
}

df = pd.DataFrame(mock_data)

colors = ['#2E86AB' if t == '促销期间' else '#A23B72' for t in df['类型']]

fig = px.bar(
    df,
    x='期间',
    y='销售额 (万元)',
    color='类型',
    color_discrete_map={
        '促销期间': '#2E86AB',
        '非促销期间': '#A23B72'
    },
    title='促销期间与非促销期间销售对比',
    labels={'期间': '期间', '销售额 (万元)': '销售额 (万元)'},
    text='销售额 (万元)',
)

fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
fig.update_layout(
    showlegend=True,
    legend_title='期间类型',
    plot_bgcolor='white',
    font=dict(size=12),
    title_x=0.5,
)

app.layout = html.Div([
    html.H1(
        '促销活动分析页面',
        style={
            'textAlign': 'center',
            'color': '#2E86AB',
            'marginBottom': '30px',
            'fontFamily': 'Arial, sans-serif'
        }
    ),
    
    html.Div([
        dcc.Graph(figure=fig)
    ], style={
        'backgroundColor': 'white',
        'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'padding': '20px',
        'margin': '20px'
    }),
    
    html.Div([
        html.H3('关键指标', style={'color': '#333', 'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.H4('促销期间平均销售额', style={'color': '#666', 'fontSize': '14px'}),
                html.P('216.7 万元', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#2E86AB'})
            ], style={'textAlign': 'center', 'padding': '20px'}),
            
            html.Div([
                html.H4('非促销期间平均销售额', style={'color': '#666', 'fontSize': '14px'}),
                html.P('110.0 万元', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#A23B72'})
            ], style={'textAlign': 'center', 'padding': '20px'}),
            
            html.Div([
                html.H4('销售提升率', style={'color': '#666', 'fontSize': '14px'}),
                html.P('97.0%', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#F18F01'})
            ], style={'textAlign': 'center', 'padding': '20px'})
        ], style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(3, 1fr)',
            'gap': '20px',
            'margin': '20px'
        })
    ], style={
        'backgroundColor': 'white',
        'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'padding': '20px',
        'margin': '20px'
    })
], style={
    'backgroundColor': '#f5f5f5',
    'minHeight': '100vh',
    'fontFamily': 'Arial, sans-serif'
})

if __name__ == '__main__':
    app.run(debug=True)
