import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


DEFAULT_PROMO_COSTS = {
    '促销期间': 50000,
    '促销前': 20000,
    '促销后': 30000
}

DEFAULT_NEW_CUSTOMERS = {
    '促销期间': 800,
    '促销前': 200,
    '促销后': 350
}

DEFAULT_PRODUCT_COST_RATIO = 0.6


def calculate_roi(
    promo_revenue: float,
    baseline_revenue: float,
    promo_cost: float
) -> Dict[str, Any]:
    incremental_revenue = max(promo_revenue - baseline_revenue, 0)
    net_profit = incremental_revenue * (1 - DEFAULT_PRODUCT_COST_RATIO)
    roi = (net_profit - promo_cost) / promo_cost * 100 if promo_cost > 0 else 0
    payback_period = promo_cost / (net_profit / 12) if net_profit > 0 else float('inf')

    return {
        '促销收入': round(promo_revenue, 2),
        '基准收入': round(baseline_revenue, 2),
        '增量收入': round(incremental_revenue, 2),
        '促销成本': round(promo_cost, 2),
        '净利润': round(net_profit, 2),
        'ROI(%)': round(roi, 2),
        '投资回收期(月)': round(payback_period, 2) if payback_period != float('inf') else 'N/A',
        'ROI等级': _get_roi_grade(roi)
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


def analyze_incremental_sales(
    df: pd.DataFrame,
    promo_types: List[str],
    baseline_type: str = '非促销期间'
) -> Dict[str, Any]:
    result = {}

    baseline_data = df[df['类型'] == baseline_type]
    baseline_sales = baseline_data['销售额'].sum() if len(baseline_data) > 0 else 0
    baseline_avg = baseline_data['销售额'].mean() if len(baseline_data) > 0 else 0
    baseline_count = len(baseline_data)

    for ptype in promo_types:
        promo_data = df[df['类型'] == ptype]
        promo_sales = promo_data['销售额'].sum() if len(promo_data) > 0 else 0
        promo_avg = promo_data['销售额'].mean() if len(promo_data) > 0 else 0
        promo_count = len(promo_data)

        if baseline_count > 0 and promo_count > 0:
            normalized_baseline = baseline_avg * promo_count
            incremental = promo_sales - normalized_baseline
            lift_rate = (promo_avg - baseline_avg) / baseline_avg * 100 if baseline_avg > 0 else 0
        else:
            incremental = 0
            lift_rate = 0

        contribution_rate = promo_sales / df['销售额'].sum() * 100 if df['销售额'].sum() > 0 else 0

        result[ptype] = {
            '促销总销售额': round(promo_sales, 2),
            '促销日均销售额': round(promo_avg, 2),
            '基准总销售额(等周期)': round(normalized_baseline if baseline_count > 0 else 0, 2),
            '增量销售额': round(incremental, 2),
            '销售提升率(%)': round(lift_rate, 2),
            '活动天数': promo_count,
            '销售占比(%)': round(contribution_rate, 2),
            '提升等级': _get_lift_grade(lift_rate)
        }

    return result


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


def analyze_customer_acquisition_cost(
    df: pd.DataFrame,
    promo_types: List[str],
    new_customers_map: Optional[Dict[str, int]] = None,
    promo_costs_map: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    result = {}
    new_customers_map = new_customers_map or DEFAULT_NEW_CUSTOMERS
    promo_costs_map = promo_costs_map or DEFAULT_PROMO_COSTS

    for ptype in promo_types:
        promo_data = df[df['类型'] == ptype]
        promo_sales = promo_data['销售额'].sum() if len(promo_data) > 0 else 0
        new_customers = new_customers_map.get(ptype, 0)
        promo_cost = promo_costs_map.get(ptype, 0)

        cac = promo_cost / new_customers if new_customers > 0 else float('inf')
        clv = promo_sales / new_customers if new_customers > 0 else 0
        cac_clv_ratio = cac / clv * 100 if clv > 0 else float('inf')
        avg_order_value = promo_sales / len(promo_data) if len(promo_data) > 0 else 0

        result[ptype] = {
            '新增客户数': new_customers,
            '客户获取成本(CAC)': round(cac, 2) if cac != float('inf') else 'N/A',
            '客户生命周期价值(CLV)': round(clv, 2),
            'CAC/CLV比率(%)': round(cac_clv_ratio, 2) if cac_clv_ratio != float('inf') else 'N/A',
            '平均客单价': round(avg_order_value, 2),
            '促销总投入': round(promo_cost, 2),
            '客户质量等级': _get_cac_grade(cac_clv_ratio if cac_clv_ratio != float('inf') else 999)
        }

    return result


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
    promo_types: List[str],
    product_cost_ratio: float = DEFAULT_PRODUCT_COST_RATIO,
    promo_costs_map: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    result = {}
    promo_costs_map = promo_costs_map or DEFAULT_PROMO_COSTS

    for ptype in promo_types:
        promo_data = df[df['类型'] == ptype]
        promo_sales = promo_data['销售额'].sum() if len(promo_data) > 0 else 0

        gross_profit = promo_sales * (1 - product_cost_ratio)
        promo_cost = promo_costs_map.get(ptype, 0)
        net_profit = gross_profit - promo_cost
        gross_margin = (gross_profit / promo_sales * 100) if promo_sales > 0 else 0
        net_margin = (net_profit / promo_sales * 100) if promo_sales > 0 else 0
        cost_efficiency = (gross_profit / promo_cost * 100) if promo_cost > 0 else 0

        result[ptype] = {
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

    return result


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
        'ROI': 0.30,
        '销售增量': 0.25,
        '客户获取': 0.20,
        '利润边际': 0.25
    }
    weights = weights or default_weights

    total_weight = sum(weights.values())
    if total_weight != 0:
        weights = {k: v / total_weight for k, v in weights.items()}

    scores = {}
    radar_data = {}

    for ptype in incremental_data.keys():
        roi_score = _normalize_roi(roi_data.get('ROI(%)', 0))
        lift_score = _normalize_lift(incremental_data[ptype].get('销售提升率(%)', 0))
        cac_ratio = cac_data[ptype].get('CAC/CLV比率(%)', 100)
        if isinstance(cac_ratio, str):
            cac_ratio = 100
        cac_score = _normalize_cac(cac_ratio)
        margin_score = _normalize_margin(margin_data[ptype].get('净利率(%)', 0))

        dimension_scores = {
            'ROI': round(roi_score, 2),
            '销售增量': round(lift_score, 2),
            '客户获取': round(cac_score, 2),
            '利润边际': round(margin_score, 2)
        }

        comprehensive = (
            dimension_scores['ROI'] * weights['ROI'] +
            dimension_scores['销售增量'] * weights['销售增量'] +
            dimension_scores['客户获取'] * weights['客户获取'] +
            dimension_scores['利润边际'] * weights['利润边际']
        )

        scores[ptype] = {
            '维度评分': dimension_scores,
            '综合评分': round(comprehensive, 2),
            '评级': _get_comprehensive_grade(comprehensive)
        }

        radar_data[ptype] = {
            '指标': list(dimension_scores.keys()),
            '评分': list(dimension_scores.values())
        }

    return {
        '各活动评分': scores,
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
    ptype: str,
    comprehensive_data: Dict[str, Any],
    roi_data: Dict[str, Any],
    incremental_data: Dict[str, Any],
    cac_data: Dict[str, Any],
    margin_data: Dict[str, Any]
) -> List[str]:
    suggestions = []

    scores = comprehensive_data['各活动评分'].get(ptype, {}).get('维度评分', {})

    if scores.get('ROI', 100) < 60:
        roi_val = roi_data.get('ROI(%)', 0)
        if roi_val < 0:
            suggestions.append(
                f'【投资回报】当前活动 ROI 为 {roi_val:.2f}%，处于亏损状态。建议：'
                f'重新评估促销成本结构，优化投放渠道，或调整折扣力度以提升边际收益。'
            )
        elif roi_val < 20:
            suggestions.append(
                f'【投资回报】ROI 仅为 {roi_val:.2f}%，收益较低。建议：'
                f'分析高ROI渠道并加大投入，减少低效广告支出，提升活动精准度。'
            )

    if scores.get('销售增量', 100) < 60:
        lift = incremental_data[ptype].get('销售提升率(%)', 0)
        if lift <= 0:
            suggestions.append(
                f'【销售增量】销售提升率为 {lift:.2f}%，未实现预期增长。建议：'
                f'优化促销机制设计，增加稀缺性和紧迫感，或尝试捆绑销售、满减等更具吸引力的促销形式。'
            )
        elif lift < 20:
            suggestions.append(
                f'【销售增量】销售仅提升 {lift:.2f}%，效果有限。建议：'
                f'扩大活动触达范围，加强社交媒体和KOL推广，或针对高价值客户制定专属优惠。'
            )

    if scores.get('客户获取', 100) < 60:
        cac_ratio = cac_data[ptype].get('CAC/CLV比率(%)', 100)
        if isinstance(cac_ratio, (int, float)) and cac_ratio > 60:
            suggestions.append(
                f'【客户获取】CAC/CLV 比率达 {cac_ratio:.2f}%，获客效率偏低。建议：'
                f'优化获客渠道，通过老客户推荐计划降低CAC，同时通过会员体系提升客户复购和生命周期价值。'
            )

    if scores.get('利润边际', 100) < 60:
        net_margin = margin_data[ptype].get('净利率(%)', 0)
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

    overall_score = comprehensive_data['各活动评分'].get(ptype, {}).get('综合评分', 0)
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


def compare_with_history(
    ptype: str,
    current_scores: Dict[str, Any],
    historical_scores: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    if not historical_scores:
        historical_scores = [
            {'活动名称': '历史活动A_春节大促', '综合评分': 72.5, 'ROI': 78, '销售增量': 65, '客户获取': 70, '利润边际': 76},
            {'活动名称': '历史活动B_618促销', '综合评分': 68.3, 'ROI': 65, '销售增量': 72, '客户获取': 68, '利润边际': 67},
            {'活动名称': '历史活动C_双11狂欢', '综合评分': 81.2, 'ROI': 85, '销售增量': 82, '客户获取': 78, '利润边际': 80},
            {'活动名称': '历史活动D_周年庆', '综合评分': 63.8, 'ROI': 60, '销售增量': 68, '客户获取': 62, '利润边际': 64}
        ]

    current_dim = current_scores.get('维度评分', {})
    current_comprehensive = current_scores.get('综合评分', 0)

    historical_comprehensive = [h['综合评分'] for h in historical_scores]
    avg_history = sum(historical_comprehensive) / len(historical_comprehensive) if historical_comprehensive else 0
    max_history = max(historical_comprehensive) if historical_comprehensive else 0
    min_history = min(historical_comprehensive) if historical_comprehensive else 0

    rank = 1
    for h_score in historical_comprehensive:
        if current_comprehensive < h_score:
            rank += 1
    rank_str = f'第{rank}名（共{len(historical_scores) + 1}个活动）'

    comparisons = []
    for h in historical_scores:
        diff = round(current_comprehensive - h['综合评分'], 2)
        comparisons.append({
            '对比活动': h['活动名称'],
            '历史评分': h['综合评分'],
            '当前评分': round(current_comprehensive, 2),
            '分差': diff,
            '对比结果': '优于' if diff > 0 else ('持平' if diff == 0 else '劣于')
        })

    avg_dim_roi = sum(h.get('ROI', 0) for h in historical_scores) / len(historical_scores)
    avg_dim_lift = sum(h.get('销售增量', 0) for h in historical_scores) / len(historical_scores)
    avg_dim_cac = sum(h.get('客户获取', 0) for h in historical_scores) / len(historical_scores)
    avg_dim_margin = sum(h.get('利润边际', 0) for h in historical_scores) / len(historical_scores)

    dimension_comparison = {
        'ROI': {
            '当前评分': current_dim.get('ROI', 0),
            '历史平均': round(avg_dim_roi, 2),
            '差异': round(current_dim.get('ROI', 0) - avg_dim_roi, 2)
        },
        '销售增量': {
            '当前评分': current_dim.get('销售增量', 0),
            '历史平均': round(avg_dim_lift, 2),
            '差异': round(current_dim.get('销售增量', 0) - avg_dim_lift, 2)
        },
        '客户获取': {
            '当前评分': current_dim.get('客户获取', 0),
            '历史平均': round(avg_dim_cac, 2),
            '差异': round(current_dim.get('客户获取', 0) - avg_dim_cac, 2)
        },
        '利润边际': {
            '当前评分': current_dim.get('利润边际', 0),
            '历史平均': round(avg_dim_margin, 2),
            '差异': round(current_dim.get('利润边际', 0) - avg_dim_margin, 2)
        }
    }

    return {
        '当前综合评分': round(current_comprehensive, 2),
        '历史平均分': round(avg_history, 2),
        '历史最高分': round(max_history, 2),
        '历史最低分': round(min_history, 2),
        '相对历史平均': round(current_comprehensive - avg_history, 2),
        '历史排名': rank_str,
        '活动对比明细': comparisons,
        '维度对比': dimension_comparison,
        '对比结论': _generate_comparison_conclusion(
            current_comprehensive, avg_history, max_history, dimension_comparison
        )
    }


def _generate_comparison_conclusion(
    current_score: float,
    avg_history: float,
    max_history: float,
    dim_comparison: Dict[str, Any]
) -> str:
    diff = current_score - avg_history

    if current_score >= max_history:
        strong_dims = [k for k, v in dim_comparison.items() if v['差异'] >= 5]
        conclusion = (
            f'🎉 本次活动表现卓越！综合评分 {current_score:.2f} 创历史新高，'
            f'高于历史平均 {diff:+.2f} 分。'
        )
        if strong_dims:
            conclusion += f' 其中「{"、".join(strong_dims)}」维度表现尤为突出，值得重点推广经验。'
        return conclusion
    elif diff >= 5:
        strong_dims = [k for k, v in dim_comparison.items() if v['差异'] >= 5]
        weak_dims = [k for k, v in dim_comparison.items() if v['差异'] < -5]
        conclusion = (
            f'📈 本次活动表现优秀，综合评分 {current_score:.2f}，'
            f'高于历史平均 {diff:+.2f} 分。'
        )
        if strong_dims:
            conclusion += f' 优势维度：「{"、".join(strong_dims)}」。'
        if weak_dims:
            conclusion += f' 需改进维度：「{"、".join(weak_dims)}」。'
        return conclusion
    elif diff >= -5:
        conclusion = (
            f'➡️ 本次活动表现中规中矩，综合评分 {current_score:.2f}，'
            f'与历史平均基本持平（{diff:+.2f} 分）。'
            f'建议各维度均衡优化，争取下次活动突破平均水平。'
        )
        return conclusion
    else:
        weak_dims = [k for k, v in dim_comparison.items() if v['差异'] < -5]
        conclusion = (
            f'📉 本次活动表现低于历史平均，综合评分 {current_score:.2f}，'
            f'低于历史平均 {abs(diff):.2f} 分。'
        )
        if weak_dims:
            conclusion += f' 主要薄弱环节：「{"、".join(weak_dims)}」，需针对性优化。'
        return conclusion


def get_promo_activity_types(df: pd.DataFrame) -> List[str]:
    if '类型' not in df.columns:
        return []
    types = df['类型'].dropna().unique().tolist()
    return [str(t) for t in types if t != '非促销期间']


def evaluate_promo_activity(
    df: pd.DataFrame,
    activity_type: str,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    promo_types = [activity_type]

    baseline_type = '非促销期间'
    promo_revenue = df[df['类型'] == activity_type]['销售额'].sum() if len(df[df['类型'] == activity_type]) > 0 else 0
    baseline_data = df[df['类型'] == baseline_type]
    baseline_avg = baseline_data['销售额'].mean() if len(baseline_data) > 0 else 0
    promo_count = len(df[df['类型'] == activity_type])
    baseline_revenue = baseline_avg * promo_count if baseline_avg > 0 else 0
    promo_cost = DEFAULT_PROMO_COSTS.get(activity_type, 30000)

    roi_result = calculate_roi(promo_revenue, baseline_revenue, promo_cost)
    incremental_result = analyze_incremental_sales(df, promo_types, baseline_type)
    cac_result = analyze_customer_acquisition_cost(df, promo_types)
    margin_result = analyze_profit_margin(df, promo_types)
    comprehensive_result = calculate_comprehensive_score(
        roi_result, incremental_result, cac_result, margin_result, weights
    )
    suggestions = generate_improvement_suggestions(
        activity_type, comprehensive_result, roi_result,
        incremental_result, cac_result, margin_result
    )
    history_comparison = compare_with_history(
        activity_type, comprehensive_result['各活动评分'][activity_type]
    )

    return {
        '活动名称': activity_type,
        'ROI分析': roi_result,
        '增量销售分析': incremental_result[activity_type],
        '客户获取分析': cac_result[activity_type],
        '利润边际分析': margin_result[activity_type],
        '综合评分': comprehensive_result['各活动评分'][activity_type],
        '雷达图数据': comprehensive_result['雷达图数据'][activity_type],
        '权重配置': comprehensive_result['权重配置'],
        '改进建议': suggestions,
        '历史对比': history_comparison
    }
