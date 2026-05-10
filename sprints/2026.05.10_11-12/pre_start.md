# Sprint 2026.05.10 11-12 Pre Start

## 目标

- 继续 hourly OKR iteration，优先推进当前低完成度功能，而不是只做状态扫描。
- 本轮主攻 Objective 2：补齐 `TrashCollection` fixed-route 送达结果与 task record 的结构化复盘证据。

## Owner

- Robot Platform Engineer：行为层代码、回归测试和目标验证。
- Autonomy Algorithm Engineer：只读复核 fixed-route status JSON contract。
- Product Manager / OKR Owner：本轮收口、OKR 进度和 sprint 留档。

## 验收口径

- `delivery_mode=fixed_route` 的 `TrashCollection` 成功路径必须把 fixed-route status JSON 的关键字段保留到 `nav_results` / task record。
- 失败和 timeout 仍必须返回明确 `error_code`、`result_code` 和 task record。
- 测试只做护栏，至少跑行为目标测试和完整 smoke。

## 风险

- 本轮不做真实 Nav2 / fixed-route 行驶，不宣称实车闭环完成。
- `AGENTS.md` 已有 unrelated 修改，本轮不得误提交。
