import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings

warnings.filterwarnings('ignore')


CUSTOMER_ID_CANDIDATES = ['客户ID', '客户编号', '用户ID', '用户编号', 'CustomerID', 'customer_id', '会员ID']
AMOUNT_CANDIDATES = ['销售额', '金额', '消费金额', '订单金额', 'Amount', 'amount']
TIME_CANDIDATES = ['期间', '日期', '时间', '订单日期', 'Date', 'date', '交易时间']
QUANTITY_CANDIDATES = ['数量', '购买数量', '销量', 'Quantity', 'quantity']


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _generate_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    np.random.seed(42)
    n_customers = 200
    n_transactions = len(df) * 3 if len(df) < 100 else len(df)

    customer_ids = [f'C{str(i).zfill(5)}' for i in range(1, n_customers + 1)]

    dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='D')
    date_strs = [d.strftime('%Y-%m-%d') for d in dates]

    categories = df['产品类别'].unique().tolist() if '产品类别' in df.columns else ['电子产品', '服装', '食品', '家居']
    regions = df['地区'].unique().tolist() if '地区' in df.columns else ['北京', '上海', '广州', '深圳']

    records = []
    for _ in range(n_transactions):
        cust_id = np.random.choice(customer_ids)
        date = np.random.choice(date_strs)
        amount = round(np.random.gamma(2, 500) + 100, 2)
        quantity = max(1, int(np.random.poisson(3)))
        category = np.random.choice(categories)
        region = np.random.choice(regions)
        records.append({
            '客户ID': cust_id,
            '期间': date,
            '销售额': amount,
            '数量': quantity,
            '产品类别': category,
            '地区': region
        })

    return pd.DataFrame(records)


def prepare_customer_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    cust_col = _find_column(df, CUSTOMER_ID_CANDIDATES)
    is_simulated = False
    if cust_col is None:
        is_simulated = True
        return _generate_customer_data(df), is_simulated

    tx_df = df.copy()
    tx_df = tx_df.rename(columns={cust_col: '客户ID'})

    amount_col = _find_column(tx_df, AMOUNT_CANDIDATES)
    if amount_col is None:
        tx_df['销售额'] = np.random.uniform(100, 5000, len(tx_df))
    else:
        tx_df = tx_df.rename(columns={amount_col: '销售额'})

    time_col = _find_column(tx_df, TIME_CANDIDATES)
    if time_col is None:
        tx_df['期间'] = pd.date_range('2024-01-01', periods=len(tx_df), freq='D').strftime('%Y-%m-%d')
    else:
        tx_df = tx_df.rename(columns={time_col: '期间'})

    qty_col = _find_column(tx_df, QUANTITY_CANDIDATES)
    if qty_col is None:
        tx_df['数量'] = np.random.randint(1, 10, len(tx_df))
    else:
        tx_df = tx_df.rename(columns={qty_col: '数量'})

    keep_cols = ['客户ID', '期间', '销售额', '数量']
    for col in ['产品类别', '地区']:
        if col in tx_df.columns:
            keep_cols.append(col)

    tx_df = tx_df[keep_cols]
    tx_df['销售额'] = pd.to_numeric(tx_df['销售额'], errors='coerce').fillna(100)
    tx_df['数量'] = pd.to_numeric(tx_df['数量'], errors='coerce').fillna(1)
    tx_df['期间'] = pd.to_datetime(tx_df['期间'], errors='coerce')
    tx_df = tx_df.dropna(subset=['期间'])
    tx_df['客户ID'] = tx_df['客户ID'].astype(str).str.strip()

    return tx_df, is_simulated


def calculate_rfm(tx_df: pd.DataFrame) -> pd.DataFrame:
    if tx_df.empty:
        return pd.DataFrame()

    tx_df = tx_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(tx_df['期间']):
        tx_df['期间'] = pd.to_datetime(tx_df['期间'], errors='coerce')
    tx_df = tx_df.dropna(subset=['期间'])

    if tx_df.empty:
        return pd.DataFrame()

    current_date = tx_df['期间'].max() + pd.Timedelta(days=1)

    rfm = tx_df.groupby('客户ID').agg({
        '期间': lambda x: (current_date - x.max()).days,
        '客户ID': 'count',
        '销售额': 'sum',
        '数量': 'sum'
    }).rename(columns={
        '期间': 'Recency',
        '客户ID': 'Frequency',
        '销售额': 'Monetary',
        '数量': 'TotalQuantity'
    }).reset_index()

    rfm['AvgOrderValue'] = (rfm['Monetary'] / rfm['Frequency']).round(2)

    return rfm


