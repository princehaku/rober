# 当前控制包缺失证据中文标签

sprint_type: micro

## 实际改动

- 在 PC workstation summary 顶层补齐 `current_motion_verification_pack_missing_evidence_labels`，以及 trip、keyboard、free-move、mapping 四个 `current_*_control_pack_missing_evidence_labels`。
- 在普通 PC 控制台 DOM 对应补齐 `data-missing-evidence-labels`，让现场页面和脚本能同时读取内部 key 与中文标签。
- 更新 TypeScript contract、前端单测、catalog 路由测试和 PC 产品文档，明确这些字段只读展示，不触发 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 236 skipped。
- 通过：`npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`，1 passed / 182 skipped。
- 通过：`npm test -- test/catalog.test.ts`，183 passed。
- 通过：`npm run build`。Vite 仍提示已有 bundle size warning，但 TypeScript 和构建均通过。
- 通过：`git diff --check`。
- 通过：重启本地 workstation 到 `0.0.0.0:7001`，PID `52744` 监听 `*:7001`。
- 通过：只读 `curl http://127.0.0.1:7001/api/robot-control/summary` 显示：
  - `motion_pack_labels=["同窗口轮速 L/R 非零","送达确认","按住窗口轮速 L/R 非零","松开后停稳","自由移动启动读回"]`
  - `trip_labels=["同窗口轮速 L/R 非零","送达确认"]`
  - `keyboard_labels=["按住窗口轮速 L/R 非零","松开后停稳"]`
  - `free_labels=["自由移动启动读回"]`
  - `mapping_labels=["画面首帧"]`

## 剩余风险

- 本轮只补 PC/API 可读性，不执行真实运动；Nav2 路线执行、键盘连续手控和自由移动的真实轮速非零证据仍需要现场勾选安全确认后做 HIL 验收。
- 当前 WYSIWYG/建图仍受相机首帧缺口影响；现场 live mapping 标签只剩 `画面首帧`，该问题不由本轮标签改动解决。
