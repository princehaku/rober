# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - Final

## 状态

- 阶段：final
- Product Owner：`product-okr-owner`
- 收口时间：2026-05-12 20:38 CST
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`

## 最终结论

本轮完成 O5 的 local/Docker phone support handoff software proof。相对上一轮 `phone_task_flow_readiness`，这次不是继续补 happy path，而是补失败后交接：用户在 blocked、等待 ACK、失败或需要人工接管时，可以打开 Support Handoff，复制中文优先、脱敏、可追踪的 support bundle。

O5 进度按保守口径从约 48% 上调到约 50%。理由是本轮闭合了 O5 KR4/KR5/KR7 的失败交接和支持摘要缺口，但证据仍只来自 local/Docker API/static/unit compatibility fence。O6 保持约 49%，O1/O2/O3/O4 不提升。

## 实际完成

- Task A / Full-stack：新增 `trashbot.phone_support_bundle.v1`，在 `/api/status.phone_support_bundle`、`/api/status.phone_readiness.phone_support_bundle`、`/api/diagnostics.phone_support_bundle` 暴露同口径 phone-safe support bundle；本地 fallback HTML 增加 Support Handoff 入口和中文优先 `safe_copy`；主操作被 command safety 阻断时 Diagnostics/Support Handoff 仍可打开。
- Task B / Robot fence：新增 remote bridge compatibility fence，确认 support metadata 不污染 `trashbot.remote.v1` command/status/ack envelope；metadata-only blocked response 不触发 robot action、不 ACK、不推进/持久化 cursor；diagnostics support bundle 脱敏且最终 zero skips。
- 文档同步：`docs/product/mobile_user_flow.md` 与 `docs/interfaces/ros_contracts.md` 路径真实存在，Task A 已同步用户流程和接口 contract。
- Product closeout：已创建 `side2side_check.md`、`final.md`，并更新 `OKR.md` 当前快照。

## 验证结果

Task A 验证证据：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
Ran 48 tests in 20.053s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py
exit 0
```

Task B 验证证据：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 76 tests in 18.878s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0
```

Product Closeout 验收命令：

```text
git diff --check -- OKR.md sprints/2026.05.12_22-23_phone-support-bundle-gate/side2side_check.md sprints/2026.05.12_22-23_phone-support-bundle-gate/final.md
exit 0, no output
```

## 失败定位

- Task A 首轮测试锚点与既有 ACK 文案不一致，已修正测试锚点并保持运行时 ACK 语义不变；第二轮针对 `/api/status` support refs 的断言过宽，已收敛到 status 实际可提供的安全字段。
- Task B 首轮 finalization 把 `not_proven.hardware_or_serial_details` 误判为 serial 泄露，已改为结构化检查 `support_refs` 和输出正文中的真实敏感值。
- Product Closeout 未发现新增失败；最终以 scoped `git diff --check` 为本阶段围栏。

## 剩余风险和未完成事项

- 没有真实手机设备、production app、真实手机 Safari/Chrome 或普通用户实机验收。
- 没有真实云/4G、OSS/CDN 实流量、生产 DB/queue、生产账号或远程手机流程。
- 没有 Nav2/fixed-route 实跑、WAVE ROVER、真实串口、HIL 或真实送达。
- Support Handoff 是 local/Docker phone support handoff software proof，不是正式售后系统或生产用户闭环。

## 下一步建议

- 若仍是 Docker-only 环境，按 live `OKR.md` 继续优先 O6 的最低可行动生产化前置 gate，但保持 `production_ready=false` 和真实云/4G缺口口径。
- 若能提供真实手机设备，优先补 O5 的 physical phone Safari/Chrome 验收、安装/runtime 证据和普通用户实机流程。
- 若能提供云/4G 条件，优先补 O6 的真实公网入口、生产 DB/queue、真实 4G/SIM 或 OSS/CDN 实流量。
