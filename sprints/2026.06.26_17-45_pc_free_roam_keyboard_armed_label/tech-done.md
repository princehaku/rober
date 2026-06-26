# PC 自由扫图键盘启用态按住才动标注

## sprint_type

micro

## 实际改动

- 普通首屏扫地式建图的键盘入口在已启用时显示 `键盘已启用（按住才动）`，避免用户误以为启用后小车会自动移动。
- 地图上的扫图流程 marker 同步显示 `键盘已启用（按住才动）`；aria 继续说明按住方向键才会移动，缺定位时 marker 不代表坐标。
- 更新 PC 工作站回归测试，锁定手动扫图路径中按钮和地图 marker 的新文案，并继续断言未按住时不发送 manual、Nav2、delivery 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改 WYSIWYG 文案，不改变键盘 armed、连续 pulse、release stop 或后端控制接口。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实键盘连续控制、真实底盘运动、真实自由跑动建图或 HIL。
