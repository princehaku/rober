# sprint_type: micro

## 功能点设计 / 验收边界

本轮目标是 `PC no-motion readiness chain`：通过 workstation PC 固定代理与真实上位机
`http://192.168.1.11:8787` 串起只读/受控 no-motion helper 证据链。

本轮不是自动导航成功，不是真实移动成功，不是送达成功，不是 `/cmd_vel`、
`/api/base/manual`、NavigateToPose 或 map reset 放开。

普通用户首屏必须继续保持 `.simple-user-console` 的 `Rober 小车控制台` + 五卡片简易
风格；高级能力只允许留在默认关闭的高级诊断。

允许验证的 no-motion readiness 范围：

- 连接 / summary 读回
- 雷达 proof refresh 或 latest/readback 读回
- 地图 proof refresh、map list，以及在风险可控时的 map start/save no-motion lifecycle
- localize reset 固定代理
- nav2 no-motion proof refresh / path generation check
- SSH cleanup / readback，确认无 `/cmd_vel`、无 `/api/base/manual`、无 `/dev/ttyS5`
  占用、无 helper/ROS 残留

如果真实 smoke 暴露 PC proxy 或状态解释缺口，才允许做最小代码修复；若无需修复，
则本轮只更新文档与证据。

## 实际改动

- 更新了 [`docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md)
  的最新状态段，补上本轮 no-motion readiness chain 的实测结论和 cleanup 边界。
- 补充本 sprint 本地首屏 smoke artifact：
  [`/Users/m1/apps/rober/sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/pc_plain_home_smoke_vitest.json`](/Users/m1/apps/rober/sprints/2026.06.11_16-20_pc_no_motion_readiness_chain/artifacts/pc_plain_home_smoke_vitest.json)
  作为 `.simple-user-console`、`Rober 小车控制台`、五卡片和禁词收口的本地 DOM smoke 证据。
- 未改 `pc-tools/workstation/src/**`、`pc-tools/workstation/test/**`、`onboard/**` 或任何硬件配置。

## 验证结果

- 真实 PC proxy no-motion chain 已由前一 worker 在 `http://127.0.0.1:18794`
  对真实上位机 `http://192.168.1.11:8787` 执行，逐步 artifact 已写入
  `artifacts/raw/01_*` 到 `artifacts/raw/15_*`。
- 雷达 proof refresh：
  - `remote_http_status=200`
  - `latest_proof_status=raw_packets_parsed`
  - `evidence_ref=o1-lidar-scan-proof-1781166326352`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
  - `lifecycle_running=false`，因此这仍是 no-motion readiness，不是持续运行或运动证明。
- 地图 proof / lifecycle：
  - `map proof refresh` 返回 `latest_proof_status=map_once_artifact_metadata_observed`
    且 `map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true`。
  - `map list` 从 `map_count=24` 变为 `map_count=26`，after 列表包含
    `pc_no_motion_20260611_162507.yaml`；`no_motion_readiness_chain_summary.json`
    中 `created_entry_present=false` 是派生摘要字段不一致，原始 after list 作为更强证据。
  - `map start` 与 `map save` 都返回 `command_result.mode=map_lifecycle_proof_helper`、
    `executed=true`、`ok=true`，只代表 no-motion lifecycle helper 被固定代理触发。
- 定位 reset：
  - `latest_proof_status=nav2_no_motion_localization_runtime_observed`
  - `evidence_ref=o10-amcl-nav2-runtime-1781166505381`
  - `initialpose_published=true`
  - `amcl_pose_observed=true`
  - `managed_runtime_cleanup_ok=true`
  - `localization_reset_observed=true`
- Nav2 no-motion path generation：
  - `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`
  - `evidence_ref=o10-amcl-nav2-runtime-1781166547645`
  - `managed_runtime_started=true`
  - `initialpose_published=true`
  - `path_generation_requested=true`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=18`
  - `planner_server_active=true`
- cleanup/readback：
  - `cmd_vel_topic_count=0`
  - `base_manual_http_count=0`
  - `/dev/ttyS5` 的 `lsof/fuser` 无输出
  - `radar_helper_ps`、`nav_helper_ps`、`cmd_vel_publishers` 无输出
  - 本轮未调用 map reset、`/api/base/manual`、NavigateToPose 或任何非 stop 运动。
- 本地首屏 smoke 使用现成的 `pc-tools/workstation/test/App.test.ts` 中
  `renders Robot Control V1 by default with Robot API proxy and locked command boundary`
  断言，Vitest JSON 报告成功写出，结果为 1 个测试通过、0 个失败，`success=true`。
- smoke 结果确认：
  - `.simple-user-console` 首屏包含 `Rober 小车控制台`
  - 五张普通卡片存在：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`
  - 默认首屏禁词未出现，包括 `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`
    以及工程诊断词
- 远端 no-motion readiness 证据链已在前一轮 worker 产出，本轮只做收口，不重跑真实上位机。
- `git diff --check` 已在收口末尾执行通过。

## 剩余风险

- 本轮仅证明 PC 侧 no-motion readiness 和首屏契约，没有把任何能力升级为自动导航、
  真实移动、真实送达或 HIL pass。
- `map start/save`、`localize reset`、`nav2 path generation` 和 `cleanup` 仍属于 no-motion
  readiness 证据，不等于真实底盘控制放行。
- 远端实机链路没有在本轮重新执行；若后续上位机状态漂移，需要再次以真实 proxy smoke
  复核，但不能把这次收口当成移动或交付成功。
