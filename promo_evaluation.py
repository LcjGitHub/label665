import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


DEFAULT_PRODUCT_COST_RATIO = 0.6

TIME_PERIOD_KEYWORDS = ['促销前', '促销期间', '促销后', '非促销期间', '预热期', '爆发期', '衰退期', '日常销售']


def _is_time_period_label(label: str) -> bool:
    for kw in TIME_PERIOD_KEYWORDS:
        if kw in str(label):
            return True
    return False


def get_activity_list(df: pd.DataFrame) -> List[str]:
    activity_col_candidates = ['活动名称', '活动', '活动名', 'campaign', 'Campaign', '活动编号']
    for col in activity_col_candidates:
        if col in df.columns:
            activities = df[col].dropna().unique().tolist()
            result = [str(a) for a in activities if str(a).strip()]
            if result:
                return result

    if '类型' in df.columns:
        types = df['类型'].dropna().unique().tolist()
        non_period = [str(t) for t in types if not _is_time_period_label(str(t)) and str(t).strip()]
        if non_period:
            return non_period

        all_types = [str(t) for t in types if str(t).strip() and str(t) != '非促销期间']
        if all_types:
            return all_types

    return []


def _get_activity_data(df: pd.DataFrame, activity_name: str, baseline_label: str = '非促销期间') -> Tuple[pd.DataFrame, pd.DataFrame]:
    activity_col_candidates = ['活动名称', '活动', '活动名', 'campaign', 'Campaign', '活动编号']
    for col in activity_col_candidates:
        if col in df.columns:
            activity_data = df[df[col].astype(str) == str(activity_name)]
            baseline_data = df[df['类型'].astype(str) == baseline_label] if '类型' in df.columns else pd.DataFrame()
            if len(activity_data) > 0:
                return activity_data, baseline_data

    activity_data = df[df['类型'].astype(str) == str(activity_name)]
    baseline_data = df[df['类型'].astype(str) == baseline_label]
    return activity_data, baseline_data


def _read_numeric_column(df: pd.DataFrame, col_candidates: List[str], default: float = 0.0) -> float:
    for col in col_candidates:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(vals) > 0:
                return float(vals.sum())
    return default


def _read_single_numeric(df: pd.DataFrame, col_candidates: List[str], default: float = 0.0) -> float:
    for col in col_candidates:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(vals) > 0:
                return float(vals.iloc[0])
    return default


def calculate_investment_return(
    promo_revenue: float,
    baseline_revenue: float,
    promo_cost: float,
    product_cost_ratio: float = DEFAULT_PRODUCT_COST_RATIO
) -> Dict[str, Any]:
    incremental_revenue = max(promo_revenue - baseline_revenue, 0)
    net_profit = incremental_revenue * (1 - product_cost_ratio)
    roi = (net_profit - promo_cost) / promo_cost * 100 if promo_cost > 0 else 0
    payback_period = promo_cost / (net_profit / 12) if net_profit > 0 else float('inf')

    return {
        '促销收入': round(promo_revenue, 2),
        '基准收入': round(baseline_revenue, 2),
        '增量收入': round(incremental_revenue, 2),
        '促销成本': round(promo_cost, 2),
        '净利润': round(net_profit, 2),
        '投资回报率(%)': round(roi, 2),
        '投资回收期(月)': round(payback_period, 2) if payback_period != float('inf') else '无法回收',
        '评级': _get_roi_grade(roi)
    }


def _get_roi_grade(roi: float) -> str:
    if roi >= 100:
        return '优秀'
    elif roi >= 50:
        return '良好'
    elif roi >= 20:
        return '中等'
    elif roi >= 0:
        return '及格'
    else:
        return '较差'


