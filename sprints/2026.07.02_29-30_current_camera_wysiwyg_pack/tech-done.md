# 当前画面 WYSIWYG 包

## sprint_type

micro

## 实际改动

- 在 `RobotControlSummaryResponse` 增加 `current_camera_wysiwyg_pack_*` 顶层短字段，聚合当前画面是否可见、共享预览状态、首帧 probe、USB/硬件动作、建图/自由移动边界和只读复测端点。
- 在 `robotControlSummary.ts` 生成 `current_camera_wysiwyg_pack_status=visible|needs_first_frame` 和白话说明：
  - 画面可见时说明当前页面或共享预览已有首帧。
  - 画面不可见时说明共享预览缺口、下一步复测、阻塞建图首帧但不阻塞自由移动。
- 在 PC 普通首屏增加 `plain-current-camera-wysiwyg-pack` DOM，只读展示相机当前包，并暴露完整 no-motion data 属性。
- 更新 `docs/product/pc_tools_workstation.md`，明确摄像头 WYSIWYG 包和 RViz2/Foxglove/PC 页面之间的边界。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts`
  - 结果：通过，`2 passed`，`247 passed`。
- `npm run build`
  - 结果：通过。
  - 备注：Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告，不影响本轮相机包验证。
- `npm run lint`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无空白错误。
- 现场只读 live summary：
  - 7001 已重启并监听 `0.0.0.0:7001`。
  - `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `current_camera_wysiwyg_pack_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `current_camera_wysiwyg_pack_source_diagnosis_not_exclusive=true`
  - `current_camera_wysiwyg_pack_usb_speed=12M`
  - `current_camera_wysiwyg_pack_blocks_mapping_start=true`
  - `current_camera_wysiwyg_pack_blocks_free_move=false`
  - `current_camera_wysiwyg_pack_sends_motion_when_clicked=false`
  - `current_camera_wysiwyg_pack_starts_camera_exclusive_capture=false`

## 剩余风险

- 本轮只做 summary/DOM/software proof，没有触发真实摄像头独占采集、Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- 当前 live 现场摄像头首帧仍需上车硬件复测；该包让 PC 端能直接读出“阻塞建图、不阻塞自由移动”的事实，但不等于物理摄像头已恢复。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件：
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
