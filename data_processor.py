import pandas as pd
import numpy as np
import base64
import io
import calendar
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional


REQUIRED_COLUMNS = ['期间', '销售额', '类型']

TIME_PERIOD_KEYWORDS = ['促销前', '促销期间', '促销后', '非促销期间', '预热期', '爆发期', '衰退期', '日常销售']

ACTIVITY_COLORS = [
    '#2E86AB', '#A23B72', '#F18F01', '#C73E1D',
    '#3B1F2B', '#6A994E', '#577590', '#F94144'
]

DTYPE_CN_MAP = {
    'int64': '整数型 (64位)',
    'int32': '整数型 (32位)',
    'int': '整数型',
    'float64': '浮点型 (64位)',
    'float32': '浮点型 (32位)',
    'float': '浮点型',
    'object': '文本型',
    'string': '字符串型',
    'bool': '布尔型',
    'datetime64': '日期时间型',
    'datetime64[ns]': '日期时间型',
    'category': '分类型'
}


def dtype_to_cn(dtype_str: str) -> str:
    return DTYPE_CN_MAP.get(dtype_str, dtype_str)


def parse_uploaded_file(contents: str, filename: str) -> Tuple[Optional[pd.DataFrame], List[str]]:
    errors: List[str] = []
    df: Optional[pd.DataFrame] = None

    if contents is None:
        errors.append('未选择文件')
        return df, errors

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            errors.append('不支持的文件格式，请上传 CSV 或 Excel 文件')
            return df, errors
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('gbk')))
        except Exception as e:
            errors.append(f'文件编码错误，请尝试 UTF-8 或 GBK 编码: {str(e)}')
            return df, errors
    except Exception as e:
        errors.append(f'文件解析失败: {str(e)}')
        return df, errors

    if df is not None and df.empty:
        errors.append('文件中没有数据')

    return df, errors


def validate_columns(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    actual_columns = list(df.columns)

    for col in REQUIRED_COLUMNS:
        if col not in actual_columns:
            errors.append(f'缺少必要列: "{col}"')

    return errors


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['', 'nan', 'NaN', 'None', 'NULL'], np.nan)

    if '销售额' in df.columns:
        df['销售额'] = pd.to_numeric(df['销售额'], errors='coerce')

    if '期间' in df.columns:
        df['期间'] = df['期间'].astype(str).str.strip()

    if '类型' in df.columns:
        df['类型'] = df['类型'].astype(str).str.strip()

    df = df.dropna(how='all')
    df = df.reset_index(drop=True)

    return df


def detect_outliers_iqr(series: pd.Series) -> pd.Series:
    if series.dtype not in ['int64', 'float64']:
        return pd.Series([False] * len(series), index=series.index)

    s = series.dropna()
    if len(s) < 4:
        return pd.Series([False] * len(series), index=series.index)

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1

    if iqr == 0:
        return pd.Series([False] * len(series), index=series.index)

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return (series < lower_bound) | (series > upper_bound)


def generate_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    report: Dict[str, Any] = {}

    report['total_rows'] = len(df)
    report['total_columns'] = len(df.columns)

    missing_stats = {}
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df) * 100) if len(df) > 0 else 0
        missing_stats[col] = {
            'count': int(missing_count),
            'percentage': round(missing_pct, 2)
        }
    report['missing_stats'] = missing_stats

    dtype_info = {}
    for col in df.columns:
        dtype_info[col] = dtype_to_cn(str(df[col].dtype))
    report['dtype_info'] = dtype_info

    outlier_info: Dict[str, Any] = {}
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            outlier_mask = detect_outliers_iqr(df[col])
            outlier_indices = df[outlier_mask].index.tolist()
            if len(outlier_indices) > 0:
                outlier_values = df.loc[outlier_indices, col].tolist()
                outlier_info[col] = {
                    'count': len(outlier_indices),
                    'indices': [int(i) for i in outlier_indices[:10]],
                    'values': [round(float(v), 2) if not pd.isna(v) else None for v in outlier_values[:10]]
                }
    report['outlier_info'] = outlier_info

    report['is_valid'] = True
    validation_errors: List[str] = []

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            report['is_valid'] = False
            validation_errors.append(f'缺少必要列: "{col}"')

    if len(df) < 3:
        report['is_valid'] = False
        validation_errors.append('数据行数不足，至少需要 3 行数据')

    if '销售额' in df.columns:
        if df['销售额'].isna().all():
            report['is_valid'] = False
            validation_errors.append('"销售额"列全部为空')
        if df['销售额'].dtype not in ['int64', 'float64']:
            report['is_valid'] = False
            validation_errors.append('"销售额"列无法转换为数值类型')

    if '类型' in df.columns:
        unique_types = df['类型'].dropna().unique().tolist()
        if len(unique_types) < 2:
            report['is_valid'] = False
            validation_errors.append('"类型"列至少需要 2 种不同的分类值')

    report['validation_errors'] = validation_errors

    return report