def analyze_sales_lift(
    df: pd.DataFrame,
    activity_name: str,
    baseline_label: str = '非促销期间'
) -> Dict[str, Any]:
    activity_data, baseline_data = _get_activity_data(df, activity_name, baseline_label)

    promo_sales = activity_data['销售额'].sum() if len(activity_data) > 0 else 0
    promo_avg = activity_data['销售额'].mean() if len(activity_data) > 0 else 0
    promo_count = len(activity_data)

    baseline_avg = baseline_data['销售额'].mean() if len(baseline_data) > 0 else 0
    baseline_count = len(baseline_data)

    if baseline_count > 0 and promo_count > 0:
        normalized_baseline = baseline_avg * promo_count
        incremental = promo_sales - normalized_baseline
        lift_rate = (promo_avg - baseline_avg) / baseline_avg * 100 if baseline_avg > 0 else 0
    else:
        normalized_baseline = 0
        incremental = 0
        lift_rate = 0

    total_sales = df['销售额'].sum() if '销售额' in df.columns else 0
    contribution_rate = promo_sales / total_sales * 100 if total_sales > 0 else 0

    return {
        '促销总销售额': round(promo_sales, 2),
        '促销日均销售额': round(promo_avg, 2),
        '基准总销售额(等周期)': round(normalized_baseline, 2),
        '增量销售额': round(incremental, 2),
        '销售提升率(%)': round(lift_rate, 2),
        '活动天数': promo_count,
        '销售占比(%)': round(contribution_rate, 2),
        '提升等级': _get_lift_grade(lift_rate)
    }


def _get_lift_grade(lift_rate: float) -> str:
    if lift_rate >= 100:
        return '显著提升'
    elif lift_rate >= 50:
        return '明显提升'
    elif lift_rate >= 20:
        return '适度提升'
    elif lift_rate >= 0:
        return '轻微提升'
    else:
        return '负增长'


def analyze_customer_acquisition(
    df: pd.DataFrame,
    activity_name: str,
    new_customers: Optional[int] = None,
    promo_cost: Optional[float] = None
) -> Dict[str, Any]:
    activity_data, _ = _get_activity_data(df, activity_name)
    promo_sales = activity_data['销售额'].sum() if len(activity_data) > 0 else 0

    if new_customers is None:
        new_customers = int(_read_numeric_column(
            activity_data,
            ['新增客户数', '新客户数', '获客数', '新增用户'],
            default=0
        ))
        if new_customers == 0:
            new_customers = int(_read_single_numeric(
                activity_data,
                ['新增客户数', '新客户数', '获客数', '新增用户'],
                default=0
            ))

    if promo_cost is None:
        promo_cost = _read_numeric_column(
            activity_data,
            ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
            default=0
        )
        if promo_cost == 0:
            promo_cost = _read_single_numeric(
                activity_data,
                ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
                default=0
            )

    cac = promo_cost / new_customers if new_customers > 0 else float('inf')
    clv = promo_sales / new_customers if new_customers > 0 else 0
    cac_clv_ratio = cac / clv * 100 if clv > 0 else float('inf')
    avg_order_value = promo_sales / len(activity_data) if len(activity_data) > 0 else 0

    return {
        '新增客户数': new_customers,
        '客户获取成本': round(cac, 2) if cac != float('inf') else '无数据',
        '客户生命周期价值': round(clv, 2),
        '获客投入产出比(%)': round(cac_clv_ratio, 2) if cac_clv_ratio != float('inf') else '无数据',
        '平均客单价': round(avg_order_value, 2),
        '促销总投入': round(promo_cost, 2),
        '客户质量等级': _get_cac_grade(cac_clv_ratio if cac_clv_ratio != float('inf') else 999)
    }


def _get_cac_grade(ratio: float) -> str:
    if ratio <= 20:
        return '优秀'
    elif ratio <= 40:
        return '良好'
    elif ratio <= 60:
        return '中等'
    elif ratio <= 80:
        return '及格'
    else:
        return '较差'


