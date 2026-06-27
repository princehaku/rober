# 2026-06-28 13:25 PC free-roam mapping gate fallbacks

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当上车端 free-roam runtime 没有返回完整建图验收 gates 时，PC summary 补齐只读兜底 gate：
    `camera_first_frame`、`mapping_active`、`lidar_fresh`、`fresh_map_preview`。
  - `camera_first_frame` 兜底只使用只读 camera health/readiness/diagnosis，不打开新相机流；无首帧时明确给出检查 USB、输入、供电或 known-good UVC 的下一步。
  - `fresh_map_preview` 兜底固定为 `not_proven`，要求刷新地图画面后才能按建图验收，不把旧地图 artifact 外推为 fresh preview。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 runtime 只返回 stop/lidar gates 的场景，断言 PC summary 会补出 camera、mapping_active、fresh_map_preview gate。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 `free_roam_mapping_missing_reasons` 中的必需缺口必须能在 `free_roam_autonomy_gates` 中看到对应 evidence 和 next action。

## 验证结果

- `npm test -- test/catalog.test.ts -t "surfaces free-roam autonomy runtime state from latest artifact readback"`：通过，1 个用例通过、145 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning，不影响本轮 free-roam gate fallback。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  `free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`，且
  `free_roam_autonomy_gates` 已包含 `mapping_active/lidar_fresh/camera_first_frame/fresh_map_preview`。
  live 中 `camera_first_frame` 显示 `画面首帧未出，不是页面独占`，
  `fresh_map_preview` 显示 `地图画面未刷新`。

## 剩余风险

- 本轮只补 PC summary 的只读 gate 解释，不发送 manual、keyboard、free-roam start、Nav2、delivery、stop 或 `/cmd_vel`。
- live 当前仍是 camera 无首帧、雷达 stopped/stale、地图 fresh preview 未证明；这说明可以继续准备自由移动入口，但不能按“可建图验收”收口。
