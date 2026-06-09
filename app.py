import dash
from dash import html, dcc, dash_table, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from data_processor import (
    process_uploaded_data, REQUIRED_COLUMNS,
    aggregate_by_time_granularity, calculate_growth_rate,
    detect_seasonality, detect_anomalies,
    get_available_dimensions, filter_data
)
from trend_charts import (
    create_line_chart, create_area_chart,
    create_combined_chart
)
from promo_evaluation import (
    evaluate_promo_activity, get_activity_list
)
from customer_analysis import (
    run_customer_analysis, export_clustering_csv
)

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='stored-data', data=None),
    dcc.Store(id='stored-data-local', data=None, storage_type='local'),
    dcc.Store(id='stored-quality-report', data=None),
    dcc.Store(id='eval-result-store', data=None),
    dcc.Store(id='customer-analysis-store', data=None),
    html.Div(id='navbar-container'),
    html.Div(id='page-content')
], style={
    'backgroundColor': '#f5f5f5',
    'minHeight': '100vh',
    'fontFamily': 'Arial, sans-serif'
})


def navbar(current_path, data_valid):
    upload_active = current_path == '/' or current_path == '/upload'
    analysis_active = current_path == '/analysis'
    trend_active = current_path == '/trend'
    evaluation_active = current_path == '/evaluation'
    customer_active = current_path == '/customer'

    if data_valid:
        analysis_link = dcc.Link('促销分析', href='/analysis', style={
            'color': 'white',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#2E86AB' if analysis_active else 'transparent',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'marginRight': '10px'
        })
        trend_link = dcc.Link('趋势分析', href='/trend', style={
            'color': 'white',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#2E86AB' if trend_active else 'transparent',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'marginRight': '10px'
        })
        evaluation_link = dcc.Link('效果评估', href='/evaluation', style={
            'color': 'white',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#2E86AB' if evaluation_active else 'transparent',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'marginRight': '10px'
        })
        customer_link = dcc.Link('客户分析', href='/customer', style={
            'color': 'white',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#2E86AB' if customer_active else 'transparent',
            'borderRadius': '5px',
            'fontWeight': 'bold'
        })
    else:
        analysis_link = html.Span('促销分析', title='请先上传并验证数据', style={
            'color': '#888',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#333',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'cursor': 'not-allowed',
            'marginRight': '10px'
        })
        trend_link = html.Span('趋势分析', title='请先上传并验证数据', style={
            'color': '#888',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#333',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'cursor': 'not-allowed',
            'marginRight': '10px'
        })
        evaluation_link = html.Span('效果评估', title='请先上传并验证数据', style={
            'color': '#888',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#333',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'cursor': 'not-allowed',
            'marginRight': '10px'
        })
        customer_link = html.Span('客户分析', title='请先上传并验证数据', style={
            'color': '#888',
            'textDecoration': 'none',
            'padding': '15px 25px',
            'backgroundColor': '#333',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'cursor': 'not-allowed'
        })

    return html.Div([
        html.Div([
            html.H2('促销活动分析系统', style={
                'color': 'white',
                'margin': 0,
                'fontSize': '20px',
                'paddingRight': '40px'
            }),
            dcc.Link('数据上传', href='/upload', style={
                'color': 'white',
                'textDecoration': 'none',
                'padding': '15px 25px',
                'backgroundColor': '#2E86AB' if upload_active else 'transparent',
                'borderRadius': '5px',
                'fontWeight': 'bold',
                'marginRight': '10px'
            }),
            analysis_link,
            trend_link,
            evaluation_link,
            customer_link
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': '0 30px',
            'height': '60px',
            'backgroundColor': '#1a1a2e',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.15)'
        })
    ])


def upload_page():
    return html.Div([
        html.Div([
            html.H1('数据上传', style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginTop': '30px',
                'marginBottom': '20px'
            }),
            html.Div([
                html.Div([
                    html.H3('上传销售数据文件', style={'color': '#333', 'marginBottom': '15px'}),
                    html.P(f'必要列: {", ".join(REQUIRED_COLUMNS)}', style={
                        'color': '#666',
                        'fontSize': '14px',
                        'marginBottom': '15px'
                    }),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            '拖拽文件到此处 或 ',
                            html.A('点击选择文件', style={'color': '#2E86AB', 'fontWeight': 'bold'})
                        ]),
                        style={
                            'width': '100%',
                            'height': '120px',
                            'lineHeight': '120px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'margin': '10px 0 20px 0',
                            'backgroundColor': '#fafafa',
                            'cursor': 'pointer'
                        },
                        multiple=False,
                        accept='.csv,.xls,.xlsx'
                    ),
                    html.Div(id='upload-filename', style={
                        'textAlign': 'center',
                        'color': '#666',
                        'marginBottom': '10px'
                    }),
                    html.Div(id='upload-errors', style={
                        'color': '#e74c3c',
                        'padding': '15px',
                        'backgroundColor': '#fdecea',
                        'borderRadius': '5px',
                        'marginBottom': '15px',
                        'display': 'none'
                    })
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    'padding': '25px',
                    'margin': '20px'
                }),

                html.Div(id='preview-section', style={'display': 'none'}, children=[
                    html.Div([
                        html.H3('数据预览（前 10 行）', style={'color': '#333', 'marginBottom': '15px'}),
                        html.Div(id='preview-table-container')
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '10px',
                        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                        'padding': '25px',
                        'margin': '20px'
                    }),

                    html.Div([
                        html.H3('数据质量报告', style={'color': '#333', 'marginBottom': '20px'}),
                        html.Div(id='quality-report-container')
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '10px',
                        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                        'padding': '25px',
                        'margin': '20px'
                    })
                ])
            ])
        ])
    ])


def analysis_page():
    return html.Div([
        html.Div(id='analysis-content')
    ])


def trend_page():
    return html.Div([
        html.H1(
            '多维度销售趋势分析',
            style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginBottom': '30px',
                'marginTop': '30px'
            }
        ),

        html.Div(id='trend-filters-container', style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px',
            'margin': '20px'
        }),

        html.Div([
            html.Div([
                html.H3('销售趋势折线图', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='trend-line-chart')
            ], style={
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px',
                'margin': '20px 10px'
            }),

            html.Div([
                html.H3('销售趋势面积图', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='trend-area-chart')
            ], style={
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px',
                'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '0'}),

        html.Div([
            html.Div([
                html.H3('销售趋势组合图（柱状+折线）', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='trend-combined-chart')
            ], style={
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px',
                'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr', 'gap': '0', 'marginTop': '0'}),

        html.Div(id='trend-analysis-conclusion', style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px',
            'margin': '20px'
        })
    ])


def evaluation_page():
    return html.Div([
        html.H1(
            '促销活动效果评估',
            style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginBottom': '30px',
                'marginTop': '30px'
            }
        ),

        html.Div(id='eval-config-container', style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px',
            'margin': '20px'
        }),

        html.Div(id='eval-results-container')
    ])


CLUSTER_COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', '#27ae60', '#8e44ad', '#16a085']


def customer_page():
    return html.Div([
        html.H1(
            '客户分群与行为分析',
            style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginBottom': '30px',
                'marginTop': '30px'
            }
        ),

        html.Div(id='customer-config-container', style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px',
            'margin': '20px'
        }),

        html.Div(id='customer-summary-container'),

        html.Div(id='customer-visualization-container'),

        html.Div(id='customer-profiles-container'),

        html.Div(id='customer-detail-container')
    ])


