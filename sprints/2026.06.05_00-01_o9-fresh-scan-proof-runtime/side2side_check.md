# Side2Side Check: O9 Fresh Scan Proof Runtime

## sprint_type

sprint_type: epic

## 对照结论

本轮目标是 O9 fresh scan proof runtime：让 live 8787 refresh 产出 fresh `/scan` proof，并支撑 O3/O7 的真实 runtime 材料。当前 Product/OKR 对照结论是：不通过产品验收，不涨 O9/O3/O7。

| 验收项 | 当前事实 | Product 判定 |
| --- | --- | --- |
| live `POST /api/radar/scan-proof/refresh` 不再 405 | 早前已解除 405，HTTP 200 可返回 blocked/latest artifact | 只能说明 route 部署问题曾被解除，不等于 fresh proof |
| LiDAR-only smoke 可观察 `/scan`、`/lidar/raw_packet`、TF | Robot Software 已记录受控 smoke 可观察，且 `safe_to_control=false` | 可作为方向材料，不能替代普通 refresh artifact |
| API-managed runtime hook | 本地 diff 涉及 `upper_robot_api.py`、`test_upper_robot_api.py`、`docs/interfaces/lidar_ros2_closed_loop.md`；Robot Software 复跑 unittest/compileall/diff-check 通过；hook 已部署到 upper 并配置 systemd drop-in | `evidence_type=software_guard` + runtime blocker 收窄，不能单独涨产品 Objective |
| 远端 fresh refresh artifact | live refresh/latest 已返回 `partially_observed`：`scan_once=true`、`raw_packet=true`、`scan_hz=false`、`tf=false`、`all_required=false` | 未通过；缺 scan continuity 和 TF |
| 底盘安全边界 | 本轮不发 `/cmd_vel`，不调用 `/api/base/manual`，保持 `safe_to_control=false` | 边界正确，但不构成 HIL 或导航能力 |

## OKR 涨分判定

- O9：不涨分。没有远端 fresh `/scan` refresh artifact，API hook、HTTP 200、本地测试和 smoke 都不能包装成 O9 完成。
- O3：不涨分。没有证明 SLAM `/map`、AMCL、Nav2 消费或固定路线；fresh `/scan` 也未通过普通 live refresh 闭环。
- O7：不涨分。没有 PC/operator 触发 live runtime refresh 并展示 fresh artifact 的闭环材料。
- O8：最多记录 owner timeout/process evidence；本轮不建议改 OKR 百分比。

## evidence_type

- `software_guard`：API-managed runtime hook 本地 diff、本地 unittest/compileall/diff-check 通过、接口文档更新。
- `blocked_with_root_cause`：live latest artifact 已经从全缺失推进到 partial，但 `scan_hz=false`、`tf=false`，因此 fresh proof 未完成。
- 尚未成立：`robot_runtime_material`。成立条件必须是 live 8787 latest artifact 同时包含 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、collector log、artifact timestamp、`safe_to_control=false` 和 not_proven 边界。

## owner timeout / blocker

- 第一个 Robot Software worker 超时/中断，未验证、未部署、未形成取证材料。
- 第二个 Robot Software worker 本地实现与测试报告已有，但未完成最终 diff-check、远端部署、live refresh/latest 取证，也未自行更新 `tech-done.md`。
- 后续验收 worker 完成部署和最终只读取证，确认 blocker 已收敛为 `scan_continuity_not_observed` 和 `base_link -> laser_frame` TF 未观测。
- 当前 blocker 不是产品方向不清，而是 LiDAR runtime 在 refresh 生命周期内没有同时满足 `/scan` hz 和 TF。

## 剩余风险

- API-managed runtime hook 已部署并启用，但 LiDAR driver/static TF 仍未在普通 refresh 下全量通过。
- 下一轮需要把 `scan_hz=false` 与 TF 缺失拆成单命令验收，避免再次把 remote deployment 和 runtime diagnosis 混在一起。
- 本地 unit test 不能证明真实 `/scan` refresh、SLAM `/map`、Nav2、PC workflow、底盘 HIL 或 `safe_to_control=true`。
- 若下一轮继续没有 fresh proof，应把任务切成单命令验收：deploy/reload、runtime command status、refresh artifact、PC readback 四段分别取证。
