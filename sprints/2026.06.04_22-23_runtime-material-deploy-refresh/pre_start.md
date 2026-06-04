# Pre Start: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给低成本小车后，小车能沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。本轮不扩成新的 UI/runbook 或底盘运动，而是先把 O3/O7 的现场 runtime 证据链打通：operator 能在 PC/8787 触发只读 scan proof refresh，并拿到 fresh `/scan` proof 或明确 root cause。

## 上轮状态

- 上一轮 `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/` 已完成本地 `POST /api/radar/scan-proof/refresh` software guard、PC 同源代理和 UI 入口。
- Robot Software 本地验证：`python3 -m unittest onboard.scripts.test_upper_robot_api` 28 tests OK；`python3 -m compileall -q onboard/scripts` 通过。
- Full-Stack 本地验证：workstation 99 tests、build、lint 通过。
- Hardware 复核：只读链路未调用 `/api/base/manual`、未发送 `T=1/T=13/T=130/T=131`、未发布 `/cmd_vel`，仍保持 `safe_to_control=false`。
- 现场阻塞：`POST http://192.168.1.11:8787/api/radar/scan-proof/refresh` 返回 HTTP 405，`GET /api/radar/status` controls 仍只有 `start/stop`，说明上位机 8787 尚未部署新 route。

## 最近 2 轮 blocker scan

| Sprint | blocker root cause | 本轮处理 |
| --- | --- | --- |
| `20-21_runtime-material-followup` | live 8787 hook 仍是 `dry_run_stub/no_command_configured`，且 scan proof collector 修复未同步到上位机；O2 缺真实/受控图片 manifest。 | 本轮只处理 O3/O7 deploy refresh，不重复 O2 找图。 |
| `21-22_runtime-material-runtime-hooks` | 本地 refresh 合同完成，但 live 8787 未部署 route，`POST /api/radar/scan-proof/refresh` 返回 405。 | 本轮把 405 作为主抓手，确认安全 reload/service 路径并部署。 |

本轮没有继续消费 O5/O6 的 URL/token/cloud 配置 blocker；若 deploy refresh 再次因为未知 service/reload 权限失败，需要在 `final.md` 标记为 `blocker_root_cause: upper_8787_reload_path_unknown`，下一轮不得无意识第三次重复消费。

## 本轮目标

聚焦 KR-O3/O7-Scan-Proof-Refresh-Deploy：

1. 确认 `192.168.1.11:8787` 的实际启动方式、service 名称、reload/restart 安全路径和回滚策略。
2. 在不触碰底盘运动、不提升 `safe_to_control` 的前提下，把本地已验证的 upper refresh route 部署到上位机 runtime。
3. 通过 live 8787 `POST /api/radar/scan-proof/refresh` 取得 fresh scan proof，并用 `/api/radar/scan-proof/latest` 回读 artifact。
4. 经 PC 同源 `POST /api/o7/direct-upper/radar/scan-proof/refresh` 触发一次同源 operator workflow，保留同一 `evidence_ref`。

## 非目标

- 不执行 `/api/base/manual`、PC WASD、`/cmd_vel`、低速 pulse、turn smoke 或 stop-first HIL。
- 不把 O2 真实/受控电梯图片 manifest 纳入本轮交付；只把它保留为下一步风险。
- 不推进 SLAM `/map`、AMCL、Nav2 lifecycle 或固定路线实跑；只有 fresh `/scan` proof 通过后再进入这些 KR。
- 不处理 O5/O6 production URL、remote bearer token、DB/queue、OSS/CDN 或 4G/公网材料。
- 不修改 `OKR.md`、`tech-done.md`、`side2side_check.md` 或 `final.md`；这些等 IC 返回证据后再收口。

## Owner

- Robot Software Engineer：主责确认上位机 8787 service/reload 路径，部署 upper refresh route，验证 live POST/latest readback。
- User Touchpoint Full-Stack Engineer：配合确认 PC adapter/runtime 指向部署后的 8787，经 PC 同源入口触发 refresh 并记录 operator 可读结果。
- Hardware Infra Engineer：只读咨询，复核本轮 deploy/refresh 不触碰底盘 `/dev/ttyS5`、运动命令、HIL 或 `safe_to_control=true`。
- Product Manager / OKR Owner：本轮只补齐 pre_start/prd/tech-plan 和 owner note；IC 返回后再做 evidence type、OKR 是否涨分和历史归档判断。

## 验收口径

- 必须拿到 live `POST /api/radar/scan-proof/refresh` 非 405 结果；成功时 evidence type 才可能从 `software_guard` 升级到 `robot_runtime_material`。
- 必须回读 `/api/radar/scan-proof/latest`，并证明 artifact freshness、timestamp、topic summary 与本次 `evidence_ref` 对齐。
- 必须经 PC 同源入口触发或证明 PC runtime 仍 blocked，不能只停留在 SSH/curl 手工调用。
- 必须保留 `safe_to_control=false`、`robot_control_executed=false`、未调用底盘运动接口的证据。
- 如果 route 部署成功但 ROS2 topic 为空，应收口为 `deployed_route_ok_but_no_fresh_scan_topic`，不得写成 O3 runtime 完成。

## 风险和阻塞

- 上位机实际 service/reload 路径未确认，盲目 kill/restart 可能中断现场 runtime；必须先确认服务名、启动命令和回滚路径。
- 8787 部署后仍可能没有 ROS2 `/scan` topic；这会证明 route 已部署，但仍不能证明 O3 map/Nav2 能推进。
- PC adapter 可能仍指向旧 route 或旧 runtime bundle；必须检查 adapter version 和同源 proxy 返回。
- O2 图片 manifest、O1 stop-first HIL 仍是下一步真实材料风险，但不扩大本轮范围。
