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
    evaluate_promo_activity, get_promo_activity_types
)

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='stored-data', data=None),
    dcc.Store(id='stored-quality-report', data=None),
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
            evaluation_link
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
    if pathname in ['/analysis', '/trend', '/evaluation']:
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
        else:
            return evaluation_page()
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
    activity_types = get_promo_activity_types(df)

    if not activity_types:
        return html.Div('未检测到有效的促销活动类型', style={'color': '#e74c3c'})

    children = []

    children.append(html.Div([
        html.H3('活动选择与指标权重配置', style={'color': '#333', 'marginBottom': '20px'}),
        html.Div([
            html.Label('选择促销活动', style={
                'fontWeight': 'bold', 'color': '#333',
                'marginBottom': '8px', 'display': 'block', 'fontSize': '14px'
            }),
            dcc.Dropdown(
                id='eval-activity-select',
                options=[{'label': a, 'value': a} for a in activity_types],
                value=activity_types[0],
                style={'width': '100%', 'marginBottom': '20px'}
            )
        ], style={'marginBottom': '20px'}),

        html.Div([
            html.H4('指标权重配置（总和自动归一化为100%）', style={
                'color': '#333', 'marginBottom': '15px', 'fontSize': '15px'
            }),
            html.Div([
                html.Div([
                    html.Label('ROI 权重', style={
                        'fontWeight': 'bold', 'color': '#333',
                        'marginBottom': '6px', 'display': 'block', 'fontSize': '13px'
                    }),
                    dcc.Slider(
                        id='weight-roi',
                        min=0,
                        max=100,
                        value=30,
                        marks={i: f'{i}%' for i in range(0, 101, 20)},
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
                        marks={i: f'{i}%' for i in range(0, 101, 20)},
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
                        marks={i: f'{i}%' for i in range(0, 101, 20)},
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
                        marks={i: f'{i}%' for i in range(0, 101, 20)},
                        step=5
                    )
                ], style={'flex': '1', 'minWidth': '200px', 'marginBottom': '15px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px'}),

            html.Div(id='weight-summary', style={
                'marginTop': '10px', 'padding': '10px',
                'backgroundColor': '#eaf4fb', 'borderRadius': '6px',
                'fontSize': '13px', 'color': '#2E86AB'
            })
        ])
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
    weights = eval_result['权重配置']

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
                                'display': 'inline-block', 'width': '90px',
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
                html.H3('历史活动对比', style={'color': '#333', 'marginBottom': '15px'}),
                _build_history_comparison_panel(eval_result['历史对比'])
            ], style={
                'backgroundColor': 'white', 'borderRadius': '10px',
                'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
                'padding': '20px', 'margin': '20px 10px'
            })
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '0'}),

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


def _build_history_comparison_panel(history_data):
    children = []

    children.append(html.Div([
        html.Div([
            html.Div('历史排名', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(history_data['历史排名'], style={
                'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2E86AB'
            })
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'}),

        html.Div([
            html.Div('相对历史平均', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(
                f"{history_data['相对历史平均']:+.2f}分",
                style={
                    'fontSize': '20px', 'fontWeight': 'bold',
                    'color': '#27ae60' if history_data['相对历史平均'] >= 0 else '#e74c3c'
                }
            )
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'}),

        html.Div([
            html.Div('历史最高分', style={
                'color': '#666', 'fontSize': '13px', 'marginBottom': '4px'
            }),
            html.Div(f"{history_data['历史最高分']:.2f}", style={
                'fontSize': '20px', 'fontWeight': 'bold', 'color': '#F18F01'
            })
        ], style={'textAlign': 'center', 'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'}))

    children.append(html.Div([
        html.Div(history_data['对比结论'], style={
            'padding': '12px', 'backgroundColor': '#eaf4fb',
            'borderRadius': '6px', 'color': '#2E86AB',
            'fontSize': '13px', 'lineHeight': '1.6'
        })
    ], style={'marginBottom': '15px'}))

    dim_data = history_data['维度对比']
    dim_rows = []
    for dim, info in dim_data.items():
        dim_rows.append({
            '评估维度': dim,
            '当前评分': info['当前评分'],
            '历史平均': info['历史平均'],
            '差异': f"{info['差异']:+.2f}"
        })

    children.append(html.Div([
        html.Label('各维度与历史对比', style={
            'fontWeight': 'bold', 'color': '#333',
            'fontSize': '13px', 'marginBottom': '8px', 'display': 'block'
        }),
        dash_table.DataTable(
            data=dim_rows,
            columns=[
                {'name': '评估维度', 'id': '评估维度'},
                {'name': '当前评分', 'id': '当前评分'},
                {'name': '历史平均', 'id': '历史平均'},
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


def _build_detail_tables(eval_result):
    roi = eval_result['ROI分析']
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
            _make_table(roi, '📊 ROI 投资回报分析', 'ROI等级'),
            _make_table(inc, '📈 增量销售分析', '提升等级')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}),
        html.Div([
            _make_table(cac, '👥 客户获取成本分析', '客户质量等级'),
            _make_table(margin, '💰 利润边际分析', '利润等级')
        ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'})
    ])


@callback(
    Output('eval-config-container', 'children'),
    Input('stored-data', 'data')
)
def render_eval_config(df_json):
    return build_eval_config_content(df_json)


@callback(
    Output('weight-summary', 'children'),
    Input('weight-roi', 'value'),
    Input('weight-lift', 'value'),
    Input('weight-cac', 'value'),
    Input('weight-margin', 'value')
)
def update_weight_summary(w_roi, w_lift, w_cac, w_margin):
    total = w_roi + w_lift + w_cac + w_margin
    if total == 0:
        return html.Div('⚠️ 权重总和不能为 0，请调整权重配置', style={'color': '#e74c3c'})

    n_roi = w_roi / total * 100
    n_lift = w_lift / total * 100
    n_cac = w_cac / total * 100
    n_margin = w_margin / total * 100

    return (
        f'归一化后权重 → ROI: {n_roi:.1f}% | '
        f'销售增量: {n_lift:.1f}% | '
        f'客户获取: {n_cac:.1f}% | '
        f'利润边际: {n_margin:.1f}%'
    )


@callback(
    Output('eval-results-container', 'children'),
    Input('stored-data', 'data'),
    Input('eval-activity-select', 'value'),
    Input('weight-roi', 'value'),
    Input('weight-lift', 'value'),
    Input('weight-cac', 'value'),
    Input('weight-margin', 'value')
)
def update_eval_results(df_json, activity_type, w_roi, w_lift, w_cac, w_margin):
    if df_json is None or activity_type is None:
        return html.Div()

    total = w_roi + w_lift + w_cac + w_margin
    if total == 0:
        return html.Div()

    weights = {
        'ROI': w_roi / total,
        '销售增量': w_lift / total,
        '客户获取': w_cac / total,
        '利润边际': w_margin / total
    }

    df = pd.read_json(df_json, orient='split')
    eval_result = evaluate_promo_activity(df, activity_type, weights)
    return build_eval_results_content(eval_result)


if __name__ == '__main__':
    app.run(debug=True, port=4050)
