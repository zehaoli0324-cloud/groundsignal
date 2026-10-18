# GroundSignal 搜索运行

- 运行：run_550c0d4358ac14397631
- 状态：SYNTHETIC_ONLY
- 数据：合成测试，未执行真实模型
- 搜索/抓取/模型请求：{'search_calls': 0, 'fetch_calls': 0, 'model_calls': 0, 'large_model_calls': 0, 'simulated_model_calls': 8, 'pending_candidates': 4}

## 覆盖与缺口

| 维度 | 查询 | 成功检索 | URL | 正文 | 待审候选 |
|---|---:|---:|---:|---:|---:|
| upstream | 2 | 2 | 1 | 1 | 1 |
| downstream | 2 | 2 | 1 | 1 | 1 |
| competitors | 2 | 2 | 0 | 0 | 0 |
| investors | 2 | 2 | 1 | 1 | 1 |
| investments | 2 | 2 | 0 | 0 | 0 |
| people | 2 | 2 | 0 | 0 | 0 |
| products | 2 | 2 | 0 | 0 | 0 |
| capacity | 2 | 2 | 0 | 0 | 0 |
| counterevidence | 2 | 2 | 1 | 1 | 1 |

## 原文与候选

### 虚构测试：denial

- URL：https://source.example.invalid/denial
- 获取状态：FETCHED
- SHA-256：c7f85f90d3df3eb8f665d268dcdd9d97b2bc0905f5fb3144eca4f6d41e0fe22a
- 诊断：None

- **待审核**：星港芯片（虚构） → SUPPLIES → 远望服务器（虚构）
  - 阶段/极性：UNKNOWN / NEGATED
  - 引文区间：[39, 87]；标记：['modality_or_counterevidence']
> 星港芯片（虚构）否认已成为远望服务器（虚构）的量产供应商，并称双方仅开展技术交流，没有采购订单。

### 虚构测试：ownership

- URL：https://source.example.invalid/ownership
- 获取状态：FETCHED
- SHA-256：35ece126ff55de572b71d16bb27a475518ee9aa76d6be0ae021746de130369bc
- 诊断：None

- **待审核**：晨星基金（虚构） → OWNS → 星港芯片（虚构）
  - 阶段/极性：UNKNOWN / ASSERTED
  - 引文区间：[39, 81]；标记：['ownership_or_competition_requires_review']
> 晨星基金（虚构）持有星港芯片（虚构）8%的股权，星港芯片（虚构）仍由其创始团队控制。

### 虚构测试：reprint

- URL：https://source.example.invalid/reprint
- 获取状态：FETCHED
- SHA-256：0d59d030e473c12771fb464fb187bdc5eb5b4398ecb0d0028f2801ceaeaffd87
- 诊断：None

- **待审核**：星港芯片（虚构） → SUPPLIES → 云帆计算（虚构）
  - 阶段/极性：TESTING / ASSERTED
  - 引文区间：[39, 87]；标记：['modality_or_counterevidence', 'model_disagreement']
> 星港芯片（虚构）已向云帆计算（虚构）交付海潮一号（虚构）试产样品，仍处于客户测试阶段，尚未量产。

### 虚构测试：sample

- URL：https://source.example.invalid/sample
- 获取状态：FETCHED
- SHA-256：0d59d030e473c12771fb464fb187bdc5eb5b4398ecb0d0028f2801ceaeaffd87
- 诊断：None

- **待审核**：星港芯片（虚构） → SUPPLIES → 云帆计算（虚构）
  - 阶段/极性：TESTING / ASSERTED
  - 引文区间：[39, 87]；标记：['modality_or_counterevidence', 'model_disagreement']
> 星港芯片（虚构）已向云帆计算（虚构）交付海潮一号（虚构）试产样品，仍处于客户测试阶段，尚未量产。

## 限制

搜索成功、原文可定位和模型一致均不表示事实已确认。
同源归并提示不证明独立性。时间范围是搜索提示，正文事件时间仍需审核。
本版本按调用边界检查总时长；在途请求受单次超时约束。浏览器抓取预算计调用次数，不计子资源 HTTP 请求。
无标签时质量为 UNASSESSED；合成演示不证明真实模型质量。
