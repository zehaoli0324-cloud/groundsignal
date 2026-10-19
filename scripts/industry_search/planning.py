"""Coverage-first query planning: each requested dimension gets a task first."""
from .contracts import DIMENSIONS, aliases, digest, now, target_check

TERMS = {
    'upstream': ('供应商 代工 封装 材料', 'suppliers foundry packaging'),
    'downstream': ('客户 采购 中标 订单', 'customers procurement shipment'),
    'competitors': ('竞争对手 产品 替代', 'competitors product alternatives'),
    'investors': ('股东 融资 投资方', 'shareholders funding investors'),
    'investments': ('对外投资 控股 全资子公司', 'investments subsidiaries ownership'),
    'people': ('创始人 实际控制人 管理层', 'founder beneficial owner management'),
    'products': ('产品 认证 量产 技术', 'products qualification production'),
    'capacity': ('工厂 产能 扩产 投产', 'factory capacity expansion'),
    'counterevidence': ('否认 终止 更正 延期', 'denied terminated correction delayed'),
}


def plan(target, budget):
    target_check(target)
    queries = []
    names = aliases(target)
    english = [name for name in names if name.isascii()]
    english_name = min(english, key=len) if english else names[0]
    purposes = ('discovery_zh', 'discovery_en', 'official_followup',
                'filing_followup', 'commercial_stage', 'countercheck')
    for variant in range(6):
        for dimension in target['dimensions']:
            if len(queries) >= budget['max_queries']:
                break
            # Coverage first, then distinct source/stage/negative-evidence angles.
            name = english_name if variant == 1 else names[0]
            query = '"' + name + '" ' + TERMS[dimension][variant == 1]
            if variant == 2:
                domains = target['official_domains'][:1]
                query += ' site:' + domains[0] if domains else ' 官方公告 原文'
            elif variant == 3:
                query += ' 年报 招股书 (site:cninfo.com.cn OR site:sec.gov)'
            elif variant == 4:
                query += ' 合同 金额 试产 量产 认证 供货'
            elif variant == 5:
                query += ' 否认 终止 历史 更正 非独家'
            for key, value in target['time_range'].items():
                if value:
                    query += ' ' + key + ':' + value
            queries.append({'id': 'q_' + digest([dimension, variant, query])[:16],
                            'dimension': dimension, 'query': query,
                            'purpose': purposes[variant],
                            'time_filter': 'query_hint_not_verified'})
    return {'schema_version': 'groundsignal.search-plan.v1', 'created_at': now(),
            'target': target, 'budget': budget, 'queries': queries,
            'unplanned_dimensions': [x for x in target['dimensions']
                                     if not any(q['dimension'] == x for q in queries)]}
