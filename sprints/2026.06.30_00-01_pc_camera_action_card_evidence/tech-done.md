# 2026.06.30 00:01 PC 画面动作卡证据

sprint_type: micro

## 设计先行

本轮只补 PC 首屏“画面”动作卡的结构化只读证据，不打开相机、不新建采集。目标是让脚本和 DOM smoke 直接证明：实时画面是否真的有当前帧、多个页面是否共用同一条上游流、是否有独占摄像头声明、当前卡点是否为 UVC 无首帧。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlActionStatusCard.evidence`，增加画面 WYSIWYG 和共享预览证据字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `camera_preview` 动作卡输出当前帧可见、共享多页面、shared capture、非独占、首帧失败、source diagnosis、首帧探针、观看人数和缓存帧证据。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通动作卡兼容旧 summary，从 `readback_summary.camera` 补画面只读证据，并暴露对应 DOM `data-*` 属性。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖默认 summary 和 `source_first_frame_failed / uvc_no_frame_not_exclusive` 场景中的 `camera_preview.evidence`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 上能读到共享预览、非独占、当前无可见帧等证据。
- `pc-tools/README.md`
  - 同步记录只读字段合同和不发送控制命令边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 167 skipped (168)`。
- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary reflects camera source first-frame failure in shared preview status"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 167 skipped (168)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 217 skipped (218)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；仅保留 Vite chunk size 提示。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 386 passed (386)`。
- 通过：`git diff --check`。
- 通过：重启本机 PC Node 到 `0.0.0.0:7001`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
  - `/tmp/rober_pc_workstation_7001.log` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary`。
  - `camera_preview.evidence.camera_current_frame_visible=false`。
  - `shared_preview_multi_viewer=true`、`shared_capture=true`、`exclusive_camera_claim=false`。
  - `source_first_frame_failed=true`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`。
  - `first_frame_probe_read_ok=false`、`visible_content_proven=false`、`shared_preview_client_count=0`。
  - live 结论：当前画面缺口不是页面独占，而是 USB/UVC 摄像头没有输出首帧；PC 多页面会共用一条上游共享预览。

## 剩余风险

- 本轮只补只读合同和 DOM 验证，不打开相机、不新建独占采集、不发送 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实相机首帧仍需要继续排查 USB、摄像头输入/供电或 known-good UVC；这不阻止低速自由移动，但会阻止建图启动/建图验收进入完整闭环。
