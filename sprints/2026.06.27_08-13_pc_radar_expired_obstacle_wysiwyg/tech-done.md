# PC 雷达过期障碍距离 WYSIWYG 修复

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当上车端 free-roam gate 显示 `lidar_fresh` 已过期、未运行或 lifecycle stopped，同时 `obstacle_clear.evidence` 仍带旧的 `最近障碍 Xm` 时，PC summary 不再把该距离继续透传给地图降级 marker。
  - 改写为 `雷达未刷新，障碍距离不可用`，并提示先刷新雷达；自由移动入口仍按 `stop_available` 兜底保持可启动口径，不把雷达新鲜度重新变成低速自由移动 blocker。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加过期雷达 + 旧障碍距离的回归测试，覆盖旧距离被隐藏、`free_roam_autonomy_start_ready=true`、PC 仍不执行控制命令。
- `docs/product/pc_tools_workstation.md`
  - 同步记录过期雷达障碍距离的展示规则和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "hides stale obstacle distance"`，1 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍输出既有 chunk size warning，不影响本轮构建通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files / 275 个测试通过。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`，`GET /api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`。
- 通过：live `GET /api/robot-control/summary` 读取上位机 `http://192.168.1.11:8787` 成功，`free_roam_autonomy_start_ready=true`；`lidar_fresh.evidence=雷达距离已过期，按无雷达低速自由移动` 时，`obstacle_clear.evidence=雷达未刷新，障碍距离不可用`、`next_action=先刷新雷达；刷新前不把旧障碍距离贴到地图`。
- 现场只读观察：camera 仍为 `source_first_frame_failed` / `capture_read_returned_false`，`source_usage_owner_count=0`、`shared_preview_exclusive_camera_claim=false`，说明本轮读到的问题不是 PC 预览独占占用。

## 剩余风险

- 本轮不启动雷达、不执行 Nav2、不发 manual/keyboard/free-roam motion，不证明真实 wheel raw L/R 非零、完整路线执行或 delivery success。
- 当前 camera 首帧失败、LiDAR 无新点/过期、真实自动驾驶不能动的问题仍需要继续上车侧定位；本轮只消除 PC 地图对旧雷达障碍距离的误导。
