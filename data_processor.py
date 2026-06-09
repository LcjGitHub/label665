import pandas as pd
import numpy as np
import base64
import io
from typing import Dict, List, Tuple, Any, Optional


REQUIRED_COLUMNS = ['期间', '销售额', '类型']


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
        dtype_info[col] = str(df[col].dtype)
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
