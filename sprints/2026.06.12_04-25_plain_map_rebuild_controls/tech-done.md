# 2026-06-12 04:25 Plain Map Rebuild Controls

sprint_type: micro

## 实际改动

- 不使用 subagent，主会话直接完成实现、验证和留档。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通 `.simple-user-console` 的 `地图` 卡片新增 `重新建图` 与 `保存地图`。
  - 两个按钮复用现有固定代理：`/api/robot-control/map/start` 与
    `/api/robot-control/map/save`。
  - 普通提示只显示 `重新建图已返回；再查看地图质量。` 或
    `保存地图已返回；再查看地图质量。`
  - `map_name`、`artifact_path`、HTTP、command_result、proof、raw/readback 仍只在默认
    关闭的高级诊断中展示。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏契约：允许 `重新建图` 与 `保存地图`，继续禁止 `开始建图`、`Start`、
    `Reset`、`HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、速度和点动。
- 同步更新：
  - `docs/product/pc_tools_workstation.md`
  - `docs/navigation/fixed_route_workflow.md`
  - `docs/hardware/board_sensor_stack_smoke.md`

## 验证结果

- 本地前端测试：
  - `cd pc-tools/workstation && npm run test -- App.test.ts`：17 tests passed。
- 真实 PC proxy `POST /api/robot-control/map/start?baseUrl=http://192.168.1.11:8787`：
  - artifact: `artifacts/01_pc_proxy_plain_rebuild_map_start.json`
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `status=loaded_fail_closed_summary`
  - `command_result.mode=map_lifecycle_proof_helper`
  - `command_result.executed=true`
  - `command_result.ok=true`
  - `hard_dangerous_true_fields=[]`
- 上位机 readback：
  - artifact: `artifacts/02_upper_map_proof_latest_after_plain_rebuild.json`
  - latest evidence: `o3-map-lifecycle-1781190084998`
  - `scan_once_observed=true`
  - `map_once_observed=true`
  - `map_file_observed=true`
  - `map_metadata_observed=true`
- 地图质量 readback：
  - artifacts:
    - `artifacts/03_upper_map_list_after_plain_rebuild.json`
    - `artifacts/05_pc_proxy_map_list_after_plain_rebuild.json`
  - `map_count=26`
  - `checked_yaml_count=13`
  - `usable_map_count=0`
  - `no_free_cell_map_count=13`
  - `map_quality_summary.status=no_free_cells`
- Browser 验证：
  - artifact: `artifacts/04_browser_plain_map_controls.json`
  - 普通首屏存在 `.simple-user-console`。
  - 高级诊断默认关闭。
  - 地图卡片显示 `刷新地图 / 地图列表 / 重新建图 / 保存地图`。
  - 首屏未出现 `Nav2`、`proof`、`HIL`、`/cmd_vel`、`/api/base/manual`、`Start`、
    `Reset`、速度或点动。
- 上位机收尾：
  - `trashbot-upper-robot-api.service=active`
  - `trashbot-local-webrtc-camera.service=active`
  - 未观察到长期 `o3_map_lifecycle_proof`、`learn.launch`、`slam_toolbox` 或 LiDAR helper 残留。
  - `/dev/ttyS5` 与 `/dev/ttyACM0` 无占用输出。

## 剩余风险

- 本轮证明 PC 普通页面可以触发 no-motion 建图窗口和保存链路，不证明已经采到可导航地图。
- 真实地图质量仍为 `free=0`，因此定位移动、fixed-route execution 和 NavigateToPose 仍不能放行。
- Camera `/dev/video1` 首帧 timeout 仍未解决；非 stop 运动 gate 仍缺可见图传、外部视频、左右轮非零反馈和 LiDAR motion delta。
- 本轮没有调用 `/api/base/manual`、没有发布 `/cmd_vel`、没有执行 NavigateToPose、没有写 WAVE ROVER UART `/dev/ttyS5`。
