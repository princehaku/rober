# PC Motion 顶层摘要别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：正常可读的 `GET /api/robot-control/summary` 顶层新增 `keyboard_summary` 和 `free_roam_summary`，分别复用 `readback_summary.keyboard/free_roam`。
- `pc-tools/workstation/src/shared/contracts.ts`：补充两个顶层别名的类型。
- `pc-tools/workstation/test/catalog.test.ts`：增加别名一致性断言，并锁住 `keyboard.start_ready=true`、`free_roam.motion_start_ready=true`、`free_roam.mapping_start_ready=false` 的当前产品口径。
- `pc-tools/README.md`：记录别名边界，明确只读、不替用户勾选安全确认、不启用键盘/自由移动。

## 验证结果

- `npm run build`：TypeScript、Vite build、server TypeScript 均通过。
- `npm test -- --run test/catalog.test.ts`：首次失败于断言过度绑定 live 文案；修正为检查稳定合同事实后复跑通过，`1 passed`，`166 passed`。
- 本机部署：已重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- Live summary：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `keyboard_summary_present=true`、`free_roam_summary_present=true`，且两者顶层状态均与 `readback_summary` 嵌套状态一致。当前真实状态为 `keyboard_status=start_ready`、`keyboard_start_ready=true`、`free_roam_status=start_ready`、`free_roam_motion_start_ready=true`、`free_roam_mapping_start_ready=false`。

## 剩余风险

- 该改动只改善 PC/API 可读性，帮助现场直接判断键盘连续手控和自由移动是否只差安全确认；不触发键盘 pulse、自由移动 start、Nav2、delivery、stop 或 `/cmd_vel`。
- 当前真实目标仍需要后续现场安全确认后的键盘/自由移动/完整 Nav2 运动验证。
