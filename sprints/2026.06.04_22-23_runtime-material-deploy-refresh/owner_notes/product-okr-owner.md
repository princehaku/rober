# Product OKR Owner Note: Runtime Material Deploy Refresh

## 本轮核心抓手

KR-O3/O7-Scan-Proof-Refresh-Deploy：把上一轮已经本地验证的 scan proof refresh route 部署到真实上位机 `192.168.1.11:8787`，并通过 PC 同源入口取得 fresh scan proof。这个抓手服务 O3 的建图/定位/Nav2 前置 runtime material，也服务 O7 的 operator workflow。

## 方向判断

继续，但收窄。O2/O3 仍是产品主线最低缺口；本轮选择 O3/O7，是因为 21-22 已把下一步收敛成现场 8787 HTTP 405 部署问题。O2 图片 manifest 和 O1 stop-first HIL 均保留为风险/下一步，不扩大进本轮。

## Product 验收边界

- 可接受：live deployed refresh route、fresh `/scan` proof、latest artifact、PC 同源触发、`safe_to_control=false`、明确 blocker root cause。
- 不可接受：只给本地测试、旧 artifact、HTTP 405、SSH 手工旧路径、UI 按钮截图或未标注 evidence type 的材料。
- 不可涨分：没有 fresh runtime material 时，不调整 O3/O7；没有 IC final 证据时，不改 `OKR.md`。

## 后续收口规则

1. IC 返回后先核对 owner notes、命令输出和 artifact freshness。
2. 再更新 `tech-done.md`、`side2side_check.md`、`final.md`。
3. 只有 `robot_runtime_material` 成立时，才建议 O3/O7 小幅涨分；否则写成 `blocked_with_root_cause`。
4. 已完成 KR 只有在 `final.md` 有验收结论后才能进入 `docs/process/okr_progress_log.md` 或 `OKR.md` 历史区，本轮计划阶段不做历史归档。

## Product 收口追加

- 收口时间：2026-06-04 22-23 CST。
- 方向判断：继续，但 O3/O7 不涨分；O8 可按治理进展维持约 44%。
- 核心事实：live `POST /api/radar/scan-proof/refresh` 已从 HTTP 405 变为 HTTP 200，部署 blocker 解除。
- 不涨分原因：proof result 仍是 `blocked_or_not_observed`，blocker 为 `ros2_command_unavailable` 和 `upper_api_scan_not_proven`，没有 fresh `/scan` runtime material。
- O7 判断：PC fail-closed blocker display 是有效 software guard，但未做 live smoke，也不证明 operator runtime workflow。
- 下一步：修上位机 ROS2 runtime environment / collector command path，恢复 `ros2` 命令或切到正确 ROS2 容器内 collector，再复测 refresh；之后才进入 SLAM/map/AMCL/Nav2。