def process_uploaded_data(contents: str, filename: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        'success': False,
        'df': None,
        'preview': None,
        'quality_report': None,
        'errors': []
    }

    df, parse_errors = parse_uploaded_file(contents, filename)
    if parse_errors:
        result['errors'].extend(parse_errors)
        return result

    if df is None:
        result['errors'].append('数据解析失败')
        return result

    col_errors = validate_columns(df)
    if col_errors:
        result['errors'].extend(col_errors)
        result['df'] = df
        result['preview'] = df.head(10).copy()
        result['quality_report'] = generate_quality_report(df)
        return result

    df_cleaned = clean_data(df)
    quality_report = generate_quality_report(df_cleaned)

    result['success'] = quality_report['is_valid']
    result['df'] = df_cleaned
    result['preview'] = df_cleaned.head(10).copy()
    result['quality_report'] = quality_report
    if not quality_report['is_valid']:
        result['errors'].extend(quality_report['validation_errors'])

    return result


def try_parse_datetime(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, errors='coerce')
    except Exception:
        return pd.Series([pd.NaT] * len(series))


def aggregate_by_time_granularity(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    granularity: str = '日',
    group_col: Optional[str] = None
) -> pd.DataFrame:
    result_df = df.copy().reset_index(drop=True)
    result_df['_row_order'] = result_df.index

    is_datetime_parsed = False

    if not pd.api.types.is_datetime64_any_dtype(result_df[time_col]):
        result_df['_parsed_time'] = try_parse_datetime(result_df[time_col])
        if result_df['_parsed_time'].isna().all():
            result_df['时间'] = result_df[time_col].astype(str)
            agg_col = '时间'
            is_datetime_parsed = False
        else:
            result_df[time_col] = result_df['_parsed_time']
            is_datetime_parsed = True
    else:
        is_datetime_parsed = True

    if is_datetime_parsed:
        if granularity == '日':
            result_df['时间'] = result_df[time_col].dt.strftime('%Y-%m-%d')
        elif granularity == '周':
            result_df['时间'] = result_df[time_col].dt.strftime('%Y-W%W')
        elif granularity == '月':
            result_df['时间'] = result_df[time_col].dt.strftime('%Y-%m')
        else:
            result_df['时间'] = result_df[time_col].dt.strftime('%Y-%m-%d')
        agg_col = '时间'

    result_df['_sort_key'] = result_df['时间'] if is_datetime_parsed else result_df['_row_order']

    if group_col and group_col in result_df.columns:
        order_df = result_df.groupby([agg_col, group_col], as_index=False)['_sort_key'].min()
        agg_df = result_df.groupby([agg_col, group_col], as_index=False)[value_col].sum()
        agg_df = agg_df.merge(order_df, on=[agg_col, group_col])
    else:
        order_df = result_df.groupby([agg_col], as_index=False)['_sort_key'].min()
        agg_df = result_df.groupby([agg_col], as_index=False)[value_col].sum()
        agg_df = agg_df.merge(order_df, on=[agg_col])

    if is_datetime_parsed:
        agg_df = agg_df.sort_values('_sort_key').reset_index(drop=True)
    else:
        agg_df = agg_df.sort_values('_sort_key').reset_index(drop=True)

    agg_df = agg_df.drop(columns=['_sort_key'])

    return agg_df


def calculate_growth_rate(df: pd.DataFrame, value_col: str = '销售额') -> Dict[str, Any]:
    result: Dict[str, Any] = {
        'total_growth_rate': None,
        'period_growth_rates': [],
        'avg_growth_rate': None,
        'trend': 'stable'
    }

    if len(df) < 2:
        return result

    sorted_df = df.reset_index(drop=True)
    values = sorted_df[value_col].values

    total_first = values[0]
    total_last = values[-1]
    if total_first > 0:
        result['total_growth_rate'] = round((total_last - total_first) / total_first * 100, 2)

    period_rates = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            rate = round((values[i] - values[i - 1]) / values[i - 1] * 100, 2)
            period_rates.append({
                'period': f"{sorted_df['时间'].iloc[i-1]} → {sorted_df['时间'].iloc[i]}",
                'rate': rate
            })

    result['period_growth_rates'] = period_rates
    if period_rates:
        result['avg_growth_rate'] = round(
            sum(r['rate'] for r in period_rates) / len(period_rates), 2
        )
        if result['avg_growth_rate'] > 5:
            result['trend'] = 'up'
        elif result['avg_growth_rate'] < -5:
            result['trend'] = 'down'
        else:
            result['trend'] = 'stable'

    return result


