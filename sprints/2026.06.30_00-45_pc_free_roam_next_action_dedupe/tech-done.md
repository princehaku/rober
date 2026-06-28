# PC Free Roam Next Action Deduplication

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：收敛 `freeRoamAutonomyNextAction` 的 `start_ready + external_stop` 分支，把“解除停止请求”和“可先自由移动”合成一句，避免普通首屏连续出现两次“勾选现场安全确认”。
- `pc-tools/workstation/test/catalog.test.ts`：补停止请求场景断言，确保 `free_roam_autonomy_next_action` 中“勾选现场安全确认”只出现一次。
- `docs/product/pc_tools_workstation.md`：同步记录自由移动只读下一步文案去重规则。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam"`，12 个相关测试通过，148 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，live 返回 `safe_command_boundary.free_roam_autonomy_next_action=当前处于停止请求；勾选现场安全确认后可先自由移动，开始时会先解除停止请求；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面`，同值同步到 `readback_summary.free_roam.next_action_plain`，只出现一次“勾选现场安全确认”。

## 剩余风险

- 本轮只修 PC summary/safe boundary 只读文案，不启动自由移动、不发送 stop、不发送 `/cmd_vel`；真实自由移动仍需要现场人员勾选安全确认后操作。