def analyze_profit_margin(
    df: pd.DataFrame,
    activity_name: str,
    product_cost_ratio: float = DEFAULT_PRODUCT_COST_RATIO,
    promo_cost: Optional[float] = None
) -> Dict[str, Any]:
    activity_data, _ = _get_activity_data(df, activity_name)
    promo_sales = activity_data['销售额'].sum() if len(activity_data) > 0 else 0

    if promo_cost is None:
        promo_cost = _read_numeric_column(
            activity_data,
            ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
            default=0
        )
        if promo_cost == 0:
            promo_cost = _read_single_numeric(
                activity_data,
                ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
                default=0
            )

    gross_profit = promo_sales * (1 - product_cost_ratio)
    net_profit = gross_profit - promo_cost
    gross_margin = (gross_profit / promo_sales * 100) if promo_sales > 0 else 0
    net_margin = (net_profit / promo_sales * 100) if promo_sales > 0 else 0
    cost_efficiency = (gross_profit / promo_cost * 100) if promo_cost > 0 else 0

    return {
        '促销销售额': round(promo_sales, 2),
        '产品成本': round(promo_sales * product_cost_ratio, 2),
        '毛利润': round(gross_profit, 2),
        '促销费用': round(promo_cost, 2),
        '净利润': round(net_profit, 2),
        '毛利率(%)': round(gross_margin, 2),
        '净利率(%)': round(net_margin, 2),
        '成本效率(%)': round(cost_efficiency, 2),
        '利润等级': _get_margin_grade(net_margin)
    }


def _get_margin_grade(net_margin: float) -> str:
    if net_margin >= 25:
        return '优秀'
    elif net_margin >= 15:
        return '良好'
    elif net_margin >= 8:
        return '中等'
    elif net_margin >= 0:
        return '及格'
    else:
        return '亏损'


