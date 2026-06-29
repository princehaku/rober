# PC 相机 source diagnosis 下一步 fallback

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中修正 camera summary：
  - 当 source diagnosis 还没有硬件结论、`source_diagnosis_next_action_plain` 原本为空时，回退到共享 MJPEG/首帧检查下一步；
  - 已明确为 `uvc_no_frame_not_exclusive` 时仍保留更强的 USB/输入/供电/known-good UVC 复测提示。
- 在 `pc-tools/workstation/src/server/index.ts` 中同步修正 `/api/robot-control/camera/mjpeg/status`，让只读 status 端点也返回非空普通下一步。
- 更新 `pc-tools/workstation/test/catalog.test.ts` 与 `pc-tools/workstation/test/App.test.ts`，锁定默认 waiting 状态和已出帧状态下的 source diagnosis fallback 文案。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 已通过相机定向 server 验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera|Camera|MJPEG|mjpeg|shared preview|uvc|first-frame|first frame"`，结果 `26 passed | 136 skipped`。
- 已通过首屏/共享预览定向验证：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default|shared camera preview|waiting state until the browser draws a video frame|auto-join"`，结果 `4 passed | 211 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `2 files / 377 tests passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，监听 Node PID 为 `25196`。
- 已通过 7001 live 只读验证：
  - `GET /api/robot-control/summary` 返回 `source_diagnosis_next_action_plain="打开页面会自动接入共享 MJPEG；若仍无画面，点只读检查复测首帧。"`；
  - `GET /api/robot-control/camera/mjpeg/status` 返回同一条非空 next action；
  - 两个接口仍显示 `shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮只改只读文案和测试，不新建额外 camera capture、不重启相机、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- live 如果仍无首帧，后续仍需要按页面提示检查共享预览、首帧 probe 或 UVC 输入链路。
- live 验证只调用只读 `GET /api/robot-control/summary` 和 `GET /api/robot-control/camera/mjpeg/status`。
