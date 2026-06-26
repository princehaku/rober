sprint_type: micro

# PC 实时画面只读检查按钮

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 在普通首屏“实时画面”卡片新增“检查画面（只读）”按钮，复用固定 `POST /api/robot-control/camera/first-frame/probe` 探针。
- 新增首屏 `只读检查` 摘要：样张读到时显示“上位机样张已读到，实时窗口仍未打开”，失败时复用普通相机失败文案。
- `pc-tools/workstation/test/App.test.ts` 增加回归：只读检查只调用 camera first-frame probe，不调用 camera offer、operator report、manual、Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md` 同步记录“检查画面（只读）”的边界与 WYSIWYG 语义。

## 验证结果

- `npm test -- test/App.test.ts -t "checks the plain camera frame"`：通过，1 passed / 121 skipped。
- `npm test -- test/App.test.ts`：通过，122 passed。
- `npm test`：通过，2 files / 219 passed。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启在 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `TCP *:7001 (LISTEN)`。
- live summary 验证：默认小车 camera readback 为 `camera_status=ready`、`devices_status=loaded`、`source_readiness=source_selected_not_probed`、`last_offer_error=camera_open_failed`、`last_offer_failure_reason=opencv_capture_not_opened`，顶层仍为 `safe_to_control=false`、`delivery_success=false`。
- live camera probe 验证：`POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `proxy_status=probe_failed`、`status=open_failed`、`remote_http_status=503`、`open_ok=false`、`read_ok=false`、`visible_content_proven=false`、`failure_reason=probe_http_status_503`，顶层仍为 `safe_to_control=false`、`robot_control_executed=false`。这会在首屏只读检查中落为失败提示，不会误报实时画面可见。

## 剩余风险

- 该按钮只能证明上位机 camera probe 能否读到首帧样张；不证明 WebRTC 实时画面已显示，不证明轮速、LiDAR delta、Nav2 实跑或 delivery success。
