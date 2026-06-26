# PC Free Roam Param Load WYSIWYG

## sprint_type

micro

## 实际改动

- 修改 `pc-tools/workstation/src/shared/contracts.ts`：扩展 free-roam autonomy 代理合同，保留 `write_strategy`、参数名列表、参数数量、stdout 短摘要和 `mapping_active_applied`。
- 修改 `pc-tools/workstation/src/server/index.ts`：PC Node 从上位机 `command_result.results[0]` 摘取 `ros2_param_load` 写入证据，不再只压缩为 `mode/executed/ok`。
- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏自动扫图卡新增“状态机写入”摘要，显示启动/停止参数是否一次写入、是否请求运动双锁、是否只按自由移动记录、以及 `cmd_vel_topic` 未被改写。
- 修改 `pc-tools/workstation/test/App.test.ts`：更新 start/stop fixture 为真实 `ros2_param_load` 形状，并断言普通首屏显示启动 6 项、停止 5 项状态机写入证据。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：记录 PC 端不再丢失 free-roam 状态机写入证据。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|自动扫图"`：通过，`1 passed`，`19 passed / 122 skipped`。
- `cd pc-tools/workstation && npm run build`：通过，TypeScript 与 Vite build OK；保留既有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只让 PC 所见即所得展示状态机参数写入证据；不远程发 start 打开运动双锁。
- 真实自由移动 start 仍需现场人员在小车旁边确认安全后 HIL。
