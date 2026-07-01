# 2026.07.01 09:12 PC 当前卡点送达闭环读回

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏当前卡点区新增 `plain-live-delivery-closure-readback`，镜像送达区 `plain-delivery-closure-summary`。
- 新增 `plain-live-delivery-closure-readback-refresh`，只读回 `/api/robot-control/delivery/latest`。
- 当前卡点现在同时显示完整行程到点/轮速/送达三段闭环，不用滚到送达区才能看到 delivery success 缺口。
- DOM 明确声明该按钮不提交 delivery complete、不执行 Nav2、不发送手控/键盘/自由移动、不启动建图、不 stop、不发送 motion。
- 更新 PC 工作站产品边界文档，记录当前卡点送达闭环读回合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|renders Robot Control V1 by default"`，1 file passed，4 tests passed，227 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning；当前产物为 `dist/assets/index-BWkTdggq.js` 与 `dist/assets/index-7krFlZYN.css`。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`GET http://127.0.0.1:7001/map` 返回 `200 OK`。
- 通过：构建产物包含 `plain-live-delivery-closure-readback`、`送达闭环` 和 `读回送达`。
- 通过：只读 `GET /api/robot-control/delivery/latest?robot_api_base_url=http://192.168.1.11:8787` 返回 `proxy_status=latest_loaded`、`delivery_success=false`、`robot_control_executed=false`，缺口仍是现场送达确认材料。

## 剩余风险

- 当前改动是 PC 只读 UI/DOM 合同；delivery success 仍需要现场材料和最终确认完成后才能提交。
- 完整 Nav2 闭环仍缺同窗口 wheel L/R 非零和 delivery success；相机仍需现场修复 USB full-speed 链路后复测。
