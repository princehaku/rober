# 2026.06.27 14:50 PC 自由移动面板 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在相机或雷达未 ready、且地图记录未启动时，把普通首屏建图操作卡标题切为 `自由移动 / 建图`。
  - 同步把操作状态行切为 `自由移动状态`，明确当前没有运动发布、低速自移动不依赖雷达新鲜度、建图另看相机和雷达。
  - 地图记录启动或传感器满足建图验收口径时，仍保留原 `扫地式建图` 流程。
- `pc-tools/workstation/test/App.test.ts`
  - 增加相机首帧失败、雷达不 ready 的 live 形状断言，锁定标题、说明和状态行。
- `docs/product/pc_tools_workstation.md`
- `docs/navigation/free_roam_autonomy.md`

## 验证结果

- 已通过：`npm test -- --run App.test.ts -t "splits free movement from mapping acceptance"`
- 已通过：`npm test`，291 个测试通过。
- 已通过：`npm run build`，Vite 仍有既有 chunk size 警告。
- 已通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，PC Node 仍监听 `*:7001`。
- 已通过：只读 `GET /api/robot-control/summary?robot_base_url=http://192.168.1.11:8787`：
  - `camera.status=source_first_frame_failed`
  - `camera.source_usage_status=not_in_use`
  - `camera.source_usage_owner_count=0`
  - `lidar.latest_scan_proof_fresh=false`
  - `free_roam_autonomy_start_ready=true`
  - `free_roam_autonomy_runtime.artifact_only=true`
  - `free_roam_autonomy_runtime.cmd_vel_publish_enabled=false`
  - `free_roam.mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`
- 已通过：`grep -R -q` 确认 `dist/assets` 包含 `自由移动 / 建图`、`低速自移动不依赖雷达新鲜度`、`建图另看相机和雷达`。
- 已通过：`curl -fsS http://127.0.0.1:7001/` 返回首页 HTML。

## 剩余风险

- 本轮只修 PC WYSIWYG 文案与测试，不触发真实自由移动、Nav2 或 `/cmd_vel`。
- 真实小车是否移动、Nav2 路线是否完成、摄像头是否恢复出画面仍需要现场安全确认后单独验证。