def detect_seasonality(df: pd.DataFrame, value_col: str = '销售额') -> Dict[str, Any]:
    result: Dict[str, Any] = {
        'has_seasonality': False,
        'seasonal_pattern': None,
        'peak_periods': [],
        'low_periods': []
    }

    if len(df) < 4:
        return result

    sorted_df = df.reset_index(drop=True)
    values = sorted_df[value_col].values
    times = sorted_df['时间'].values

    mean_val = values.mean()
    std_val = values.std() if len(values) > 1 else 0

    if std_val == 0:
        return result

    cv = std_val / mean_val if mean_val != 0 else 0

    if cv > 0.3:
        result['has_seasonality'] = True

        peak_indices = [i for i, v in enumerate(values) if v > mean_val + std_val]
        low_indices = [i for i, v in enumerate(values) if v < mean_val - std_val]

        result['peak_periods'] = [str(times[i]) for i in peak_indices]
        result['low_periods'] = [str(times[i]) for i in low_indices]

        if peak_indices and low_indices:
            if len(peak_indices) >= 2 and len(low_indices) >= 2:
                result['seasonal_pattern'] = '存在明显的周期性波动模式'
            else:
                result['seasonal_pattern'] = '存在部分季节性特征'
        elif peak_indices:
            result['seasonal_pattern'] = '存在旺季特征'
        elif low_indices:
            result['seasonal_pattern'] = '存在淡季特征'

    return result


def detect_anomalies(df: pd.DataFrame, value_col: str = '销售额') -> List[Dict[str, Any]]:
    anomalies = []

    if len(df) < 4:
        return anomalies

    sorted_df = df.reset_index(drop=True)
    values = sorted_df[value_col].values
    times = sorted_df['时间'].values

    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1

    if iqr == 0:
        return anomalies

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    for i, v in enumerate(values):
        if v < lower_bound:
            anomalies.append({
                'time': str(times[i]),
                'value': float(v),
                'type': '偏低异常',
                'deviation': round((v - np.mean(values)) / np.mean(values) * 100, 2) if np.mean(values) != 0 else 0
            })
        elif v > upper_bound:
            anomalies.append({
                'time': str(times[i]),
                'value': float(v),
                'type': '偏高异常',
                'deviation': round((v - np.mean(values)) / np.mean(values) * 100, 2) if np.mean(values) != 0 else 0
            })

    return anomalies


def get_available_dimensions(df: pd.DataFrame) -> Dict[str, List[str]]:
    dimensions: Dict[str, List[str]] = {}

    if '产品类别' in df.columns:
        categories = df['产品类别'].dropna().unique().tolist()
        dimensions['产品类别'] = [str(c) for c in categories]
    elif '类别' in df.columns:
        categories = df['类别'].dropna().unique().tolist()
        dimensions['产品类别'] = [str(c) for c in categories]

    if '地区' in df.columns:
        regions = df['地区'].dropna().unique().tolist()
        dimensions['地区'] = [str(r) for r in regions]
    elif '区域' in df.columns:
        regions = df['区域'].dropna().unique().tolist()
        dimensions['地区'] = [str(r) for r in regions]

    if '类型' in df.columns:
        types = df['类型'].dropna().unique().tolist()
        dimensions['类型'] = [str(t) for t in types]

    return dimensions


def filter_data(
    df: pd.DataFrame,
    categories: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    types: Optional[List[str]] = None
) -> pd.DataFrame:
    result = df.copy()

    if categories:
        cat_col = '产品类别' if '产品类别' in result.columns else ('类别' if '类别' in result.columns else None)
        if cat_col:
            result = result[result[cat_col].astype(str).isin(categories)]

    if regions:
        reg_col = '地区' if '地区' in result.columns else ('区域' if '区域' in result.columns else None)
        if reg_col:
            result = result[result[reg_col].astype(str).isin(regions)]

    if types and '类型' in result.columns:
        result = result[result['类型'].astype(str).isin(types)]

    return result


def _is_time_period_label(label: str) -> bool:
    for kw in TIME_PERIOD_KEYWORDS:
        if kw in str(label):
            return True
    return False


def get_activity_name_column(df: pd.DataFrame) -> Optional[str]:
    activity_col_candidates = ['活动名称', '活动', '活动名', 'campaign', 'Campaign', '活动编号']
    for col in activity_col_candidates:
        if col in df.columns:
            return col
    return None


