# Sprint 2026.05.12_10-11 Phone UI Readiness Gate - Side-by-Side Check

## 状态

- 阶段：side2side_check
- 收口时间：2026-05-12 11:16 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 证据边界：`software_proof_docker_local_phone_ui_readiness_gate`
- Product acceptance：通过，限 O5 本地/Docker phone readiness gate。

## 用户价值和产品北极星

北极星仍是普通用户只用手机完成 trash delivery 的发车、状态查看、异常理解和人工恢复。本轮没有交付生产手机 app，但已经把本地 fallback operator 入口从 debug 字段堆叠推进到“能不能继续、为什么不能、下一步怎么做”的 phone-first readiness gate。

## OKR 映射

- O5 KR1：通过 `/api/status.phone_readiness` 和首屏 readiness panel，补齐连接/状态/发车前判断/异常恢复的用户入口。
- O5 KR4：把 local delivery、action permissions、local/mock `remote_readiness`、可选 preflight 和 backup/restore drill 摘要聚合成 phone-safe 诊断摘要。
- O5 KR5：普通用户看到中文优先的 `safe_phone_copy`、`recovery_hint` 和 `support_level`，不需要理解 ROS2、串口、ACK 或云实现细节。
- O5 KR7：首屏 phone-first readiness gate 已落地为本地 fallback 调试入口；生产手机 app、真实手机设备/浏览器验收和完整视觉质量仍未完成。
- O6：只消费既有 remote readiness / preflight / backup restore 字段，不新增 O6 生产云或 4G 证据。
- O1/O2/O3/O4：没有真实硬件、Nav2/fixed-route、视觉、WAVE ROVER 或 HIL 证据，不更新。

## Side-by-Side 验收

| PRD P0 验收项 | 实际证据 | Product 判定 |
| --- | --- | --- |
| 手机入口聚合 remote readiness、backup/restore/preflight、delivery command state 和恢复提示 | `operator_gateway_http.py` 新增 `trashbot.phone_readiness.v1`；`/api/status` 兼容新增 `phone_readiness`；HTML 首屏新增 readiness panel。 | 通过 |
| 覆盖 `ok`、`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` | `test_operator_gateway_http.py` 覆盖 stale/pending/auth/cloud/malformed；ACK 不写成 delivery completed。 | 通过 |
| backup/restore/preflight 缺失、blocked、local valid 均保持 local/Docker proof 边界 | `_copy_gate` / `_unknown_gate` 保守映射为 `not_run` 或 `unknown`；`not_proven` 保留生产 app、真实云/4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL。 | 通过 |
| collect / confirm_dropoff / cancel 的 command pending/ACK/failed/ignored 不与 delivery success 混淆 | `phone_readiness.local_delivery.state` 保留真实 local 状态；测试确认 remote ok/ACK 不等于 `completed`。 | 通过 |
| 输出不泄露敏感字段或硬件字段 | 新增文档明确不得展示 raw JSON、凭证、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`；静态测试覆盖 schema/UI 字符串。 | 通过，仍需后续真实端到端脱敏抽样 |
| targeted unittest、py_compile、scoped diff check | Worker 报告 `Ran 68 tests in 15.452s OK`、py_compile exit 0、scoped diff check exit 0；本轮 Product acceptance 再跑 sprint/OKR scoped diff check。 | 通过 |

## 做什么 / 不做什么

已做：

- 落地本地 operator phone readiness gate。
- 保持 `/api/status` 向后兼容，只新增可忽略的 `phone_readiness` 字段。
- 同步更新 `docs/product/mobile_user_flow.md`、`docs/product/remote_4g_mvp.md` 和 `docs/interfaces/ros_contracts.md`。
- 将 OKR O5 从约 33% 保守上调到约 38%。

未做：

- 不声明生产手机 app。
- 不声明真实手机设备或浏览器验收。
- 不声明真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量或生产账号体系。
- 不声明 Nav2/fixed-route 送达、WAVE ROVER 运动、串口反馈或 HIL。
- 不提升 O6 或 O1/O2/O3/O4。

## 风险、阻塞和证据链

- 真实手机 UI 的视觉质量、触控尺寸、首屏加载时间和主流 iPhone/Android 浏览器适配仍未实测。
- 本地 operator HTML 仍是 fallback 调试入口，不能替代正式手机 web/app。
- `cloud_preflight` 与 `backup_restore` 目前是可选输入摘要；后续要接真实 artifact 生命周期时，需要 Full-stack/Robot 再定义路径和刷新策略。
- ACK 仍只是 command envelope 处理证据，不能作为 delivery success 或机器人运动证据。
- 下一步 O5 应转向真实手机浏览器验收与生产 phone app 外观/交互，而不是继续只堆 backend readiness 字段。
