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
    for variant in range(3):
        for dimension in target['dimensions']:
            if len(queries) >= budget['max_queries']:
                break
            # Chinese discovery, English alias discovery, first-party follow-up.
            name = names[0] if variant != 1 else names[-1]
            query = '"' + name + '" ' + TERMS[dimension][variant == 1]
            if variant == 2:
                domains = list(dict.fromkeys([*target['official_domains'], 'cninfo.com.cn', 'sse.com.cn', 'szse.cn']))
                query += ' (' + ' OR '.join('site:' + d for d in domains[:5]) + ')'
            for key, value in target['time_range'].items():
                if value:
                    query += ' ' + key + ':' + value
            queries.append({'id': 'q_' + digest([dimension, variant, query])[:16],
                            'dimension': dimension, 'query': query,
                            'purpose': ('discovery_zh', 'discovery_en', 'first_party_followup')[variant],
                            'time_filter': 'query_hint_not_verified'})
    return {'schema_version': 'groundsignal.search-plan.v1', 'created_at': now(),
            'target': target, 'budget': budget, 'queries': queries,
            'unplanned_dimensions': [x for x in target['dimensions']
                                     if not any(q['dimension'] == x for q in queries)]}