def extract_activity_dates(df: pd.DataFrame) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        'date_activity_map': {},
        'activity_dates': {},
        'activity_colors': {},
        'activity_sales': {},
        'available': False
    }

    if df is None or len(df) == 0:
        return result

    time_col = '期间' if '期间' in df.columns else None
    if time_col is None:
        return result

    df_copy = df.copy()
    parsed_dates = try_parse_datetime(df_copy[time_col])
    if parsed_dates.isna().all():
        return result
    df_copy['_parsed_date'] = parsed_dates
    df_copy = df_copy.dropna(subset=['_parsed_date'])

    if len(df_copy) == 0:
        return result

    activity_col = get_activity_name_column(df_copy)

    if activity_col:
        activities = df_copy[activity_col].dropna().unique().tolist()
        activities = [str(a) for a in activities if str(a).strip()]
    elif '类型' in df_copy.columns:
        types = df_copy['类型'].dropna().unique().tolist()
        activities = [str(t) for t in types if not _is_time_period_label(str(t)) and str(t).strip()]
        if not activities:
            activities = [str(t) for t in types if str(t).strip() and str(t) != '非促销期间']
        activity_col = '类型'
    else:
        return result

    if not activities:
        return result

    for idx, activity in enumerate(activities):
        result['activity_colors'][activity] = ACTIVITY_COLORS[idx % len(ACTIVITY_COLORS)]
        result['activity_dates'][activity] = []
        result['activity_sales'][activity] = 0.0

    for _, row in df_copy.iterrows():
        activity_val = str(row.get(activity_col, '')) if activity_col else ''
        if activity_val not in result['activity_dates']:
            continue
        date_val = row['_parsed_date']
        date_str = date_val.strftime('%Y-%m-%d')
        if date_str not in result['date_activity_map']:
            result['date_activity_map'][date_str] = []
        if activity_val not in result['date_activity_map'][date_str]:
            result['date_activity_map'][date_str].append(activity_val)
        if date_str not in result['activity_dates'][activity_val]:
            result['activity_dates'][activity_val].append(date_str)
        sales_val = row.get('销售额', 0)
        if pd.notna(sales_val):
            result['activity_sales'][activity_val] += float(sales_val)

    for activity in activities:
        result['activity_dates'][activity].sort()

    result['available'] = True
    return result


def get_monthly_activity_stats(
    activity_data: Dict[str, Any],
    year: int,
    month: int
) -> Dict[str, Any]:
    stats: Dict[str, Any] = {
        'activity_count': 0,
        'activity_names': [],
        'avg_sales': 0.0,
        'total_sales': 0.0,
        'active_days': 0,
        'details': []
    }

    if not activity_data.get('available', False):
        return stats

    month_prefix = f'{year:04d}-{month:02d}'
    month_activities = set()
    month_dates = set()
    total_sales = 0.0

    for date_str, acts in activity_data.get('date_activity_map', {}).items():
        if date_str.startswith(month_prefix):
            month_dates.add(date_str)
            for act in acts:
                month_activities.add(act)

    for activity in month_activities:
        act_dates = [d for d in activity_data.get('activity_dates', {}).get(activity, []) if d.startswith(month_prefix)]
        act_sales = activity_data.get('activity_sales', {}).get(activity, 0.0)
        act_days = len(act_dates)
        avg_sale = act_sales / act_days if act_days > 0 else 0
        stats['details'].append({
            'name': activity,
            'days': act_days,
            'total_sales': round(act_sales, 2),
            'avg_daily_sales': round(avg_sale, 2),
            'color': activity_data.get('activity_colors', {}).get(activity, '#2E86AB')
        })
        total_sales += act_sales

    stats['activity_count'] = len(month_activities)
    stats['activity_names'] = sorted(list(month_activities))
    stats['active_days'] = len(month_dates)
    stats['total_sales'] = round(total_sales, 2)
    if len(month_dates) > 0:
        stats['avg_sales'] = round(total_sales / len(month_dates), 2)
    else:
        stats['avg_sales'] = 0.0

    stats['details'] = sorted(stats['details'], key=lambda x: x['total_sales'], reverse=True)

    return stats


def get_date_range(activity_data: Dict[str, Any]) -> Optional[Tuple[datetime, datetime]]:
    if not activity_data.get('available', False):
        return None

    all_dates = list(activity_data.get('date_activity_map', {}).keys())
    if not all_dates:
        return None

    sorted_dates = sorted(all_dates)
    try:
        min_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        max_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        return (min_date, max_date)
    except Exception:
        return None
