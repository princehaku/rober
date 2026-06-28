# PC Radar Status Plain Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 05:02 CST
- status: done

## 实际改动

- 扩展 PC Node 只读 `GET /api/robot-control/radar/status` 响应合同，新增顶层 `plain_hint` 与 `next_action_plain`。
- `plain_hint` 对齐 `radar_status_plain`，`next_action_plain` 对齐 `radar_next_action_plain`，让现场脚本只看顶层字段时也能判断雷达是否 fresh、旧扫描是否不能当作地图 marker。
- 保留既有 `radar_overlay_wysiwyg_status_plain` 与 `radar_overlay_wysiwyg_next_action_plain`，继续强调地图 marker 所见即所得仍以 `GET /api/robot-control/map/preview` 的 overlay 计数为准。
- 补充 radar status 回归测试，锁定停止态雷达不会被误当成当前地图 marker，且顶层白话字段与专用字段一致。
- 同步 `docs/product/pc_tools_workstation.md`，说明该字段只消费只读 radar status，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar status"`：通过，1 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/radar/status`：通过，返回 `plain_hint=雷达未运行或扫描已停；旧雷达来源点不能当作当前地图 marker。`、`next_action_plain=先启动雷达并等待扫描 fresh，再刷新地图画面确认 marker。`，且与 `radar_status_plain/radar_next_action_plain` 一致；`robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强 radar status 的只读顶层可读性；真实地图 marker 仍需要雷达 lifecycle running、扫描 fresh，并通过 map preview 同轮 overlay 证明实际贴图点数。
