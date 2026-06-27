# 2026.06.28 03:56 free-roam latest 建图验收缺口只读补齐

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/free-roam/autonomy/latest` 的 `latest_key_values` 保留原有 `gate_count`，并新增 `runtime_gate_count`、`mapping_gate_count`、`mapping_required_ids`、`mapping_missing`、`mapping_ready`。
  - 建图验收固定按 `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview` 四项归一化；上车 runtime 缺少某个 gate 时按未证明处理。
  - 该接口仍是只读 GET，不启动 free-roam、不打开相机、不启动雷达、不发送 manual/Nav2/stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展 free-roam autonomy latest 只读代理回归测试，锁定“只读、不发 start/stop/manual”以及建图验收缺口补齐。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步说明 latest 代理现在直接暴露建图验收缺口，继续区分“自由移动可启动”和“建图可验收”。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "free-roam autonomy latest proxy reads fixed runtime artifact without starting autonomy"`，1 passed / 334 skipped。
- 通过：`cd pc-tools/workstation && npm test`，335 passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示生产包 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮 server 合同构建通过。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，只读 live GET
  `/api/robot-control/free-roam/autonomy/latest?baseUrl=http://192.168.1.11:8787` 返回
  `proxy_status=latest_loaded`、`remote_http_status=200`、`runtime_gate_count=5`、
  `mapping_required_ids=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `mapping_ready=false`、`safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只改 PC 只读状态解释，不触发真实发车；不证明 wheel raw L/R 非零、Nav2 完整路线执行或 delivery success。
- live 上车端当前摄像头仍可能是 `source_first_frame_failed`，雷达/地图预览是否 fresh 仍以真实 runtime 与 summary readback 为准。