def calculate_comprehensive_score(
    roi_data: Dict[str, Any],
    incremental_data: Dict[str, Any],
    cac_data: Dict[str, Any],
    margin_data: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    default_weights = {
        '投资回报': 0.30,
        '销售增量': 0.25,
        '客户获取': 0.20,
        '利润边际': 0.25
    }
    weights = weights or default_weights

    total_weight = sum(weights.values())
    if total_weight != 0:
        weights = {k: v / total_weight for k, v in weights.items()}

    roi_score = _normalize_roi(roi_data.get('投资回报率(%)', 0))
    lift_score = _normalize_lift(incremental_data.get('销售提升率(%)', 0))
    cac_ratio = cac_data.get('获客投入产出比(%)', 100)
    if isinstance(cac_ratio, str):
        cac_ratio = 100
    cac_score = _normalize_cac(cac_ratio)
    margin_score = _normalize_margin(margin_data.get('净利率(%)', 0))

    dimension_scores = {
        '投资回报': round(roi_score, 2),
        '销售增量': round(lift_score, 2),
        '客户获取': round(cac_score, 2),
        '利润边际': round(margin_score, 2)
    }

    comprehensive = (
        dimension_scores['投资回报'] * weights['投资回报'] +
        dimension_scores['销售增量'] * weights['销售增量'] +
        dimension_scores['客户获取'] * weights['客户获取'] +
        dimension_scores['利润边际'] * weights['利润边际']
    )

    radar_data = {
        '指标': list(dimension_scores.keys()),
        '评分': list(dimension_scores.values())
    }

    return {
        '维度评分': dimension_scores,
        '综合评分': round(comprehensive, 2),
        '评级': _get_comprehensive_grade(comprehensive),
        '雷达图数据': radar_data,
        '权重配置': weights
    }


def _normalize_roi(roi: float) -> float:
    if roi >= 150:
        return 100
    elif roi >= 100:
        return 90 + (roi - 100) / 50 * 10
    elif roi >= 50:
        return 75 + (roi - 50) / 50 * 15
    elif roi >= 20:
        return 60 + (roi - 20) / 30 * 15
    elif roi >= 0:
        return 40 + roi / 20 * 20
    else:
        return max(0, 40 + roi / 5)


def _normalize_lift(lift: float) -> float:
    if lift >= 150:
        return 100
    elif lift >= 100:
        return 90 + (lift - 100) / 50 * 10
    elif lift >= 50:
        return 75 + (lift - 50) / 50 * 15
    elif lift >= 20:
        return 60 + (lift - 20) / 30 * 15
    elif lift >= 0:
        return 40 + lift / 20 * 20
    else:
        return max(0, 40 + lift / 5)


def _normalize_cac(ratio: float) -> float:
    if ratio <= 15:
        return 100
    elif ratio <= 30:
        return 85 + (30 - ratio) / 15 * 15
    elif ratio <= 50:
        return 65 + (50 - ratio) / 20 * 20
    elif ratio <= 70:
        return 45 + (70 - ratio) / 20 * 20
    elif ratio <= 100:
        return 20 + (100 - ratio) / 30 * 25
    else:
        return max(0, 20 - (ratio - 100) / 10)


def _normalize_margin(margin: float) -> float:
    if margin >= 30:
        return 100
    elif margin >= 20:
        return 85 + (margin - 20) / 10 * 15
    elif margin >= 10:
        return 65 + (margin - 10) / 10 * 20
    elif margin >= 5:
        return 45 + (margin - 5) / 5 * 20
    elif margin >= 0:
        return 20 + margin / 5 * 25
    else:
        return max(0, 20 + margin / 2)


def _get_comprehensive_grade(score: float) -> str:
    if score >= 85:
        return 'S级（卓越）'
    elif score >= 75:
        return 'A级（优秀）'
    elif score >= 65:
        return 'B级（良好）'
    elif score >= 55:
        return 'C级（中等）'
    elif score >= 45:
        return 'D级（及格）'
    else:
        return 'E级（待改进）'


def generate_improvement_suggestions(
    activity_name: str,
    comprehensive_data: Dict[str, Any],
    roi_data: Dict[str, Any],
    incremental_data: Dict[str, Any],
    cac_data: Dict[str, Any],
    margin_data: Dict[str, Any]
) -> List[str]:
    suggestions = []

    scores = comprehensive_data.get('维度评分', {})

    if scores.get('投资回报', 100) < 60:
        roi_val = roi_data.get('投资回报率(%)', 0)
        if roi_val < 0:
            suggestions.append(
                f'【投资回报】当前活动投资回报率为 {roi_val:.2f}%，处于亏损状态。建议：'
                f'重新评估促销成本结构，优化投放渠道，或调整折扣力度以提升边际收益。'
            )
        elif roi_val < 20:
            suggestions.append(
                f'【投资回报】投资回报率仅为 {roi_val:.2f}%，收益较低。建议：'
                f'分析高效渠道并加大投入，减少低效广告支出，提升活动精准度。'
            )

    if scores.get('销售增量', 100) < 60:
        lift = incremental_data.get('销售提升率(%)', 0)
        if lift <= 0:
            suggestions.append(
                f'【销售增量】销售提升率为 {lift:.2f}%，未实现预期增长。建议：'
                f'优化促销机制设计，增加稀缺性和紧迫感，或尝试捆绑销售、满减等更具吸引力的促销形式。'
            )
        elif lift < 20:
            suggestions.append(
                f'【销售增量】销售仅提升 {lift:.2f}%，效果有限。建议：'
                f'扩大活动触达范围，加强社交媒体推广，或针对高价值客户制定专属优惠。'
            )

    if scores.get('客户获取', 100) < 60:
        cac_ratio = cac_data.get('获客投入产出比(%)', 100)
        if isinstance(cac_ratio, (int, float)) and cac_ratio > 60:
            suggestions.append(
                f'【客户获取】获客投入产出比为 {cac_ratio:.2f}%，获客效率偏低。建议：'
                f'优化获客渠道，通过老客户推荐计划降低成本，同时通过会员体系提升客户复购和生命周期价值。'
            )

    if scores.get('利润边际', 100) < 60:
        net_margin = margin_data.get('净利率(%)', 0)
        if net_margin < 0:
            suggestions.append(
                f'【利润边际】净利率为 {net_margin:.2f}%，活动处于亏损状态。建议：'
                f'严格控制产品成本，降低折扣幅度，或通过提高客单价（如满赠、加价购）改善利润结构。'
            )
        elif net_margin < 8:
            suggestions.append(
                f'【利润边际】净利率仅为 {net_margin:.2f}%，利润空间较薄。建议：'
                f'优化促销品类组合，主推高毛利产品，同时减少不必要的营销费用。'
            )

    overall_score = comprehensive_data.get('综合评分', 0)
    if overall_score >= 75:
        suggestions.append(
            f'【整体评价】活动综合评分为 {overall_score:.2f}，表现优秀！'
            f'建议总结成功经验，形成可复制的活动模板，并探索在更多品类或区域推广。'
        )
    elif overall_score >= 60:
        suggestions.append(
            f'【整体评价】活动综合评分为 {overall_score:.2f}，整体良好但仍有提升空间。'
            f'建议聚焦上述薄弱环节进行针对性优化，争取下次活动达到优秀水平。'
        )
    else:
        suggestions.append(
            f'【整体评价】活动综合评分为 {overall_score:.2f}，未达预期。'
            f'建议进行全面复盘，重新审视活动目标、预算分配和执行策略，必要时调整活动整体方案。'
        )

    return suggestions


def compare_with_all_activities(
    current_activity: str,
    all_activity_results: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    all_scores = []
    for act_name, result in all_activity_results.items():
        comp = result.get('综合评分', {})
        all_scores.append({
            '活动名称': act_name,
            '综合评分': comp.get('综合评分', 0),
            '投资回报': comp.get('维度评分', {}).get('投资回报', 0),
            '销售增量': comp.get('维度评分', {}).get('销售增量', 0),
            '客户获取': comp.get('维度评分', {}).get('客户获取', 0),
            '利润边际': comp.get('维度评分', {}).get('利润边际', 0),
            '评级': comp.get('评级', '')
        })

    sorted_scores = sorted(all_scores, key=lambda x: x['综合评分'], reverse=True)
    rank_map = {item['活动名称']: i + 1 for i, item in enumerate(sorted_scores)}

    other_scores = [s for s in all_scores if s['活动名称'] != current_activity]
    other_comprehensive = [s['综合评分'] for s in other_scores]

    if other_comprehensive:
        avg_other = sum(other_comprehensive) / len(other_comprehensive)
        max_other = max(other_comprehensive)
        min_other = min(other_comprehensive)
    else:
        avg_other = 0
        max_other = 0
        min_other = 0

    current_result = all_activity_results.get(current_activity, {})
    current_comp = current_result.get('综合评分', {})
    current_score = current_comp.get('综合评分', 0)
    current_dim = current_comp.get('维度评分', {})

    rank = rank_map.get(current_activity, 1)
    rank_str = f'第{rank}名（共{len(all_scores)}个活动）'

    comparisons = []
    for s in sorted_scores:
        diff = round(current_score - s['综合评分'], 2)
        comparisons.append({
            '活动名称': s['活动名称'],
            '综合评分': s['综合评分'],
            '投资回报': s['投资回报'],
            '销售增量': s['销售增量'],
            '客户获取': s['客户获取'],
            '利润边际': s['利润边际'],
            '评级': s['评级'],
            '与当前活动分差': diff if s['活动名称'] != current_activity else 0,
            '对比结果': '当前活动' if s['活动名称'] == current_activity else (
                '优于' if diff > 0 else ('持平' if diff == 0 else '劣于')
            )
        })

    avg_dim_roi = sum(s['投资回报'] for s in other_scores) / len(other_scores) if other_scores else 0
    avg_dim_lift = sum(s['销售增量'] for s in other_scores) / len(other_scores) if other_scores else 0
    avg_dim_cac = sum(s['客户获取'] for s in other_scores) / len(other_scores) if other_scores else 0
    avg_dim_margin = sum(s['利润边际'] for s in other_scores) / len(other_scores) if other_scores else 0

    dimension_comparison = {
        '投资回报': {
            '当前评分': current_dim.get('投资回报', 0),
            '其他活动平均': round(avg_dim_roi, 2),
            '差异': round(current_dim.get('投资回报', 0) - avg_dim_roi, 2)
        },
        '销售增量': {
            '当前评分': current_dim.get('销售增量', 0),
            '其他活动平均': round(avg_dim_lift, 2),
            '差异': round(current_dim.get('销售增量', 0) - avg_dim_lift, 2)
        },
        '客户获取': {
            '当前评分': current_dim.get('客户获取', 0),
            '其他活动平均': round(avg_dim_cac, 2),
            '差异': round(current_dim.get('客户获取', 0) - avg_dim_cac, 2)
        },
        '利润边际': {
            '当前评分': current_dim.get('利润边际', 0),
            '其他活动平均': round(avg_dim_margin, 2),
            '差异': round(current_dim.get('利润边际', 0) - avg_dim_margin, 2)
        }
    }

    return {
        '当前综合评分': round(current_score, 2),
        '其他活动平均分': round(avg_other, 2),
        '其他活动最高分': round(max_other, 2),
        '其他活动最低分': round(min_other, 2),
        '相对其他活动平均': round(current_score - avg_other, 2),
        '总排名': rank_str,
        '各活动评分明细表': comparisons,
        '维度对比': dimension_comparison,
        '对比结论': _generate_comparison_conclusion(
            current_score, avg_other, max_other, dimension_comparison, len(all_scores)
        )
    }


def _generate_comparison_conclusion(
    current_score: float,
    avg_other: float,
    max_other: float,
    dim_comparison: Dict[str, Any],
    total_count: int
) -> str:
    diff = current_score - avg_other

    if total_count <= 1:
        return '📋 当前仅有一个活动可供评估，建议积累更多活动数据后进行横向对比分析。'

    if current_score >= max_other and max_other > 0:
        strong_dims = [k for k, v in dim_comparison.items() if v['差异'] >= 5]
        conclusion = (
            f'🎉 本次活动表现卓越！综合评分 {current_score:.2f} 在所有活动中名列前茅，'
            f'高于其他活动平均 {diff:+.2f} 分。'
        )
        if strong_dims:
            conclusion += f' 其中「{"、".join(strong_dims)}」维度表现尤为突出，值得重点推广经验。'
        return conclusion
    elif diff >= 5:
        strong_dims = [k for k, v in dim_comparison.items() if v['差异'] >= 5]
        weak_dims = [k for k, v in dim_comparison.items() if v['差异'] < -5]
        conclusion = (
            f'📈 本次活动表现优秀，综合评分 {current_score:.2f}，'
            f'高于其他活动平均 {diff:+.2f} 分。'
        )
        if strong_dims:
            conclusion += f' 优势维度：「{"、".join(strong_dims)}」。'
        if weak_dims:
            conclusion += f' 需改进维度：「{"、".join(weak_dims)}」。'
        return conclusion
    elif diff >= -5:
        conclusion = (
            f'➡️ 本次活动表现中规中矩，综合评分 {current_score:.2f}，'
            f'与其他活动平均基本持平（{diff:+.2f} 分）。'
            f'建议各维度均衡优化，争取下次活动超越平均水平。'
        )
        return conclusion
    else:
        weak_dims = [k for k, v in dim_comparison.items() if v['差异'] < -5]
        conclusion = (
            f'📉 本次活动表现低于其他活动平均，综合评分 {current_score:.2f}，'
            f'低于其他活动平均 {abs(diff):.2f} 分。'
        )
        if weak_dims:
            conclusion += f' 主要薄弱环节：「{"、".join(weak_dims)}」，需针对性优化。'
        return conclusion


def evaluate_single_activity(
    df: pd.DataFrame,
    activity_name: str,
    weights: Optional[Dict[str, float]] = None,
    promo_cost: Optional[float] = None,
    new_customers: Optional[int] = None,
    product_cost_ratio: float = DEFAULT_PRODUCT_COST_RATIO,
    baseline_label: str = '非促销期间'
) -> Dict[str, Any]:
    activity_data, baseline_data = _get_activity_data(df, activity_name, baseline_label)
    promo_revenue = activity_data['销售额'].sum() if len(activity_data) > 0 else 0
    baseline_avg = baseline_data['销售额'].mean() if len(baseline_data) > 0 else 0
    promo_count = len(activity_data)
    baseline_revenue = baseline_avg * promo_count if baseline_avg > 0 else 0

    if promo_cost is None:
        promo_cost = _read_numeric_column(
            activity_data,
            ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
            default=0
        )
        if promo_cost == 0:
            promo_cost = _read_single_numeric(
                activity_data,
                ['促销成本', '活动成本', '营销费用', '推广费用', '投入成本'],
                default=0
            )

    roi_result = calculate_investment_return(promo_revenue, baseline_revenue, promo_cost, product_cost_ratio)
    incremental_result = analyze_sales_lift(df, activity_name, baseline_label)
    cac_result = analyze_customer_acquisition(df, activity_name, new_customers, promo_cost)
    margin_result = analyze_profit_margin(df, activity_name, product_cost_ratio, promo_cost)
    comprehensive_result = calculate_comprehensive_score(
        roi_result, incremental_result, cac_result, margin_result, weights
    )

    return {
        '活动名称': activity_name,
        '投资回报分析': roi_result,
        '增量销售分析': incremental_result,
        '客户获取分析': cac_result,
        '利润边际分析': margin_result,
        '综合评分': comprehensive_result,
        '雷达图数据': comprehensive_result['雷达图数据']
    }


def evaluate_promo_activity(
    df: pd.DataFrame,
    activity_name: str,
    weights: Optional[Dict[str, float]] = None,
    promo_cost: Optional[float] = None,
    new_customers: Optional[int] = None,
    product_cost_ratio: float = DEFAULT_PRODUCT_COST_RATIO,
    baseline_label: str = '非促销期间'
) -> Dict[str, Any]:
    all_activities = get_activity_list(df)

    all_activity_results = {}
    for act in all_activities:
        all_activity_results[act] = evaluate_single_activity(
            df, act, weights, promo_cost, new_customers, product_cost_ratio, baseline_label
        )

    current = all_activity_results.get(activity_name, {})
    if not current:
        current = evaluate_single_activity(
            df, activity_name, weights, promo_cost, new_customers, product_cost_ratio, baseline_label
        )
        all_activity_results[activity_name] = current

    suggestions = generate_improvement_suggestions(
        activity_name,
        current['综合评分'],
        current['投资回报分析'],
        current['增量销售分析'],
        current['客户获取分析'],
        current['利润边际分析']
    )
    history_comparison = compare_with_all_activities(activity_name, all_activity_results)

    return {
        '活动名称': activity_name,
        '投资回报分析': current['投资回报分析'],
        '增量销售分析': current['增量销售分析'],
        '客户获取分析': current['客户获取分析'],
        '利润边际分析': current['利润边际分析'],
        '综合评分': current['综合评分'],
        '雷达图数据': current['雷达图数据'],
        '权重配置': current['综合评分']['权重配置'],
        '改进建议': suggestions,
        '活动对比': history_comparison,
        '所有活动结果': all_activity_results
    }
