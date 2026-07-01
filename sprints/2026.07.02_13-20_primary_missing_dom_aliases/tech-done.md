# Primary Missing DOM Aliases

sprint_type: micro

## 实际改动

- 修正 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通首屏 `plain-field-acceptance-packet` DOM 合同，直接暴露当前主缺口动作的 `data-field-acceptance-primary-missing-action-*` 字段，包括动作名称、start/stop endpoint、验收读回端点、是否会让车动、是否需要安全确认，以及 camera/radar/operator/route 预检是否需要。
- 修正 `pc-tools/workstation/test/App.test.ts` 的 summary mock 形状，把主缺口动作字段放回 summary 顶层，确保测试覆盖真实组件读取路径。
- 补齐 `pc-tools/README.md` 里主缺口动作短 alias 清单，避免文档漏写 action label、stop endpoint 和 operator preflight 字段。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `67967`。
- 真实小车默认地址只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `status=needs_wheel_rerun`，`field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`，主缺口动作 start endpoint 为 `/api/robot-control/nav2/goal/execute`，`field_acceptance_primary_missing_action_minimal_precheck_safety_only=true`，camera/radar/operator/route preflight 均为 `false`，`radar_overlay_wysiwyg_complete=true`，当前 WYSIWYG 缺口只剩 `camera`。

## 剩余风险

- 本轮只做 GET-only 运行态 smoke 和前端 DOM 合同测试，未发任何 motion/control POST，也未执行 Nav2、键盘连续手控、自由移动或建图。
- 真实 motion 目标仍需在明确安全确认后完成：完整 Nav2 路线执行同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动运行读回。
- 相机首帧仍是 WYSIWYG 和建图启动的硬件缺口；雷达贴图当前已完成，不再是本轮 blocker。
