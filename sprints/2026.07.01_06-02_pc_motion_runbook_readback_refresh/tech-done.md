# PC 动作清单只读验收入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏动作清单每行新增“读回验收”按钮。按钮按动作类型只刷新固定验收端点：完整行程读最近行程、底盘轮速、summary 和送达 latest；键盘读底盘轮速和 summary；自由移动读 free-roam latest 和 summary；建图读地图预览和 summary。
- 同文件新增 `liveMotionRunbookReadbackPendingAction` 和 `refreshLiveMotionRunbookReadback`，用于避免重复点击，并保持读回动作与执行动作分离。
- `pc-tools/workstation/test/App.test.ts`：补充动作清单 DOM 合同和点击行为测试，确认“去启用键盘”仍只聚焦不发请求，“读回验收”只调用 base feedback samples 与 summary，不调用 manual、Nav2 execute、free-roam start、map start、delivery complete 或 stop。
- `docs/product/pc_tools_workstation.md`：同步动作清单只读验收入口合同。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 test。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts`：通过，1 file / 229 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- --run --fileParallelism=false`：通过，3 files / 413 tests。
- `git diff --check`：通过。
- 7001 只读 smoke：`GET /api/robot-control/summary` 返回 200，默认小车地址 `http://192.168.1.11:8787`，动作清单包含 `run_nav2_route,hold_keyboard,start_free_move,start_mapping_when_sensors_ready`，验收端点包含 latest、轮速、summary、delivery latest、free-roam latest 和 map preview，且 `live_motion_runbook_minimal_precheck_safety_only=true`。`GET /` 和 `GET /map` 均返回 200 HTML。

## 剩余风险

- 本轮没有执行真实 Nav2、键盘运动、自由移动、建图、送达或 stop；新增入口只减少现场验收读回步骤，不替代真实运动后的现场验收。
- 当前目标仍未完成：完整行程、键盘连续控制、自由移动运行和相机首帧仍需要真实现场安全确认与硬件读回。
