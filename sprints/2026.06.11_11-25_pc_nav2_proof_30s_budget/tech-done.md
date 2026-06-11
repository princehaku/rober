# PC Nav2 Proof 30s Budget

## Sprint Type

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 PC fixed proxy 的 Nav2 no-motion path proof body 从 20s 对齐到 30s：
    - `timeout_s=30`
    - `managed_timeout_s=30`
    - `path_generation_timeout_s=30`
  - 浏览器仍只能传 `baseUrl`，不能传自定义 timeout、goal 或任意 Robot API 参数。
  - `computeRobotProofRefreshTimeoutMs` 未改逻辑；新 body 的估算值为 `30+30+30+30=120s` 加 `30s` margin，但仍受 `timeout_cap_ms=90000` 封顶，workstation 不会无限等待。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 Nav2 refresh 固定 POST body 为 30s。
  - 锁定 Nav2 fetch timeout 预算仍为 `90_000ms` cap。
- `pc-tools/workstation/test/App.test.ts`
  - 将普通首屏 DOM smoke artifact 写入本 sprint `artifacts/`。
  - 保持 `.simple-user-console` 禁词覆盖：`检查路径`、`Nav2`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual` 等不进入普通首屏。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 说明 30s 是 clean-baseline direct Robot API 在同一 no-motion contract 下的实测稳定窗口。
  - 明确该入口仍是 no-motion proof，不是 NavigateToPose、`/cmd_vel`、`/api/base/manual`、真实运动或 delivery success。

## 真实证据与 Artifact

- 普通首屏 smoke：
  - `artifacts/pc_plain_user_home_dom_smoke.json`
  - `forbidden_token_presence` 全部为 `false`，高级诊断默认关闭且仍保留 `check_path/nav_goal_preflight/hil_materials/proof_readback`。
- PC fixed proxy 请求记录：
  - `artifacts/pc_proxy_nav2_30s_request.json`
  - 记录浏览器传入的无效 body `{ timeout_s: 1, path_goal_x: 99 }` 仅作为 ignored body；期望 fixed proxy body 为 30s。
- 真实上位机 PC proxy smoke：
  - `artifacts/pc_proxy_nav2_30s_response_attempt_1.json`
  - `artifacts/pc_proxy_nav2_30s_smoke_summary.json`
  - 首轮成功，无需重试：
    - `proxy_status=refresh_forwarded`
    - `remote_http_status=200`
    - `last_result_status=refreshed`
    - `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`
    - `path_generated=true`
    - `path_generation_succeeded=true`
    - `path_point_count=31`
    - `planner_server_active=true`
    - `blocked_reasons=[]`
    - elapsed `46136ms`
- 真实上位机 cleanup readback：
  - `artifacts/remote_cleanup_readback_after_nav2_30s_smoke_final.log`
  - `process_readback_filtered` 为空，未见 `o10_amcl_nav2_runtime_proof/map_server/amcl/planner_server/lifecycle_manager/lidar_driver` 残留。
  - `fuser/lsof /dev/ttyS5 /dev/ttyACM0` 无输出，未见设备占用。
  - 临时 workstation API `127.0.0.1:18787` 已停止，停止后 `curl` 连接失败。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过；Vite build completed，`tsc` server/client 通过。
- `cd pc-tools/workstation && npm run test -- --run`
  - 通过；`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过；`eslint .` 无输出。
- `git diff --check`
  - 通过；无 whitespace error。

## 剩余风险

- 本轮证明 PC fixed proxy 的 30s no-motion path proof 能稳定消费真实上位机并生成路径；不证明真实 NavigateToPose、真实底盘运动、`/cmd_vel`、`/api/base/manual`、真实路线执行或 delivery success。
- 30s 是当前 clean-baseline 实测稳定窗口；如果后续地图、CPU 负载或 Nav2 lifecycle 变慢，仍需要重新采样并调整上位机 helper 或 PC cap，而不是开放浏览器自定义 timeout。
- 当前完成时间：2026-06-11 12:19:47 CST。
