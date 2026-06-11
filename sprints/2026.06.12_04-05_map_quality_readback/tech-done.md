# 2026-06-12 04:05 Map Quality Readback

sprint_type: micro

## 实际改动

- 不使用 subagent，主会话直接完成本轮实现、验证和留档。
- `onboard/scripts/upper_robot_api.py`
  - `/api/map/list` 增加只读 YAML/PGM 地图质量分析。
  - 对每个 YAML 地图输出 `quality.cell_counts.free/unknown/occupied/other`、
    `has_free_cells` 和 `navigation_quality`。
  - 顶层输出 `map_quality_summary`、`map_usable_for_navigation`、
    `map_needs_rebuild`，让 PC 能在 Nav2 proof 前提示重新建图。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC map lifecycle proxy 白名单提取上位机地图质量摘要。
  - 代理失败或旧上位机缺字段时返回 `not_loaded` 默认结构，不把未知状态误判为可导航。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 增加 `RobotControlMapQualitySummary` 和 map lifecycle response 质量字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通 `.simple-user-console` 地图卡片在 `map_needs_rebuild=true` 时显示
    `当前地图不可导航，需要重新建图。`
  - 默认关闭的高级诊断增加短字段 `map quality`，显示 status/usable/no_free。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 free=0 YAML/PGM 的本地单元测试。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 增加 PC proxy 与普通首屏提示回归。
- 同步更新：
  - `docs/product/pc_tools_workstation.md`
  - `docs/navigation/fixed_route_workflow.md`
  - `docs/hardware/board_sensor_stack_smoke.md`

## 验证结果

- 本地单元/构建：
  - `python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_map_lifecycle_proof_helper`：37 tests OK。
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
  - `cd pc-tools/workstation && npm run test -- catalog.test.ts App.test.ts`：2 files / 94 tests passed。
- 真实上位机部署：
  - 已 scp `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
  - 本地/远端 sha256 均为 `9ca02ee288404517e8051588fadcb9bc250eb132113d074b6e0b69a503a0760f`。
  - `trashbot-upper-robot-api.service=active`。
- 真实上位机 `/api/map/list`：
  - artifact: `artifacts/01_upper_map_list_quality.json`
  - `map_count=26`
  - `checked_yaml_count=13`
  - `usable_map_count=0`
  - `no_free_cell_map_count=13`
  - `map_quality_summary.status=no_free_cells`
  - `map_usable_for_navigation=false`
  - `map_needs_rebuild=true`
- PC fixed proxy `GET /api/robot-control/map/list?baseUrl=http://192.168.1.11:8787`：
  - artifact: `artifacts/02_pc_proxy_map_list_quality.json`
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `map_quality_summary.status=no_free_cells`
  - `map_needs_rebuild=true`
  - `hard_dangerous_true_fields=[]`
- Browser 验证：
  - artifact: `artifacts/03_browser_plain_map_quality.json`
  - 本机 Vite `http://127.0.0.1:5179/` + PC API `http://127.0.0.1:8787`。
  - 填入 `http://192.168.1.11:8787` 后点击“地图列表”。
  - 普通首屏存在 `.simple-user-console`，高级诊断默认关闭。
  - 地图卡片显示 `当前地图不可导航，需要重新建图。`
  - 首屏未出现 `Nav2`、`proof`、`HIL`、`/cmd_vel`、`/api/base/manual`。

## 剩余风险

- 本轮只证明 PC 和上位机能读出地图质量 blocker，不证明已经完成重新建图。
- 当前真实上位机 13 张 YAML 地图仍全部 `free=0`，不能进入真实定位移动或 fixed-route execution。
- Camera `/dev/video1` 首帧仍是独立 blocker；非 stop 运动 gate 仍缺可见图传、外部视频、左右轮非零反馈和 LiDAR motion delta。
- 本轮没有调用 `/api/base/manual`、没有发布 `/cmd_vel`、没有执行 NavigateToPose、没有写 WAVE ROVER UART `/dev/ttyS5`。
