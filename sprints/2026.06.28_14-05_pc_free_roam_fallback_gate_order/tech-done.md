# 2026-06-28 14:05 PC free-roam fallback gate order

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `defaultFreeRoamGateRows()`，让没有上车 free-roam runtime 时的 fallback gates 也复用 `sortFreeRoamGateRows()`。
  - fallback gate 顺序现在同样先显示 `operator_confirmed/stop_available/motion_hil_unlock`，再显示 `camera_first_frame/lidar_fresh`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 在无 runtime 的 locked boundary 场景中断言 fallback gate 顺序，避免初始/降级状态把相机或雷达排到运动发布状态前面。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 runtime missing、初始加载或连接降级时也保持“自由移动启动条件优先，建图验收缺口随后”的 gate 顺序。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`：通过，1 个用例通过、145 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮 fallback gate 顺序。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  live runtime 路径仍保持 gate 前三项为 `operator_confirmed`、`stop_available`、`motion_hil_unlock`。

## 剩余风险

- 本轮只调整没有 runtime 时的只读 fallback gate 顺序，不发送 manual、keyboard、free-roam start、Nav2、delivery、stop 或 `/cmd_vel`。
- live 当前有 runtime，因此 live 验证主要确认正常 runtime 路径未被破坏；fallback 路径由 focused test 覆盖。