def build_quality_report_content(report):
    if report is None:
        return html.Div()

    children = []

    children.append(html.Div([
        html.Div([
            html.H4('数据概况', style={'color': '#2E86AB', 'marginBottom': '10px'}),
            html.P(f'总行数: {report["total_rows"]} 行', style={'margin': '5px 0', 'color': '#333'}),
            html.P(f'总列数: {report["total_columns"]} 列', style={'margin': '5px 0', 'color': '#333'})
        ], style={
            'padding': '15px',
            'backgroundColor': '#eaf4fb',
            'borderRadius': '8px',
            'marginBottom': '20px'
        })
    ]))

    missing_rows = []
    for col, stats in report['missing_stats'].items():
        missing_rows.append({
            '列名': col,
            '缺失数量': stats['count'],
            '缺失比例(%)': stats['percentage']
        })

    children.append(html.Div([
        html.H4('缺失值统计', style={'color': '#2E86AB', 'marginBottom': '10px'}),
        dash_table.DataTable(
            data=missing_rows,
            columns=[
                {'name': '列名', 'id': '列名'},
                {'name': '缺失数量', 'id': '缺失数量'},
                {'name': '缺失比例(%)', 'id': '缺失比例(%)'}
            ],
            style_cell={'padding': '10px', 'textAlign': 'left'},
            style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'}
        )
    ], style={'marginBottom': '20px'}))

    dtype_rows = []
    for col, dtype in report['dtype_info'].items():
        dtype_rows.append({
            '列名': col,
            '数据类型': dtype
        })

    children.append(html.Div([
        html.H4('数据类型信息', style={'color': '#2E86AB', 'marginBottom': '10px'}),
        dash_table.DataTable(
            data=dtype_rows,
            columns=[
                {'name': '列名', 'id': '列名'},
                {'name': '数据类型', 'id': '数据类型'}
            ],
            style_cell={'padding': '10px', 'textAlign': 'left'},
            style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto'}
        )
    ], style={'marginBottom': '20px'}))

    if report['outlier_info']:
        outlier_children = []
        for col, info in report['outlier_info'].items():
            outlier_children.append(html.Div([
                html.Strong(f'{col}: ', style={'color': '#e74c3c'}),
                html.Span(f'检测到 {info["count"]} 个异常值', style={'color': '#e74c3c'})
            ], style={'padding': '5px 0'}))
            if info.get('values'):
                outlier_children.append(html.Div([
                    html.Span('  示例值: ', style={'color': '#666', 'fontSize': '13px'}),
                    html.Span(str(info['values']), style={'color': '#666', 'fontSize': '13px'})
                ]))

        children.append(html.Div([
            html.H4('异常值提示', style={'color': '#e74c3c', 'marginBottom': '10px'}),
            html.Div(outlier_children, style={
                'padding': '15px',
                'backgroundColor': '#fdecea',
                'borderRadius': '8px'
            })
        ], style={'marginBottom': '20px'}))
    else:
        children.append(html.Div([
            html.H4('异常值提示', style={'color': '#27ae60', 'marginBottom': '10px'}),
            html.Div('未检测到异常值', style={
                'padding': '15px',
                'backgroundColor': '#e8f8f0',
                'borderRadius': '8px',
                'color': '#27ae60'
            })
        ], style={'marginBottom': '20px'}))

    if report.get('validation_errors'):
        children.append(html.Div([
            html.H4('验证错误', style={'color': '#e74c3c', 'marginBottom': '10px'}),
            html.Ul([html.Li(err, style={'color': '#e74c3c'}) for err in report['validation_errors']],
            style={
                'padding': '15px',
                'backgroundColor': '#fdecea',
                'borderRadius': '8px'
            })
        ]))

    if report.get('is_valid'):
        children.append(html.Div([
            html.Div([
                html.Span('✓ 数据验证通过！', style={
                    'color': 'white',
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                }),
                html.Div([
                    dcc.Link('前往促销分析', href='/analysis', style={
                        'backgroundColor': 'white',
                        'color': '#27ae60',
                        'padding': '8px 20px',
                        'borderRadius': '5px',
                        'textDecoration': 'none',
                        'fontWeight': 'bold',
                        'marginLeft': '15px'
                    }),
                    dcc.Link('前往趋势分析', href='/trend', style={
                        'backgroundColor': 'white',
                        'color': '#2E86AB',
                        'padding': '8px 20px',
                        'borderRadius': '5px',
                        'textDecoration': 'none',
                        'fontWeight': 'bold',
                        'marginLeft': '15px'
                    })
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'space-between',
                'padding': '20px',
                'backgroundColor': '#27ae60',
                'borderRadius': '8px'
            })
        ]))
    else:
        children.append(html.Div([
            html.Div('✗ 数据验证未通过，请修正数据后重新上传', style={
                'color': 'white',
                'fontWeight': 'bold',
                'fontSize': '16px'
            })], style={
                'padding': '20px',
                'backgroundColor': '#e74c3c',
                'borderRadius': '8px'
            }))

    return html.Div(children)


def build_analysis_content(df_json):
    if df_json is None:
        return html.Div([
            html.Div([
                html.H2('请先上传数据', style={'color': '#2E86AB', 'textAlign': 'center', 'marginTop': '60px'}),
                html.P('您尚未上传有效的数据文件，请先前往数据上传页面。', style={
                    'textAlign': 'center',
                    'color': '#666',
                    'marginTop': '20px'
                }),
                html.Div([
                    dcc.Link('前往数据上传', href='/upload', style={
                        'display': 'inline-block',
                        'padding': '12px 30px',
                        'backgroundColor': '#2E86AB',
                        'color': 'white',
                        'textDecoration': 'none',
                        'borderRadius': '5px',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    })
                ], style={'textAlign': 'center', 'marginTop': '30px'})
            ], style={
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '40px',
                'margin': '40px auto',
                'maxWidth': '600px'
            })
        ])

    df = pd.read_json(df_json, orient='split')

    if '销售额' not in df.columns:
        return html.Div('数据格式错误', style={'padding': '40px', 'color': '#e74c3c'})

    fig = px.bar(
        df,
        x='期间',
        y='销售额',
        color='类型',
        color_discrete_map={
            '促销期间': '#2E86AB',
            '非促销期间': '#A23B72'
        },
        title='促销期间与非促销期间销售对比',
        labels={'期间': '期间', '销售额': '销售额'},
        text='销售额',
    )

    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(
        showlegend=True,
        legend_title='期间类型',
        plot_bgcolor='white',
        font=dict(size=12),
        title_x=0.5,
    )

    promo_data = df[df['类型'] == '促销期间']
    non_promo_data = df[df['类型'] == '非促销期间']

    promo_avg = promo_data['销售额'].mean() if len(promo_data) > 0 else 0
    non_promo_avg = non_promo_data['销售额'].mean() if len(non_promo_data) > 0 else 0
    lift_rate = ((promo_avg - non_promo_avg) / non_promo_avg * 100) if non_promo_avg > 0 else 0

    return html.Div([
        html.H1(
            '促销活动分析页面',
            style={
                'textAlign': 'center',
                'color': '#2E86AB',
                'marginBottom': '30px',
                'marginTop': '30px'
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
                    html.P(f'{promo_avg:.1f}', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#2E86AB'})
                ], style={'textAlign': 'center', 'padding': '20px'}),

                html.Div([
                    html.H4('非促销期间平均销售额', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{non_promo_avg:.1f}', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#A23B72'})
                ], style={'textAlign': 'center', 'padding': '20px'}),

                html.Div([
                    html.H4('销售提升率', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{lift_rate:.1f}%', style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#F18F01'})
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
    ])


@callback(
    Output('stored-data', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('stored-data-local', 'data'),
    State('stored-data', 'data'),
    prevent_initial_call='initial_duplicate'
)
def restore_data_from_local(pathname, local_data, current_data):
    if current_data is None and local_data is not None:
        return local_data
    return dash.no_update


@callback(
    Output('navbar-container', 'children'),
    Input('url', 'pathname'),
    Input('stored-data', 'data')
)
def render_navbar(pathname, stored_data):
    data_valid = stored_data is not None
    return navbar(pathname, data_valid)


@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('stored-data', 'data')
)
def display_page(pathname, stored_data):
    if pathname in ['/analysis', '/trend', '/evaluation', '/customer']:
        if stored_data is None:
            return html.Div([
                html.Div([
                    html.H2('请先上传数据', style={'color': '#2E86AB', 'textAlign': 'center', 'marginTop': '60px'}),
                    html.P('您尚未上传有效的数据文件，请先前往数据上传页面完成验证。', style={
                        'textAlign': 'center',
                        'color': '#666',
                        'marginTop': '20px'
                    }),
                    html.Div([
                        dcc.Link('前往数据上传', href='/upload', style={
                            'display': 'inline-block',
                            'padding': '12px 30px',
                            'backgroundColor': '#2E86AB',
                            'color': 'white',
                            'textDecoration': 'none',
                            'borderRadius': '5px',
                            'fontWeight': 'bold',
                            'textAlign': 'center'
                        })
                    ], style={'textAlign': 'center', 'marginTop': '30px'})
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                    'padding': '40px',
                    'margin': '40px auto',
                    'maxWidth': '600px'
                })
            ])
        if pathname == '/analysis':
            return analysis_page()
        elif pathname == '/trend':
            return trend_page()
        elif pathname == '/evaluation':
            return evaluation_page()
        else:
            return customer_page()
    else:
        return upload_page()


@callback(
    Output('analysis-content', 'children'),
    Input('stored-data', 'data')
)
def render_analysis_content(df_json):
    return build_analysis_content(df_json)


@callback(
    Output('stored-data', 'data'),
    Output('stored-data-local', 'data'),
    Output('stored-quality-report', 'data'),
    Output('upload-filename', 'children'),
    Output('upload-errors', 'children'),
    Output('upload-errors', 'style'),
    Output('preview-section', 'style'),
    Output('preview-table-container', 'children'),
    Output('quality-report-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('stored-data', 'data'),
    State('stored-quality-report', 'data'),
    prevent_initial_call=True
)
def handle_upload(contents, filename, existing_data, existing_report):
    ctx = dash.callback_context

    if not ctx.triggered:
        return (
            existing_data,
            existing_data,
            existing_report,
            '',
            '',
            {'display': 'none'},
            {'display': 'none'},
            html.Div(),
            html.Div()
        )

    if contents is None:
        return (
            existing_data,
            existing_data,
            existing_report,
            '',
            '',
            {'display': 'none'},
            {'display': 'none'},
            html.Div(),
            html.Div()
        )

    result = process_uploaded_data(contents, filename)

    errors = result['errors']
    success = result['success']
    df = result['df']
    preview = result['preview']
    report = result['quality_report']

    stored_data = df.to_json(orient='split') if (df is not None and success) else existing_data
    stored_report = json.dumps(report) if report is not None else existing_report

    filename_display = html.Div([
        html.Strong('已上传文件: ', style={'color': '#333'}),
        html.Span(filename, style={'color': '#2E86AB'})
    ])

    if errors:
        errors_display = html.Div([
            html.H4('上传失败:', style={'margin': '0 0 10px 0'}),
            html.Ul([html.Li(e) for e in errors])
        ])
        errors_style = {
            'color': '#e74c3c',
            'padding': '15px',
            'backgroundColor': '#fdecea',
            'borderRadius': '5px',
            'marginBottom': '15px',
            'display': 'block'
        }
    else:
        errors_display = ''
        errors_style = {'display': 'none'}

    preview_style = {'display': 'block'} if preview is not None else {'display': 'none'}

    preview_table = html.Div()
    if preview is not None:
        preview_table = dash_table.DataTable(
            data=preview.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in preview.columns],
            style_cell={'padding': '10px', 'textAlign': 'left', 'whiteSpace': 'normal'},
            style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'},
            style_table={'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '400px'},
            page_size=10
        )

    quality_content = html.Div()
    if report is not None:
        quality_content = build_quality_report_content(report)

    return (
        stored_data,
        stored_data,
        stored_report,
        filename_display,
        errors_display,
        errors_style,
        preview_style,
        preview_table,
        quality_content
    )


@callback(
    Output('trend-filters-container', 'children'),
    Input('stored-data', 'data')
)
def render_trend_filters(df_json):
    if df_json is None:
        return html.Div()

    df = pd.read_json(df_json, orient='split')
    dimensions = get_available_dimensions(df)

    children = []

    children.append(html.Div([
        html.Label('时间粒度', style={'fontWeight': 'bold', 'color': '#333', 'marginBottom': '8px', 'display': 'block'}),
        dcc.RadioItems(
            id='time-granularity',
            options=[
                {'label': '按日', 'value': '日'},
                {'label': '按周', 'value': '周'},
                {'label': '按月', 'value': '月'}
            ],
            value='日',
            inline=True,
            labelStyle={'marginRight': '20px', 'fontSize': '14px'}
        )
    ], style={'marginBottom': '20px'}))

    filter_row = []

    if dimensions.get('产品类别'):
        filter_row.append(html.Div([
            html.Label('产品类别', style={'fontWeight': 'bold', 'color': '#333', 'marginBottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': c, 'value': c} for c in dimensions['产品类别']],
                value=None,
                multi=True,
                placeholder='选择产品类别（可多选）',
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px'}))

    if dimensions.get('地区'):
        filter_row.append(html.Div([
            html.Label('地区', style={'fontWeight': 'bold', 'color': '#333', 'marginBottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='region-filter',
                options=[{'label': r, 'value': r} for r in dimensions['地区']],
                value=None,
                multi=True,
                placeholder='选择地区（可多选）',
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'minWidth': '200px'}))

    if filter_row:
        children.append(html.Div(filter_row, style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px', 'alignItems': 'flex-end'}))

    return html.Div(children)


def process_trend_data(df_json, granularity, categories, regions):
    if df_json is None:
        return None, None

    df = pd.read_json(df_json, orient='split')
    df = filter_data(df, categories, regions, None)

    if len(df) == 0:
        return None, None

    time_col = '期间' if '期间' in df.columns else df.columns[0]
    agg_df = aggregate_by_time_granularity(df, time_col, '销售额', granularity, None)

    return df, agg_df


@callback(
    Output('trend-line-chart', 'figure'),
    Output('trend-area-chart', 'figure'),
    Output('trend-combined-chart', 'figure'),
    Output('trend-analysis-conclusion', 'children'),
    Input('stored-data', 'data'),
    Input('time-granularity', 'value'),
    Input('category-filter', 'value'),
    Input('region-filter', 'value')
)
def update_trend_charts(df_json, granularity, categories, regions):
    if df_json is None:
        empty_fig = {
            'data': [],
            'layout': {
                'title': {'text': '暂无数据', 'x': 0.5},
                'xaxis': {'visible': False},
                'yaxis': {'visible': False}}}
        return empty_fig, empty_fig, empty_fig, html.Div()

    original_df, agg_df = process_trend_data(df_json, granularity, categories, regions)

    if agg_df is None or len(agg_df) == 0 or agg_df.empty:
        empty_fig = {
            'data': [],
            'layout': {
                'title': {'text': '暂无数据', 'x': 0.5},
                'xaxis': {'visible': False},
                'yaxis': {'visible': False},
                'annotations': [{
                    'text': '请选择筛选条件后查看数据',
                    'showarrow': False,
                    'font': {'size': 16}}]}}
        return empty_fig, empty_fig, empty_fig, html.Div('暂无数据，请调整筛选条件')

    line_fig = create_line_chart(agg_df, group_col=None,
                            title=f'销售趋势折线图（{granularity}度）')
    area_fig = create_area_chart(agg_df, group_col=None,
                                title=f'销售趋势面积图（{granularity}度）')
    combined_fig = create_combined_chart(agg_df, group_col=None,
                               title=f'销售趋势组合图（{granularity}度）')

    conclusion = build_trend_conclusion(agg_df, original_df)

    return line_fig, area_fig, combined_fig, conclusion


def build_trend_conclusion(agg_df, original_df):
    if agg_df is None or len(agg_df) < 2:
        return html.Div([
            html.H3('趋势分析结论', style={'color': '#333', 'marginBottom': '15px'}),
            html.P('数据点不足，无法进行趋势分析', style={'color': '#999'})
        ])

    children = []
    children.append(html.H3('趋势分析结论', style={'color': '#333', 'marginBottom': '20px'}))

    growth = calculate_growth_rate(agg_df)
    seasonality = detect_seasonality(agg_df)
    anomalies = detect_anomalies(agg_df)

    children.append(html.Div([
        html.H4('📈 增长率分析', style={'color': '#2E86AB', 'marginBottom': '12px'}),
        html.Div([
            html.Div([
                html.Div([
                    html.P('累计增长率', style={'color': '#666', 'fontSize': '14px', 'margin': '0'}),
                    html.P(
                        f"{growth['total_growth_rate']:.2f}%" if growth['total_growth_rate'] is not None else 'N/A',
                        style={'fontSize': '28px', 'fontWeight': 'bold',
                               'color': '#27ae60' if (growth['total_growth_rate'] or 0) >= 0 else '#e74c3c',
                               'margin': '5px 0 0 0'}
                    )
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'flex': '1'}),
                html.Div([
                    html.P('平均环比增长率', style={'color': '#666', 'fontSize': '14px', 'margin': '0'}),
                    html.P(
                        f"{growth['avg_growth_rate']:.2f}%" if growth['avg_growth_rate'] is not None else 'N/A',
                        style={'fontSize': '28px', 'fontWeight': 'bold',
                               'color': '#27ae60' if (growth['avg_growth_rate'] or 0) >= 0 else '#e74c3c',
                               'margin': '5px 0 0 0'}
                    )
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'flex': '1'}),
                html.Div([
                    html.P('整体趋势', style={'color': '#666', 'fontSize': '14px', 'margin': '0'}),
                    html.P(
                        {'up': '📈 上升趋势', 'down': '📉 下降趋势', 'stable': '➡️ 平稳趋势'}.get(growth['trend'], '未知'),
                        style={'fontSize': '20px', 'fontWeight': 'bold',
                               'color': '#27ae60' if growth['trend'] == 'up' else (
                                   '#e74c3c' if growth['trend'] == 'down' else '#F18F01'),
                               'margin': '5px 0 0 0'}
                    )
                ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'flex': '1'})
            ], style={'display': 'flex', 'gap': '15px', 'marginTop': '10px'})
        ])
    ], style={'marginBottom': '25px', 'padding': '20px', 'backgroundColor': '#eaf4fb', 'borderRadius': '10px'}))

    seasonality_children = []
    if seasonality['has_seasonality']:
        seasonality_children.append(html.Div([
            html.Strong('季节性模式: ', style={'color': '#F18F01'}),
            html.Span(seasonality['seasonal_pattern'] or '检测到季节性特征', style={'color': '#333'})
        ], style={'marginBottom': '10px'}))
        if seasonality['peak_periods']:
            seasonality_children.append(html.Div([
                html.Strong('旺季时段: ', style={'color': '#27ae60'}),
                html.Span('、'.join(seasonality['peak_periods']), style={'color': '#333'})
            ], style={'marginBottom': '8px'}))
        if seasonality['low_periods']:
            seasonality_children.append(html.Div([
                html.Strong('淡季时段: ', style={'color': '#e74c3c'}),
                html.Span('、'.join(seasonality['low_periods']), style={'color': '#333'})
            ]))
    else:
        seasonality_children.append(html.Div(
            '未检测到明显的季节性模式，销售数据相对平稳',
            style={'color': '#666'}
        ))

    children.append(html.Div([
        html.H4('🌊 季节性模式识别', style={'color': '#F18F01', 'marginBottom': '12px'}),
        html.Div(seasonality_children)
    ], style={'marginBottom': '25px', 'padding': '20px', 'backgroundColor': '#fff8e6', 'borderRadius': '10px'}))

    anomaly_children = []
    if anomalies:
        for a in anomalies:
            color = '#e74c3c' if '偏低' in a['type'] else '#C73E1D'
            anomaly_children.append(html.Div([
                html.Strong(f"[{a['time']}] ", style={'color': color}),
                html.Span(f"{a['type']}: 销售额 {a['value']:,.0f}，偏离均值 {a['deviation']:+.2f}%",
                          style={'color': '#333'})
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #eee'}))
    else:
        anomaly_children.append(html.Div(
            '✅ 未检测到异常波动，数据表现正常',
            style={'color': '#27ae60'}
        ))

    children.append(html.Div([
        html.H4('⚠️ 异常波动提醒', style={'color': '#C73E1D', 'marginBottom': '12px'}),
        html.Div(anomaly_children)
    ], style={'padding': '20px', 'backgroundColor': '#fdecea' if anomalies else '#e8f8f0', 'borderRadius': '10px'}))

    return html.Div(children)


def build_eval_config_content(df_json):
    if df_json is None:
        return html.Div()

    df = pd.read_json(df_json, orient='split')
    activity_types = get_activity_list(df)

    if not activity_types:
        return html.Div('未检测到有效的促销活动类型，请确认数据中包含活动名称列或类型列', style={
            'color': '#e74c3c', 'padding': '20px', 'fontSize': '14px'
        })

    children = []

    children.append(html.Div([
        html.H3('活动配置与评估参数', style={'color': '#333', 'marginBottom': '20px'}),

        html.Div([
            html.Label('选择促销活动', style={
                'fontWeight': 'bold', 'color': '#333',
                'marginBottom': '8px', 'display': 'block', 'fontSize': '14px'
            }),
            dcc.Dropdown(
                id='eval-activity-select',
                options=[{'label': a, 'value': a} for a in activity_types],
                value=activity_types[0],
                style={'width': '100%'}
            )
        ], style={'marginBottom': '20px'}),

        html.Div([
            html.H4('指标权重配置（总和自动归一化为100%）', style={
                'color': '#333', 'marginBottom': '15px', 'fontSize': '15px'
            }),
            html.Div([
                html.Div([
                    html.Label('投资回报 权重', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Slider(
                        id='weight-roi',
                        min=0,
                        max=100,
                        value=30,
                        marks={i: f'{i}%' for i in range(0, 101, 25)},
                        step=5
                    )
                ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px', 'marginBottom': '15px'}),

                html.Div([
                    html.Label('销售增量 权重', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Slider(
                        id='weight-lift',
                        min=0,
                        max=100,
                        value=25,
                        marks={i: f'{i}%' for i in range(0, 101, 25)},
                        step=5
                    )
                ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px', 'marginBottom': '15px'}),

                html.Div([
                    html.Label('客户获取 权重', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Slider(
                        id='weight-cac',
                        min=0,
                        max=100,
                        value=20,
                        marks={i: f'{i}%' for i in range(0, 101, 25)},
                        step=5
                    )
                ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px', 'marginBottom': '15px'}),

                html.Div([
                    html.Label('利润边际 权重', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Slider(
                        id='weight-margin',
                        min=0,
                        max=100,
                        value=25,
                        marks={i: f'{i}%' for i in range(0, 101, 25)},
                        step=5
                    )
                ], style={'flex': '1', 'minWidth': '200px', 'marginBottom': '15px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px'}),

            html.Div(id='weight-summary', style={
                'marginTop': '10px', 'padding': '10px',
                'backgroundColor': '#eaf4fb', 'borderRadius': '6px',
                'fontSize': '13px', 'color': '#2E86AB'
            })
        ], style={'marginBottom': '20px'}),

        html.Div([
            html.H4('活动参数配置（如数据中未包含，可手动填写）', style={
                'color': '#333', 'marginBottom': '15px', 'fontSize': '15px'
            }),
            html.Div([
                html.Div([
                    html.Label('促销成本（元）', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Input(
                        id='input-promo-cost',
                        type='number',
                        placeholder='请输入促销总成本',
                        min=0,
                        value=30000,
                        style={
                            'width': '100%', 'padding': '10px',
                            'border': '1px solid #ddd', 'borderRadius': '5px',
                            'fontSize': '14px'
                        }
                    ),
                    html.Div('数据中包含促销成本/活动成本/营销费用列时将自动读取', style={
                        'color': '#999', 'fontSize': '11px', 'marginTop': '5px'
                    })
                ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px', 'marginBottom': '15px'}),

                html.Div([
                    html.Label('新增客户数（人）', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Input(
                        id='input-new-customers',
                        type='number',
                        placeholder='请输入新增客户数量',
                        min=0,
                        value=500,
                        style={
                            'width': '100%', 'padding': '10px',
                            'border': '1px solid #ddd', 'borderRadius': '5px',
                            'fontSize': '14px'
                        }
                    ),
                    html.Div('数据中包含新增客户数/新客户数/获客数列时将自动读取', style={
                        'color': '#999', 'fontSize': '11px', 'marginTop': '5px'
                    })
                ], style={'flex': '1', 'minWidth': '200px', 'marginBottom': '15px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px'})
        ], style={'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#fafafa', 'borderRadius': '8px'}),

        html.Div([
            html.Button(
                '生成评估结果',
                id='btn-generate-eval',
                n_clicks=0,
                style={
                    'backgroundColor': '#2E86AB', 'color': 'white',
                    'padding': '12px 40px', 'border': 'none',
                    'borderRadius': '6px', 'fontWeight': 'bold',
                    'fontSize': '15px', 'cursor': 'pointer',
                    'boxShadow': '0 2px 6px rgba(46, 134, 171, 0.4)'
                }
            )
        ], style={'textAlign': 'center', 'marginTop': '10px'})
    ]))

    return html.Div(children)


def create_radar_chart(radar_data, activity_name):
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=radar_data['评分'] + [radar_data['评分'][0]],
        theta=radar_data['指标'] + [radar_data['指标'][0]],
        fill='toself',
        name=activity_name,
        line=dict(color='#2E86AB', width=3),
        fillcolor='rgba(46, 134, 171, 0.3)',
        marker=dict(size=10, color='#2E86AB')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=13, color='#333')
            )
        ),
        showlegend=False,
        title=dict(
            text=f'{activity_name} - 综合评分雷达图',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='#333')
        ),
        margin=dict(l=30, r=30, t=80, b=30),
        paper_bgcolor='white'
    )

    return fig


def build_eval_results_content(eval_result):
    if eval_result is None:
        return html.Div()

    activity_name = eval_result['活动名称']
    comprehensive = eval_result['综合评分']
    radar_data = eval_result['雷达图数据']

    children = []

    children.append(html.Div([
        html.Div([
            html.H3('综合评分概览', style={'color': '#333', 'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.Div('综合评分', style={
                        'color': '#666', 'fontSize': '14px', 'marginBottom': '5px'
                    }),
                    html.Div(f"{comprehensive['综合评分']:.2f}", style={
                        'fontSize': '48px', 'fontWeight': 'bold',
                        'color': '#2E86AB'
                    }),
                    html.Div(comprehensive['评级'], style={
                        'fontSize': '18px', 'fontWeight': 'bold',
                        'color': '#F18F01', 'marginTop': '5px'
                    })
                ], style={
                    'textAlign': 'center', 'padding': '20px',
                    'backgroundColor': '#eaf4fb', 'borderRadius': '10px',
                    'flex': '1'
                }),

                html.Div([
                    html.Div([
                        html.Div('各维度评分：', style={
                            'fontWeight': 'bold', 'color': '#333',
                            'marginBottom': '12px', 'fontSize': '14px'
                        })
                    ]),
                    html.Div([
                        html.Div([
                            html.Span(dim, style={
                                'display': 'inline-block', 'width': '100px',
                                'color': '#666', 'fontSize': '13px'
                            }),
                            html.Div([
                                html.Div(style={
                                    'width': f"{score}%",
                                    'height': '18px',
                                    'backgroundColor': '#2E86AB' if score >= 70 else (
                                        '#F18F01' if score >= 50 else '#e74c3c'
                                    ),
                                    'borderRadius': '4px',
                                    'display': 'inline-block'
                                })
                            ], style={
                                'display': 'inline-block',
                                'width': '150px',
                                'backgroundColor': '#f0f0f0',
                                'borderRadius': '4px',
                                'height': '18px',
                                'overflow': 'hidden',
                                'verticalAlign': 'middle'
                            }),
                            html.Span(f" {score:.1f}分", style={
                                'fontWeight': 'bold', 'color': '#333',
                                'fontSize': '13px', 'marginLeft': '8px'
                            })
                        ], style={'marginBottom': '10px'})
                        for dim, score in comprehensive['维度评分'].items()
                    ])
                ], style={'flex': '2', 'padding': '20px'})
            ], style={'display': 'flex', 'gap': '20px', 'alignItems': 'center'})
        ], style={
            'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px', 'margin': '20px'
        }),

        html.Div([
            html.Div([
                html.H3('综合评分雷达图', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(figure=create_radar_chart(radar_data, activity_name))
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            }),

            html.Div([
                html.H3('各活动对比分析', style={'color': '#333', 'marginBottom': '15px'}),
                _build_activity_comparison_panel(eval_result['活动对比'])
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '0'}),

        html.Div([
            html.H3('各活动评分对比明细', style={'color': '#333', 'marginBottom': '15px'}),
            _build_all_activities_table(eval_result['活动对比'])
        ], style={
            'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px', 'margin': '20px'
        }),

        html.Div([
            html.H3('核心指标详细分析', style={'color': '#333', 'marginBottom': '20px'}),
            _build_detail_tables(eval_result)
        ], style={
            'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px', 'margin': '20px'
        }),

        html.Div([
            html.H3('改进建议', style={'color': '#333', 'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.Div('💡', style={'fontSize': '22px', 'marginRight': '10px'}),
                    html.Div(suggestion, style={
                        'color': '#333', 'lineHeight': '1.8',
                        'fontSize': '14px', 'flex': '1'
                    })
                ], style={
                    'display': 'flex', 'alignItems': 'flex-start',
                    'padding': '15px', 'marginBottom': '10px',
                    'backgroundColor': '#fffaf0', 'borderLeft': '4px solid #F18F01',
                    'borderRadius': '6px'
                })
                for suggestion in eval_result['改进建议']
            ])
        ], style={
            'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px', 'margin': '20px'
        })
    ]))

    return html.Div(children)


def _build_activity_comparison_panel(comp_data):
    children = []

    children.append(html.Div([
        html.Div([
            html.Div('总排名', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(comp_data['总排名'], style={
                'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2E86AB'
            })
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'}),

        html.Div([
            html.Div('相对其他活动平均', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(
                f"{comp_data['相对其他活动平均']:+.2f}分",
                style={
                    'fontSize': '20px', 'fontWeight': 'bold',
                    'color': '#27ae60' if comp_data['相对其他活动平均'] >= 0 else '#e74c3c'
                }
            )
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'}),

        html.Div([
            html.Div('其他活动最高分', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(f"{comp_data['其他活动最高分']:.2f}", style={
                'fontSize': '20px', 'fontWeight': 'bold', 'color': '#F18F01'
            })
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'}))

    children.append(html.Div([
        html.Div(comp_data['对比结论'], style={
            'padding': '12px', 'backgroundColor': '#eaf4fb',
            'borderRadius': '6px', 'color': '#2E86AB',
            'fontSize': '13px', 'lineHeight': '1.6'
        })
    ], style={'marginBottom': '15px'}))

    dim_data = comp_data['维度对比']
    dim_rows = []
    for dim, info in dim_data.items():
        dim_rows.append({
            '评估维度': dim,
            '当前评分': info['当前评分'],
            '其他活动平均': info['其他活动平均'],
            '差异': f"{info['差异']:+.2f}"
        })

    children.append(html.Div([
        html.Label('各维度与其他活动对比', style={
            'fontWeight': 'bold', 'color': '#333',
            'fontSize': '13px', 'marginBottom': '8px', 'display': 'block'
        }),
        dash_table.DataTable(
            data=dim_rows,
            columns=[
                {'name': '评估维度', 'id': '评估维度'},
                {'name': '当前评分', 'id': '当前评分'},
                {'name': '其他活动平均', 'id': '其他活动平均'},
                {'name': '差异', 'id': '差异'}
            ],
            style_cell={'padding': '8px', 'textAlign': 'center', 'fontSize': '13px'},
            style_header={
                'backgroundColor': '#f0f0f0', 'fontWeight': 'bold',
                'fontSize': '13px', 'textAlign': 'center'
            },
            style_table={'overflowX': 'auto'}
        )
    ]))

    return html.Div(children)


def _build_all_activities_table(comp_data):
    rows = comp_data['各活动评分明细表']

    def _style_row(row):
        if row['对比结果'] == '当前活动':
            return {'backgroundColor': '#eaf4fb', 'fontWeight': 'bold'}
        return {}

    return dash_table.DataTable(
        data=rows,
        columns=[
            {'name': '活动名称', 'id': '活动名称'},
            {'name': '综合评分', 'id': '综合评分'},
            {'name': '投资回报', 'id': '投资回报'},
            {'name': '销售增量', 'id': '销售增量'},
            {'name': '客户获取', 'id': '客户获取'},
            {'name': '利润边际', 'id': '利润边际'},
            {'name': '评级', 'id': '评级'},
            {'name': '对比结果', 'id': '对比结果'}
        ],
        style_cell={'padding': '10px', 'textAlign': 'center', 'fontSize': '13px'},
        style_header={
            'backgroundColor': '#f0f0f0', 'fontWeight': 'bold',
            'fontSize': '13px', 'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{对比结果} = "当前活动"'},
                'backgroundColor': '#eaf4fb',
                'fontWeight': 'bold'
            },
            {
                'if': {'filter_query': '{对比结果} = "优于"'},
                'color': '#27ae60'
            },
            {
                'if': {'filter_query': '{对比结果} = "劣于"'},
                'color': '#e74c3c'
            }
        ],
        style_table={'overflowX': 'auto'},
        sort_action='native'
    )


def _build_detail_tables(eval_result):
    roi = eval_result['投资回报分析']
    inc = eval_result['增量销售分析']
    cac = eval_result['客户获取分析']
    margin = eval_result['利润边际分析']

    def _make_table(data_dict, title, grade_key=None):
        rows = []
        for k, v in data_dict.items():
            if k == grade_key:
                continue
            rows.append({'指标': k, '数值': v})

        header_style = {'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'}
        cell_style = {'padding': '10px', 'textAlign': 'left', 'fontSize': '13px'}

        table_content = [
            dash_table.DataTable(
                data=rows,
                columns=[{'name': '指标', 'id': '指标'}, {'name': '数值', 'id': '数值'}],
                style_cell=cell_style,
                style_header=header_style,
                style_table={'overflowX': 'auto'}
            )
        ]

        if grade_key and grade_key in data_dict:
            table_content.insert(0, html.Div([
                html.Span('等级评定: ', style={'color': '#666', 'fontSize': '13px'}),
                html.Span(data_dict[grade_key], style={
                    'fontWeight': 'bold', 'color': '#F18F01',
                    'fontSize': '15px', 'marginLeft': '5px'
                })
            ], style={'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#fffaf0', 'borderRadius': '6px'}))

        return html.Div([
            html.H4(title, style={'color': '#2E86AB', 'marginBottom': '12px', 'fontSize': '15px'}),
            html.Div(table_content)
        ], style={'padding': '15px', 'backgroundColor': '#fafafa', 'borderRadius': '8px'})

    return html.Div([
        html.Div([
            _make_table(roi, '📊 投资回报分析', '评级'),
            _make_table(inc, '📈 增量销售分析', '提升等级')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}),
        html.Div([
            _make_table(cac, '👥 客户获取成本分析', '客户质量等级'),
            _make_table(margin, '💰 利润边际分析', '利润等级')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'})
    ])


@callback(
    Output('eval-config-container', 'children'),
    Input('stored-data', 'data'),
    prevent_initial_call=False
)
def render_eval_config(df_json):
    if df_json is None:
        return html.Div()
    return build_eval_config_content(df_json)


@callback(
    Output('weight-summary', 'children'),
    Input('weight-roi', 'value'),
    Input('weight-lift', 'value'),
    Input('weight-cac', 'value'),
    Input('weight-margin', 'value'),
    prevent_initial_call=True
)
def update_weight_summary(w_roi, w_lift, w_cac, w_margin):
    if w_roi is None or w_lift is None or w_cac is None or w_margin is None:
        return dash.no_update

    total = w_roi + w_lift + w_cac + w_margin
    if total == 0:
        return html.Div('⚠️ 权重总和不能为 0，请调整权重配置', style={'color': '#e74c3c'})

    n_roi = w_roi / total * 100
    n_lift = w_lift / total * 100
    n_cac = w_cac / total * 100
    n_margin = w_margin / total * 100

    return (
        f'归一化后权重 → 投资回报: {n_roi:.1f}% | '
        f'销售增量: {n_lift:.1f}% | '
        f'客户获取: {n_cac:.1f}% | '
        f'利润边际: {n_margin:.1f}%'
    )


@callback(
    Output('eval-results-container', 'children'),
    Output('eval-result-store', 'data'),
    Input('btn-generate-eval', 'n_clicks'),
    State('stored-data', 'data'),
    State('eval-activity-select', 'value'),
    State('weight-roi', 'value'),
    State('weight-lift', 'value'),
    State('weight-cac', 'value'),
    State('weight-margin', 'value'),
    State('input-promo-cost', 'value'),
    State('input-new-customers', 'value'),
    prevent_initial_call=True
)
def generate_eval_results(n_clicks, df_json, activity_type, w_roi, w_lift, w_cac, w_margin, promo_cost, new_customers):
    if n_clicks is None or n_clicks == 0:
        return html.Div(), None

    if df_json is None or activity_type is None:
        return html.Div([
            html.Div('⚠️ 请先上传有效数据并选择促销活动', style={
                'color': '#e74c3c', 'padding': '20px',
                'backgroundColor': '#fdecea', 'borderRadius': '8px',
                'textAlign': 'center'
            })
        ], None)

    if w_roi is None or w_lift is None or w_cac is None or w_margin is None:
        return dash.no_update, dash.no_update

    total = w_roi + w_lift + w_cac + w_margin
    if total == 0:
        return html.Div([
            html.Div('⚠️ 权重总和不能为 0，请调整权重配置', style={
                'color': '#e74c3c', 'padding': '20px',
                'backgroundColor': '#fdecea', 'borderRadius': '8px',
                'textAlign': 'center'
            })
        ], None)

    weights = {
        '投资回报': w_roi / total,
        '销售增量': w_lift / total,
        '客户获取': w_cac / total,
        '利润边际': w_margin / total
    }

    df = pd.read_json(df_json, orient='split')

    actual_promo_cost = float(promo_cost) if promo_cost is not None and promo_cost > 0 else None
    actual_new_customers = int(new_customers) if new_customers is not None and new_customers > 0 else None

    try:
        eval_result = evaluate_promo_activity(
            df, activity_type, weights,
            promo_cost=actual_promo_cost,
            new_customers=actual_new_customers
        )
        return build_eval_results_content(eval_result), eval_result
    except Exception as e:
        return html.Div([
            html.Div(f'❌ 评估失败：{str(e)}', style={
                'color': '#e74c3c', 'padding': '20px',
                'backgroundColor': '#fdecea', 'borderRadius': '8px',
                'textAlign': 'center'
            })
        ], None)


def build_customer_config_content(df_json):
    if df_json is None:
        return html.Div()

    children = []

    children.append(html.Div([
        html.H3('客户分析参数配置', style={'color': '#333', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.Label('聚类数量 (K)', style={
                    'fontWeight': 'bold', 'color': '#333',
                    'marginBottom': '8px', 'display': 'block', 'fontSize': '14px'
                }),
                dcc.Slider(
                    id='cluster-count-slider',
                    min=2,
                    max=8,
                    value=4,
                    marks={i: f'{i}个' for i in range(2, 9)},
                    step=1
                ),
                html.Div('建议 3-5 个聚类，系统会根据轮廓系数自动推荐最优值', style={
                    'color': '#999', 'fontSize': '12px', 'marginTop': '5px'
                })
            ], style={'marginBottom': '25px'}),

            html.Div([
                html.Label('散点图 X轴维度', style={
                    'fontWeight': 'bold', 'color': '#333',
                    'marginBottom': '8px', 'display': 'block', 'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='scatter-x-axis',
                    options=[
                        {'label': '最近购买天数', 'value': 'Recency'},
                        {'label': '购买频次', 'value': 'Frequency'},
                        {'label': '消费总额', 'value': 'Monetary'},
                        {'label': '平均客单价', 'value': 'AvgOrderValue'}
                    ],
                    value='Frequency',
                    style={'width': '100%'}
                )
            ], style={'flex': '1', 'minWidth': '200px', 'marginRight': '20px', 'marginBottom': '15px'}),

            html.Div([
                html.Label('散点图 Y轴维度', style={
                    'fontWeight': 'bold', 'color': '#333',
                    'marginBottom': '8px', 'display': 'block', 'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='scatter-y-axis',
                    options=[
                        {'label': '最近购买天数', 'value': 'Recency'},
                        {'label': '购买频次', 'value': 'Frequency'},
                        {'label': '消费总额', 'value': 'Monetary'},
                        {'label': '平均客单价', 'value': 'AvgOrderValue'}
                    ],
                    value='Monetary',
                    style={'width': '100%'}
                )
            ], style={'flex': '1', 'minWidth': '200px', 'marginBottom': '15px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px'}),

        html.Div([
            html.Button(
                '开始客户分群分析',
                id='btn-run-customer-analysis',
                n_clicks=0,
                style={
                    'backgroundColor': '#2E86AB', 'color': 'white',
                    'padding': '12px 40px', 'border': 'none',
                    'borderRadius': '6px', 'fontWeight': 'bold',
                    'fontSize': '15px', 'cursor': 'pointer',
                    'boxShadow': '0 2px 6px rgba(46, 134, 171, 0.4)'
                }
            ),
            dcc.Download(id='download-customer-csv')
        ], style={'textAlign': 'center', 'marginTop': '20px'})
    ]))

    return html.Div(children)


COL_NAME_MAP = {
    'Recency': '最近购买天数',
    'Frequency': '购买频次',
    'Monetary': '消费总额',
    'AvgOrderValue': '平均客单价'
}


def build_customer_summary(analysis_result):
    if analysis_result is None or not analysis_result.get('success'):
        return html.Div()

    profiles = analysis_result.get('cluster_profiles', [])
    total_cust = analysis_result.get('total_customers', 0)
    total_tx = analysis_result.get('total_transactions', 0)
    cluster_info = analysis_result.get('cluster_info', {})
    is_simulated = analysis_result.get('is_simulated', False)

    avg_order_value = analysis_result.get('rfm_data', pd.DataFrame())
    if not avg_order_value.empty:
        avg_monetary = round(avg_order_value['Monetary'].mean(), 2)
        avg_frequency = round(avg_order_value['Frequency'].mean(), 1)
        avg_recency = round(avg_order_value['Recency'].mean(), 1)
    else:
        avg_monetary = 0
        avg_frequency = 0
        avg_recency = 0

    silhouette = cluster_info.get('silhouette_score')
    silhouette_display = silhouette if silhouette is not None else 'N/A'

    children = [
        html.Div([
            html.H3('客户分析概览', style={'color': '#333', 'marginBottom': '15px'}),

            html.Div([
                html.Div([
                    html.H4('总客户数', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{total_cust}', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#2E86AB'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#eaf4fb', 'borderRadius': '10px', 'flex': '1'}),

                html.Div([
                    html.H4('总交易数', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{total_tx}', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#A23B72'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#fbe9f4', 'borderRadius': '10px', 'flex': '1'}),

                html.Div([
                    html.H4('平均消费金额', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'¥{avg_monetary:,.0f}', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#F18F01'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#fff4e6', 'borderRadius': '10px', 'flex': '1'}),

                html.Div([
                    html.H4('平均购买频次', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{avg_frequency}次', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#27ae60'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e8f8f0', 'borderRadius': '10px', 'flex': '1'}),

                html.Div([
                    html.H4('聚类数', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{cluster_info.get("n_clusters", 0)}组', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#8e44ad'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f3eafb', 'borderRadius': '10px', 'flex': '1'}),

                html.Div([
                    html.H4('轮廓系数', style={'color': '#666', 'fontSize': '14px'}),
                    html.P(f'{silhouette_display}', style={'fontSize': '28px', 'fontWeight': 'bold', 'color': '#16a085'})
                ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e6f8f6', 'borderRadius': '10px', 'flex': '1'})
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(150px, 1fr))', 'gap': '15px'})
        ], style={
            'backgroundColor': 'white', 'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '25px', 'margin': '20px'
        })
    ]

    if is_simulated:
        children.insert(0, html.Div([
            html.Div([
                html.Strong('⚠️ 数据提示: ', style={'color': '#e67e22'}),
                html.Span('上传数据未检测到客户标识字段，当前使用的是系统自动生成的模拟交易数据进行演示分析。',
                          style={'color': '#d35400'})
            ], style={
                'padding': '12px 20px',
                'backgroundColor': '#fff5e6',
                'borderLeft': '4px solid #e67e22',
                'borderRadius': '5px',
                'fontSize': '14px'
            })
        ], style={'margin': '0 20px 10px 20px'}))

    children.append(html.Div([
        html.Button(
            '📥 导出客户分群结果为 CSV',
            id='btn-export-customer-csv',
            n_clicks=0,
            style={
                'padding': '12px 30px',
                'backgroundColor': '#27ae60',
                'color': 'white',
                'border': 'none',
                'borderRadius': '6px',
                'fontSize': '14px',
                'fontWeight': 'bold',
                'cursor': 'pointer',
                'boxShadow': '0 2px 6px rgba(39, 174, 96, 0.4)'
            }
        )
    ], style={'textAlign': 'right', 'marginTop': '15px'}))

    return html.Div(children)


def create_scatter_plot(analysis_result, x_col, y_col):
    if analysis_result is None or not analysis_result.get('success'):
        return {
            'data': [],
            'layout': {
                'title': {'text': '暂无数据', 'x': 0.5},
                'xaxis': {'visible': False},
                'yaxis': {'visible': False}}}

    clustered = analysis_result.get('clustered_data')
    if clustered is None or clustered.empty:
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    fig = go.Figure()

    x_label = COL_NAME_MAP.get(x_col, x_col)
    y_label = COL_NAME_MAP.get(y_col, y_col)

    clusters = sorted(clustered['Cluster'].unique())
    for i, cid in enumerate(clusters):
        cluster_data = clustered[clustered['Cluster'] == cid]
        name = cluster_data['聚类名称'].iloc[0] if '聚类名称' in cluster_data.columns else f'集群 {cid}'
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]

        fig.add_trace(go.Scatter(
            x=cluster_data[x_col],
            y=cluster_data[y_col],
            mode='markers',
            name=name,
            marker=dict(
                size=8,
                color=color,
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=[f"客户ID: {row['客户ID']}<br>{x_label}: {row[x_col]}<br>{y_label}: {row[y_col]}"
                  for _, row in cluster_data.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))

    fig.update_layout(
        title=f'客户分群散点图 ({x_label} vs {y_label})',
        xaxis_title=x_label,
        yaxis_title=y_label,
        plot_bgcolor='white',
        legend_title='客户群体',
        hovermode='closest',
        title_x=0.5,
        font=dict(size=12)
    )

    return fig


def create_heatmap(analysis_result):
    if analysis_result is None or not analysis_result.get('success'):
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    profiles = analysis_result.get('cluster_profiles', [])
    if not profiles:
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    metrics = ['平均最近购买天数', '平均购买频次', '平均消费总额', '平均客单价']
    if profiles and profiles[0].get('复购率(%)'):
        metrics.append('复购率(%)')

    profile_key_map = {
        '平均最近购买天数': '平均Recency(天)',
        '平均购买频次': '平均购买频次',
        '平均消费总额': '平均消费总额',
        '平均客单价': '平均客单价',
        '复购率(%)': '复购率(%)'
    }

    z = []
    x_labels = metrics
    y_labels = []

    for p in profiles:
        y_labels.append(p['聚类名称'])
        row = []
        for m in metrics:
            key = profile_key_map.get(m, m)
            row.append(p.get(key, 0))
        z.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        colorscale='Blues',
        showscale=True,
        text=[[f'{v:.2f}' for v in row] for row in z],
        texttemplate='%{text}',
        textfont=dict(size=12)
    ))

    fig.update_layout(
        title='各客户群体特征热力图',
        xaxis_title='指标',
        yaxis_title='客户群体',
        plot_bgcolor='white',
        title_x=0.5,
        font=dict(size=12)
    )

    return fig


def create_radar_chart(analysis_result):
    if analysis_result is None or not analysis_result.get('success'):
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    profiles = analysis_result.get('cluster_profiles', [])
    if not profiles:
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    fig = go.Figure()

    metrics = ['R均值', 'F均值', 'M均值']
    metric_labels = ['最近购买 (R)', '购买频次 (F)', '消费金额 (M)']

    for i, p in enumerate(profiles):
        values = [p.get(m, 0) for m in metrics]
        values.append(values[0])
        labels = metric_labels.copy()
        labels.append(labels[0])
        color = CLUSTER_COLORS[i % len(CLUSTER_COLORS)]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=p['聚类名称'],
            line=dict(color=color, width=2),
            fillcolor=f'rgba{tuple(int(color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4)) + (0.2,)}',
            marker=dict(size=6)
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], title='得分'),
            angularaxis=dict(tickfont=dict(size=12))
        ),
        title='各群体 RFM 雷达图对比',
        showlegend=True,
        legend_title='客户群体',
        title_x=0.5,
        plot_bgcolor='white',
        font=dict(size=12)
    )

    return fig


def create_segment_pie_chart(analysis_result):
    if analysis_result is None or not analysis_result.get('success'):
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    segments = analysis_result.get('segment_distribution', [])
    if not segments:
        return {
            'data': [],
            'layout': {'title': {'text': '暂无数据', 'x': 0.5}}}

    labels = [s['客户分群'] for s in segments]
    values = [s['客户数量'] for s in segments]
    pcts = [s['占比(%)'] for s in segments]

    pie_colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#27ae60', '#8e44ad', '#16a085', '#e67e22']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='label+percent',
        marker=dict(colors=pie_colors[:len(labels)], line=dict(color='white', width=2)),
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>客户数量: %{value} 人<br>占比: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title='RFM 八分群客户分布',
        showlegend=True,
        legend_title='客户分群',
        title_x=0.5,
        plot_bgcolor='white',
        font=dict(size=12),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def build_visualization_content(analysis_result, x_col, y_col):
    if analysis_result is None or not analysis_result.get('success'):
        return html.Div()

    return html.Div([
        html.Div([
            html.Div([
                html.H3('客户分群散点图', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='customer-scatter-plot', figure=create_scatter_plot(analysis_result, x_col, y_col))
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            }),

            html.Div([
                html.H3('RFM 八分群客户分布', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='customer-segment-pie', figure=create_segment_pie_chart(analysis_result))
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '0'}),

        html.Div([
            html.Div([
                html.H3('群体特征热力图', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='customer-heatmap', figure=create_heatmap(analysis_result))
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            }),

            html.Div([
                html.H3('RFM 雷达图对比', style={'color': '#333', 'marginBottom': '15px'}),
                dcc.Graph(id='customer-radar-chart', figure=create_radar_chart(analysis_result))
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '0'})
    ])


def _get_cluster_color(cluster_idx):
    return CLUSTER_COLORS[int(cluster_idx) % len(CLUSTER_COLORS)]


def build_profile_cards(analysis_result):
    if analysis_result is None or not analysis_result.get('success'):
        return html.Div()

    profiles = analysis_result.get('cluster_profiles', [])
    if not profiles:
        return html.Div()

    cards = []
    for i, p in enumerate(profiles):
        color = _get_cluster_color(p['Cluster'])
        border_color = {'borderTop': f'5px solid {color}'}

        typical_cust = p.get('典型客户', [])
        typical_str = '、'.join(typical_cust) if typical_cust else '暂无'

        prefs = p.get('偏好品类', [])
        pref_str = '、'.join(prefs) if prefs else '暂无'

        regions = p.get('主要地区', [])
        region_str = '、'.join(regions) if regions else '暂无'

        repurchase = p.get('复购率(%)', 'N/A')
        repurchase_str = f'{repurchase}%' if isinstance(repurchase, (int, float)) else str(repurchase)

        cards.append(html.Div([
            html.Div([
                html.H4(p['聚类名称'], style={
                    'color': 'white', 'margin': 0, 'fontSize': '16px',
                    'textAlign': 'center'
                })
            ], style={
                'backgroundColor': color, 'padding': '15px',
                'borderTopLeftRadius': '8px', 'borderTopRightRadius': '8px'
            }),
            html.Div([
                html.Div([
                    html.Div(f'{p["客户数量"]}人', style={
                        'fontSize': '24px', 'fontWeight': 'bold', 'color': color
                    }),
                    html.Div(f'占比 {p["客户占比(%)"]}%', style={
                        'fontSize': '12px', 'color': '#666'
                    })
                ], style={'textAlign': 'center', 'padding': '10px'}),

                html.Hr(style={'margin': '10px 0', 'border': 'none', 'borderTop': '1px solid #eee'}),

                html.Div([
                    html.Div([
                        html.Span('平均购买频次', style={'color': '#666', 'fontSize': '12px', 'display': 'block'}),
                        html.Strong(f'{p["平均购买频次"]}次', style={'color': '#333', 'fontSize': '14px'})
                    ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'}),
                    html.Div([
                        html.Span('平均客单价', style={'color': '#666', 'fontSize': '12px', 'display': 'block'}),
                        html.Strong(f'¥{p["平均客单价"]:,.0f}', style={'color': '#333', 'fontSize': '14px'})
                    ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'})
                ], style={'display': 'flex', 'marginBottom': '8px'}),

                html.Div([
                    html.Div([
                        html.Span('平均消费总额', style={'color': '#666', 'fontSize': '12px', 'display': 'block'}),
                        html.Strong(f'¥{p["平均消费总额"]:,.0f}', style={'color': '#333', 'fontSize': '14px'})
                    ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'}),
                    html.Div([
                        html.Span('复购率', style={'color': '#666', 'fontSize': '12px', 'display': 'block'}),
                        html.Strong(repurchase_str, style={'color': '#333', 'fontSize': '14px'})
                    ], style={'flex': '1', 'textAlign': 'center', 'padding': '5px'})
                ], style={'display': 'flex', 'marginBottom': '10px'}),

                html.Div([
                    html.Div('偏好品类:', style={'color': '#666', 'fontSize': '12px', 'fontWeight': 'bold'}),
                    html.Div(pref_str, style={'color': '#333', 'fontSize': '12px', 'marginTop': '3px'})
                ], style={'padding': '5px 0'}),

                html.Div([
                    html.Div('主要地区:', style={'color': '#666', 'fontSize': '12px', 'fontWeight': 'bold'}),
                    html.Div(region_str, style={'color': '#333', 'fontSize': '12px', 'marginTop': '3px'})
                ], style={'padding': '5px 0'}),

                html.Div([
                    html.Div('典型客户:', style={'color': '#666', 'fontSize': '12px', 'fontWeight': 'bold'}),
                    html.Div(typical_str, style={'color': '#333', 'fontSize': '12px', 'marginTop': '3px'})
                ], style={'padding': '5px 0'}),

                html.Button(
                    '查看详细特征',
                    id={'type': 'cluster-detail-btn', 'index': str(p['Cluster'])},
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'marginTop': '12px',
                        'padding': '8px 15px',
                        'backgroundColor': color,
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'fontSize': '13px',
                        'fontWeight': 'bold',
                        'cursor': 'pointer'
                    }
                )
            ], style={'padding': '15px'})
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'overflow': 'hidden',
            **border_color
        }))

    return html.Div([
        html.H3('客户画像卡片', style={'color': '#333', 'marginBottom': '20px', 'marginLeft': '20px', 'marginTop': '20px'}),
        html.Div(cards, style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(280px, 1fr))',
            'gap': '20px',
            'padding': '0 20px 20px 20px'
        })
    ])


def build_cluster_detail(analysis_result, cluster_id):
    if analysis_result is None or not analysis_result.get('success'):
        return html.Div()

    if cluster_id is None:
        return html.Div([
            html.Div([
                html.H3('💡 点击上方"查看详细特征"按钮查看特定客户群体的详细行为统计', style={
                    'color': '#666', 'textAlign': 'center',
                    'padding': '30px', 'fontSize': '15px'
                })
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px'
            })
        ])

    profiles = analysis_result.get('cluster_profiles', [])
    target = next((p for p in profiles if str(p['Cluster']) == str(cluster_id)), None)
    if not target:
        return html.Div()

    color = _get_cluster_color(target['Cluster'])

    detail_rows = [
        {'指标': '客户群体名称', '数值': target['聚类名称']},
        {'指标': '客户数量', '数值': f"{target['客户数量']} 人"},
        {'指标': '客户占比', '数值': f"{target['客户占比(%)']}%"},
        {'指标': '平均最近购买天数', '数值': f"{target['平均Recency(天)']} 天"},
        {'指标': '平均购买频次', '数值': f"{target['平均购买频次']} 次"},
        {'指标': '平均消费总额', '数值': f"¥{target['平均消费总额']:,.2f}"},
        {'指标': '平均客单价', '数值': f"¥{target['平均客单价']:,.2f}"}
    ]

    if target.get('复购率(%)') is not None:
        detail_rows.append({'指标': '复购率', '数值': f"{target['复购率(%)']}%"})
    if target.get('总订单数'):
        detail_rows.append({'指标': '总订单数', '数值': f"{target['总订单数']} 笔"})
    if target.get('总销售额'):
        detail_rows.append({'指标': '群体总销售额', '数值': f"¥{target['总销售额']:,.2f}"})
    if target.get('R均值'):
        detail_rows.append({'指标': 'R 得分均值', '数值': f"{target['R均值']:.2f} / 5.0"})
    if target.get('F均值'):
        detail_rows.append({'指标': 'F 得分均值', '数值': f"{target['F均值']:.2f} / 5.0"})
    if target.get('M均值'):
        detail_rows.append({'指标': 'M 得分均值', '数值': f"{target['M均值']:.2f} / 5.0"})

    children = []

    children.append(html.Div([
        html.Div([
            html.H3(f"📊 {target['聚类名称']} - 详细行为特征", style={
                'color': 'white', 'margin': 0
            })
        ], style={
            'backgroundColor': color,
            'padding': '15px 20px',
            'borderTopLeftRadius': '10px',
            'borderTopRightRadius': '10px'
        }),
        html.Div([
            dash_table.DataTable(
                data=detail_rows,
                columns=[
                    {'name': '分析指标', 'id': '指标'},
                    {'name': '统计结果', 'id': '数值'}
                ],
                style_cell={'padding': '12px 15px', 'textAlign': 'left', 'fontSize': '14px'},
                style_header={
                    'backgroundColor': '#f0f0f0',
                    'fontWeight': 'bold',
                    'fontSize': '14px',
                    'textAlign': 'center'
                },
                style_table={'overflowX': 'auto'}
            )
        ], style={'padding': '20px'})
    ], style={
        'backgroundColor': 'white', 'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'margin': '20px',
        'overflow': 'hidden'
    }))

    extra_info = []
    if target.get('偏好品类'):
        extra_info.append(html.Div([
            html.Strong('🛒 偏好品类: ', style={'color': color, 'fontSize': '14px'}),
            html.Span('、'.join(target['偏好品类']), style={'color': '#333', 'fontSize': '14px'})
        ], style={'padding': '8px 0'}))
    if target.get('主要地区'):
        extra_info.append(html.Div([
            html.Strong('📍 主要地区: ', style={'color': color, 'fontSize': '14px'}),
            html.Span('、'.join(target['主要地区']), style={'color': '#333', 'fontSize': '14px'})
        ], style={'padding': '8px 0'}))
    if target.get('典型客户'):
        extra_info.append(html.Div([
            html.Strong('👤 典型客户ID: ', style={'color': color, 'fontSize': '14px'}),
            html.Span('、'.join(target['典型客户']), style={'color': '#333', 'fontSize': '14px'})
        ], style={'padding': '8px 0'}))

    if extra_info:
        children.append(html.Div([
            html.H4('补充信息', style={'color': '#333', 'marginBottom': '10px', 'fontSize': '15px'}),
            html.Div(extra_info)
        ], style={
            'backgroundColor': '#fafafa',
            'borderRadius': '8px',
            'padding': '15px 20px',
            'margin': '0 20px 20px 20px'
        }))

    rfm_scores = []
    if target.get('R均值'):
        rfm_scores.append({'维度': '最近购买 (R)', '得分': round(target['R均值'] * 20, 1), '满分': 100})
    if target.get('F均值'):
        rfm_scores.append({'维度': '购买频次 (F)', '得分': round(target['F均值'] * 20, 1), '满分': 100})
    if target.get('M均值'):
        rfm_scores.append({'维度': '消费金额 (M)', '得分': round(target['M均值'] * 20, 1), '满分': 100})

    if rfm_scores:
        rfm_bars = []
        for s in rfm_scores:
            rfm_bars.append(html.Div([
                html.Div([
                    html.Span(s['维度'], style={'display': 'inline-block', 'width': '180px', 'color': '#666', 'fontSize': '13px'}),
                    html.Div([
                        html.Div(style={
                            'width': f"{s['得分']}%",
                            'height': '22px',
                            'backgroundColor': color,
                            'borderRadius': '4px',
                            'display': 'inline-block'
                        })
                    ], style={
                        'display': 'inline-block',
                        'width': '200px',
                        'backgroundColor': '#f0f0f0',
                        'borderRadius': '4px',
                        'height': '22px',
                        'overflow': 'hidden',
                        'verticalAlign': 'middle'
                    }),
                    html.Span(f" {s['得分']:.1f}/100", style={'fontWeight': 'bold', 'color': '#333', 'marginLeft': '10px', 'fontSize': '13px'})
                ], style={'marginBottom': '12px'})
            ]))

        children.append(html.Div([
            html.H4('RFM 维度得分', style={'color': '#333', 'marginBottom': '15px', 'fontSize': '15px'}),
            html.Div(rfm_bars)
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'padding': '20px 25px',
            'margin': '20px'
        }))

    return html.Div(children)


@callback(
    Output('customer-config-container', 'children'),
    Input('stored-data', 'data')
)
def render_customer_config(df_json):
    if df_json is None:
        return html.Div()
    return build_customer_config_content(df_json)


@callback(
    Output('customer-analysis-store', 'data'),
    Output('customer-summary-container', 'children'),
    Output('customer-visualization-container', 'children'),
    Output('customer-profiles-container', 'children'),
    Output('customer-detail-container', 'children'),
    Input('btn-run-customer-analysis', 'n_clicks'),
    State('stored-data', 'data'),
    State('cluster-count-slider', 'value'),
    State('scatter-x-axis', 'value'),
    State('scatter-y-axis', 'value'),
    prevent_initial_call=True
)
def run_analysis(n_clicks, df_json, n_clusters, x_col, y_col):
    if n_clicks is None or n_clicks == 0:
        return None, html.Div(), html.Div(), html.Div(), build_cluster_detail(None, None)

    if df_json is None:
        error_div = html.Div([
            html.Div('⚠️ 请先上传有效数据', style={
                'color': '#e74c3c', 'padding': '20px',
                'backgroundColor': '#fdecea', 'borderRadius': '8px',
                'textAlign': 'center'
            })
        ])
        return None, error_div, html.Div(), html.Div(), html.Div()

    df = pd.read_json(df_json, orient='split')

    try:
        result = run_customer_analysis(df, n_clusters=n_clusters)
        if not result.get('success'):
            error_msg = result.get('error', '分析失败')
            error_div = html.Div([
                html.Div(f'❌ {error_msg}', style={
                    'color': '#e74c3c', 'padding': '20px',
                    'backgroundColor': '#fdecea', 'borderRadius': '8px',
                    'textAlign': 'center'
                })
            ])
            return None, error_div, html.Div(), html.Div(), html.Div()

        serializable = {
            'success': True,
            'is_simulated': result.get('is_simulated', False),
            'cluster_profiles': result.get('cluster_profiles', []),
            'cluster_info': result.get('cluster_info', {}),
            'segment_distribution': result.get('segment_distribution', []),
            'total_customers': result.get('total_customers', 0),
            'total_transactions': result.get('total_transactions', 0),
            'clustered_data_json': result.get('clustered_data').to_json(orient='split') if result.get('clustered_data') is not None else None,
            'rfm_data_json': result.get('rfm_data').to_json(orient='split') if result.get('rfm_data') is not None else None
        }

        summary = build_customer_summary(result)
        viz = build_visualization_content(result, x_col, y_col)
        profiles = build_profile_cards(result)
        detail = build_cluster_detail(result, None)

        return serializable, summary, viz, profiles, detail
    except Exception as e:
        error_div = html.Div([
            html.Div(f'❌ 分析失败: {str(e)}', style={
                'color': '#e74c3c', 'padding': '20px',
                'backgroundColor': '#fdecea', 'borderRadius': '8px',
                'textAlign': 'center'
            })
        ])
        return None, error_div, html.Div(), html.Div(), html.Div()


@callback(
    Output('customer-scatter-plot', 'figure', allow_duplicate=True),
    Input('scatter-x-axis', 'value'),
    Input('scatter-y-axis', 'value'),
    State('customer-analysis-store', 'data'),
    prevent_initial_call=True
)
def update_scatter(x_col, y_col, stored):
    if not stored or not stored.get('success'):
        return dash.no_update

    clustered_json = stored.get('clustered_data_json')
    if not clustered_json:
        return dash.no_update

    try:
        clustered = pd.read_json(clustered_json, orient='split')
        temp_result = {
            'success': True,
            'clustered_data': clustered
        }
        return create_scatter_plot(temp_result, x_col, y_col)
    except Exception:
        return dash.no_update


@callback(
    Output('customer-detail-container', 'children', allow_duplicate=True),
    Input({'type': 'cluster-detail-btn', 'index': dash.ALL}, 'n_clicks'),
    State('customer-analysis-store', 'data'),
    prevent_initial_call=True
)
def show_cluster_detail(n_clicks_list, stored):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trigger = ctx.triggered[0]
    if trigger['value'] is None or trigger['value'] == 0:
        return dash.no_update

    prop_id = trigger['prop_id']
    try:
        import json as _json
        idx_dict = _json.loads(prop_id.split('.')[0])
        cluster_id = idx_dict.get('index')
    except Exception:
        return dash.no_update

    if not stored or not stored.get('success'):
        return dash.no_update

    clustered_json = stored.get('clustered_data_json')
    rfm_json = stored.get('rfm_data_json')
    if not clustered_json:
        return dash.no_update

    try:
        clustered = pd.read_json(clustered_json, orient='split')
        rfm = pd.read_json(rfm_json, orient='split') if rfm_json else pd.DataFrame()
        profiles = stored.get('cluster_profiles', [])
        temp_result = {
            'success': True,
            'clustered_data': clustered,
            'rfm_data': rfm,
            'cluster_profiles': profiles
        }
        return build_cluster_detail(temp_result, cluster_id)
    except Exception:
        return dash.no_update


@callback(
    Output('download-customer-csv', 'data'),
    Input('btn-export-customer-csv', 'n_clicks'),
    State('customer-analysis-store', 'data'),
    prevent_initial_call=True
)
def export_csv(n_clicks, stored):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    if not stored or not stored.get('success'):
        return dash.no_update

    clustered_json = stored.get('clustered_data_json')
    if not clustered_json:
        return dash.no_update

    try:
        clustered = pd.read_json(clustered_json, orient='split')
        csv_str = clustered.to_csv(index=False, encoding='utf-8-sig')
        return dict(content=csv_str, filename='客户分群结果.csv', type='text/csv')
    except Exception:
        return dash.no_update


if __name__ == '__main__':
    app.run(debug=True, port=4050)
