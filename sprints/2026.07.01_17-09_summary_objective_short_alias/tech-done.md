# Summary Objective Short Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增四项目标短 alias：`motion_ready`、`motion_complete`、`wysiwyg_ready`、`wysiwyg_complete`、`precheck_ready`、`precheck_complete`、`mapping_ready` 和 `mapping_complete`。
- `motion_ready` 表示至少有运动 runbook 可处理；`motion_complete` 跟随 motion objective 完成。
- `wysiwyg_ready` / `wysiwyg_complete` 跟随画面、地图、雷达点全部所见即所得。
- `precheck_ready` / `precheck_complete` 跟随最小预检是否已经收敛为只需现场安全确认。
- `mapping_ready` 只表示建图启动 ready；`mapping_complete` 跟随自由移动到建图 objective 完成，避免把“可先自由移动”误报成“已可建图”。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认四项目标短 alias 不再为 `null`：`motion_ready=true`、`motion_complete=false`、`wysiwyg_ready=false`、`wysiwyg_complete=false`、`precheck_ready=true`、`precheck_complete=true`、`mapping_ready=false`、`mapping_complete=false`。

## 剩余风险

- 本轮只增加只读 alias，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 当前真实状态仍是 `motion_complete=false`、`wysiwyg_complete=false`、`mapping_ready=false`、`mapping_complete=false`；完整目标仍需现场安全确认后的运动实测、相机首帧、雷达贴图和建图条件读回。
