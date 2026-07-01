# Delivery Latest Top Alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/delivery/latest` 新增送达闭环顶层短 alias，包含缺口数组、缺口数量、白话缺口、operator evidence ref、Nav2 状态、反馈样本数，以及只读/不发车边界。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 `RobotControlDeliveryLatestResponse` 合同字段。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖上位机把 `missing_required_material` 作为 JSON 字符串返回时，PC Node 仍能还原为顶层数组。
- `docs/product/pc_tools_workstation.md`：记录 `/api/robot-control/delivery/latest` 顶层 alias 与 no-motion 边界。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "delivery latest proxy reads fixed gate gap without submitting completion"`，1 passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "defaults Robot Control read-only reads"`，1 passed。
- 通过：`npm test`，3 files / 420 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，新 PID `50681`。
- 通过：只读 curl `/api/robot-control/delivery/latest?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=latest_loaded`、`delivery_success=false`、`delivery_missing_required_material_count=5`、`delivery_nav2_status=goal_succeeded`、`delivery_nav2_result_status=succeeded`、`delivery_latest_readback_only=true`、`delivery_complete_sends_motion=false`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。

## 剩余风险

- 本轮只补 delivery latest 只读合同，不触发 Nav2、manual、keyboard、free-roam、建图、delivery complete、stop 或 `/cmd_vel`。
- 完整目标仍未收口：真实车同窗口 wheel L/R 非零、delivery success、键盘按住连续轮速、自由移动运行态、相机首帧和建图启动仍需现场安全确认后的实测材料。
