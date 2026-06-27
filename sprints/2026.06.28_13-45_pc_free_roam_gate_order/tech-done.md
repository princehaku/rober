# 2026-06-28 13:45 PC free-roam gate order

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `sortFreeRoamGateRows()`，让 `free_roam_autonomy_gates` 先回答“能不能低速自由移动”，再回答“能不能按建图验收”。
  - gate 顺序固定为：`operator_confirmed`、`stop_available`、`motion_hil_unlock`、`camera_first_frame`、`lidar_fresh`、`mapping_active`、`fresh_map_preview`、`obstacle_clear`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将 runtime 只返回 stop/lidar gate 的场景收紧为精确顺序断言，避免 `mapping_active` 排到启动条件前面。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 gate 顺序按自由移动启动条件和建图验收条件分层，不把相机、雷达或地图记录误表达成低速移动前置。

## 验证结果

- `npm test -- test/catalog.test.ts -t "surfaces free-roam autonomy runtime state from latest artifact readback"`：通过，1 个用例通过、145 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮 gate 顺序。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  live gate 前三项为 `operator_confirmed`、`stop_available`、`motion_hil_unlock`；
  mapping 层随后为 `camera_first_frame`、`lidar_fresh`、`mapping_active`、`fresh_map_preview`、`obstacle_clear`。

## 剩余风险

- 本轮只调整 PC summary 的只读 gate 顺序，不发送 manual、keyboard、free-roam start、Nav2、delivery、stop 或 `/cmd_vel`。
- live 当前仍需要现场安全确认后才能启动自由移动；建图验收仍缺 camera first frame、fresh lidar、mapping active 和 fresh map preview。