def score_rfm_segments(rfm_df: pd.DataFrame) -> pd.DataFrame:
    df = rfm_df.copy()

    df['R_Score'] = pd.qcut(df['Recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
    df['F_Score'] = pd.qcut(df['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    df['M_Score'] = pd.qcut(df['Monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)

    df['RFM_Score'] = df['R_Score'] + df['F_Score'] + df['M_Score']

    def _segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if r >= 4 and f >= 4 and m >= 4:
            return '重要价值客户'
        elif r >= 4 and f <= 2 and m >= 4:
            return '重要发展客户'
        elif r <= 2 and f >= 4 and m >= 4:
            return '重要挽留客户'
        elif r <= 2 and f <= 2 and m >= 4:
            return '重要流失客户'
        elif r >= 4 and f >= 4 and m <= 2:
            return '一般价值客户'
        elif r >= 4 and f <= 2 and m <= 2:
            return '一般发展客户'
        elif r <= 2 and f >= 4 and m <= 2:
            return '一般挽留客户'
        else:
            return '一般流失客户'

    df['客户分群'] = df.apply(_segment, axis=1)
    df['RFM_Segment'] = df['R_Score'].astype(str) + df['F_Score'].astype(str) + df['M_Score'].astype(str)

    return df


def perform_kmeans_clustering(
    rfm_df: pd.DataFrame,
    n_clusters: int = 4,
    use_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if use_columns is None:
        use_columns = ['Recency', 'Frequency', 'Monetary', 'AvgOrderValue']

    available_cols = [c for c in use_columns if c in rfm_df.columns]
    if len(available_cols) < 2:
        available_cols = ['Recency', 'Frequency', 'Monetary']

    features = rfm_df[available_cols].copy()

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    target_n = n_clusters if (n_clusters and n_clusters >= 2 and n_clusters <= 8) else 4
    best_score = -1
    auto_recommend = target_n
    inertia_values = []
    silhouette_scores = []

    max_k = min(8, max(3, len(rfm_df) - 1))
    for k in range(2, max_k + 1):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(scaled_features)
            inertia_values.append({'k': k, 'inertia': round(kmeans.inertia_, 2)})
            n_unique = len(set(labels))
            if n_unique >= 2 and len(rfm_df) > n_unique * 2:
                sil_score = silhouette_score(scaled_features, labels)
                silhouette_scores.append({'k': k, 'silhouette_score': round(sil_score, 4)})
                if sil_score > best_score:
                    best_score = sil_score
                    auto_recommend = k
        except Exception:
            continue

    kmeans_final = KMeans(n_clusters=target_n, random_state=42, n_init=10)
    cluster_labels = kmeans_final.fit_predict(scaled_features)

    current_silhouette = None
    n_unique_final = len(set(cluster_labels))
    if n_unique_final >= 2 and len(rfm_df) > n_unique_final * 2:
        try:
            current_silhouette = round(silhouette_score(scaled_features, cluster_labels), 4)
        except Exception:
            current_silhouette = None

    result_df = rfm_df.copy()
    result_df['Cluster'] = cluster_labels

    cluster_centers = scaler.inverse_transform(kmeans_final.cluster_centers_)
    centers_df = pd.DataFrame(cluster_centers, columns=available_cols)
    centers_df['Cluster'] = range(target_n)

    cluster_info = {
        'n_clusters': target_n,
        'auto_recommend_k': auto_recommend,
        'cluster_centers': centers_df.to_dict('records'),
        'scaled_columns': available_cols,
        'inertia': round(kmeans_final.inertia_, 2),
        'silhouette_score': current_silhouette,
        'elbow_data': inertia_values,
        'silhouette_data': silhouette_scores
    }

    return result_df, cluster_info


def name_clusters(clustered_df: pd.DataFrame) -> pd.DataFrame:
    cluster_stats = clustered_df.groupby('Cluster').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        'AvgOrderValue': 'mean',
        '客户ID': 'count'
    }).rename(columns={'客户ID': '客户数量'})

    total = cluster_stats['客户数量'].sum()
    cluster_stats['占比(%)'] = round(cluster_stats['客户数量'] / total * 100, 2)

    r_avg = cluster_stats['Recency'].mean()
    f_avg = cluster_stats['Frequency'].mean()
    m_avg = cluster_stats['Monetary'].mean()

    cluster_names = {}
    for cid in cluster_stats.index:
        row = cluster_stats.loc[cid]
        r_high = row['Recency'] <= r_avg
        f_high = row['Frequency'] >= f_avg
        m_high = row['Monetary'] >= m_avg

        if r_high and f_high and m_high:
            name = '高价值核心客户'
        elif r_high and f_high and not m_high:
            name = '高频活跃客户'
        elif r_high and not f_high and m_high:
            name = '高消费潜力客户'
        elif not r_high and f_high and m_high:
            name = '沉睡高价值客户'
        elif r_high and not f_high and not m_high:
            name = '新客户/低频客户'
        elif not r_high and f_high and not m_high:
            name = '流失活跃客户'
        elif not r_high and not f_high and m_high:
            name = '流失高消费客户'
        else:
            name = '低价值流失客户'

        cluster_names[cid] = name

    result = clustered_df.copy()
    result['聚类名称'] = result['Cluster'].map(cluster_names)

    return result


def generate_cluster_profiles(
    clustered_df: pd.DataFrame,
    tx_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    profiles = []

    clusters = sorted(clustered_df['Cluster'].unique())
    total_customers = len(clustered_df)

    for cid in clusters:
        cluster_data = clustered_df[clustered_df['Cluster'] == cid]
        name = cluster_data['聚类名称'].iloc[0] if '聚类名称' in cluster_data.columns else f'集群 {cid}'
        count = len(cluster_data)
        pct = round(count / total_customers * 100, 2)

        profile = {
            'Cluster': int(cid),
            '聚类名称': name,
            '客户数量': int(count),
            '客户占比(%)': pct,
            '平均Recency(天)': round(cluster_data['Recency'].mean(), 1),
            '平均购买频次': round(cluster_data['Frequency'].mean(), 1),
            '平均消费总额': round(cluster_data['Monetary'].mean(), 2),
            '平均客单价': round(cluster_data['AvgOrderValue'].mean(), 2),
            'R均值': round(cluster_data['R_Score'].mean(), 2) if 'R_Score' in cluster_data.columns else None,
            'F均值': round(cluster_data['F_Score'].mean(), 2) if 'F_Score' in cluster_data.columns else None,
            'M均值': round(cluster_data['M_Score'].mean(), 2) if 'M_Score' in cluster_data.columns else None
        }

        if tx_df is not None and not tx_df.empty:
            cluster_custs = set(cluster_data['客户ID'].tolist())
            cluster_tx = tx_df[tx_df['客户ID'].isin(cluster_custs)]

            if len(cluster_tx) > 0:
                cust_order_counts = cluster_tx.groupby('客户ID').size()
                repurchase_customers = (cust_order_counts >= 2).sum()
                repurchase_rate = round(
                    repurchase_customers / len(cluster_custs) * 100, 2
                ) if len(cluster_custs) > 0 else 0.0

                if '产品类别' in cluster_tx.columns:
                    top_cats = cluster_tx.groupby('产品类别')['销售额'].sum().sort_values(ascending=False).head(3)
                    profile['偏好品类'] = top_cats.index.tolist()
                else:
                    profile['偏好品类'] = []

                if '地区' in cluster_tx.columns:
                    top_regions = cluster_tx.groupby('地区')['销售额'].sum().sort_values(ascending=False).head(3)
                    profile['主要地区'] = top_regions.index.tolist()
                else:
                    profile['主要地区'] = []

                profile['复购率(%)'] = repurchase_rate
                profile['总订单数'] = int(len(cluster_tx))
                profile['总销售额'] = round(cluster_tx['销售额'].sum(), 2)

                sample_customers = cluster_data['客户ID'].head(3).tolist()
                profile['典型客户'] = sample_customers

        profiles.append(profile)

    return profiles


def run_customer_analysis(
    df: pd.DataFrame,
    n_clusters: int = 4
) -> Dict[str, Any]:
    tx_df, is_simulated = prepare_customer_transactions(df)

    rfm = calculate_rfm(tx_df)

    if len(rfm) < 10:
        return {
            'success': False,
            'error': '客户数量不足，至少需要10个客户数据进行分析',
            'transactions': tx_df,
            'is_simulated': is_simulated
        }

    rfm_scored = score_rfm_segments(rfm)

    clustered, cluster_info = perform_kmeans_clustering(rfm_scored, n_clusters=n_clusters)

    clustered_named = name_clusters(clustered)

    profiles = generate_cluster_profiles(clustered_named, tx_df)

    segment_distribution = clustered_named['客户分群'].value_counts().reset_index()
    segment_distribution.columns = ['客户分群', '客户数量']
    segment_distribution['占比(%)'] = round(segment_distribution['客户数量'] / len(clustered_named) * 100, 2)

    return {
        'success': True,
        'transactions': tx_df,
        'rfm_data': rfm_scored,
        'clustered_data': clustered_named,
        'cluster_info': cluster_info,
        'cluster_profiles': profiles,
        'segment_distribution': segment_distribution.to_dict('records'),
        'total_customers': len(clustered_named),
        'total_transactions': len(tx_df),
        'is_simulated': is_simulated
    }


def export_clustering_results(result: Dict[str, Any], filepath: str) -> bool:
    try:
        clustered = result.get('clustered_data')
        if clustered is None or clustered.empty:
            return False

        export_df = clustered.copy()

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='客户分群结果', index=False)

            profiles = result.get('cluster_profiles', [])
            if profiles:
                pd.DataFrame(profiles).to_excel(writer, sheet_name='群体画像', index=False)

            rfm = result.get('rfm_data')
            if rfm is not None and not rfm.empty:
                rfm.to_excel(writer, sheet_name='RFM明细', index=False)

            tx = result.get('transactions')
            if tx is not None and not tx.empty:
                tx.to_excel(writer, sheet_name='交易明细', index=False)

        return True
    except Exception:
        return False


def export_clustering_csv(result: Dict[str, Any]) -> Optional[str]:
    try:
        clustered = result.get('clustered_data')
        if clustered is None or clustered.empty:
            return None

        return clustered.to_csv(index=False, encoding='utf-8-sig')
    except Exception:
        return None
