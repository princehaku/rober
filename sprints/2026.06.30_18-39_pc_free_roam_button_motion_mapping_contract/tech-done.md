# PC Free Roam Button Motion Mapping Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-free-roam-start` 自由移动主按钮新增按钮级移动/建图分层合同：
    `data-safety-confirmation-required=true`、
    `data-camera-preflight-required-for-motion=false`、
    `data-radar-preflight-required-for-motion=false`、
    `data-mapping-start-before-free-move-required`。
  - 同一按钮新增启动后只读复验合同：
    `data-post-start-radar-refresh-required=true`、
    `data-post-start-map-preview-refresh-required=true`、
    `data-post-start-radar-status-refresh-required=true`、
    `data-post-start-latest-refresh-required=true`。
  - 同一按钮补齐固定 endpoint：
    free-roam start/stop/latest、mapping start/preview、radar refresh/status。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖未勾安全确认、自由移动-only、相机/雷达 ready 后先建图再自由移动三种按钮语义。
  - 确认相机/雷达不作为自由移动发车前预检，只影响是否先启动建图记录。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步自由移动主按钮合同和目标 4 的分层口径。

## 验证结果

- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Cr_966lR.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：旧监听 `node` PID `84751` 已停止，新监听为 `node` PID `97753`，地址 `TCP *:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `assets/index-Cr_966lR.js` 和 `assets/index-BCQK7HRw.css`；JS bundle 命中 `data-camera-preflight-required-for-motion`、`data-radar-preflight-required-for-motion`、`data-mapping-start-before-free-move-required`、`data-post-start-latest-refresh-required`、`data-fixed-free-roam-latest-endpoint`、`data-fixed-free-roam-stop-endpoint`、`data-fixed-radar-status-endpoint`。
- live summary 只读检查：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`free_move_ready=true`、`free_roam_status=start_ready`、`mapping_ready=false`、`mapping_start_missing=camera_first_frame,lidar_fresh`。

## 剩余风险

- 本轮只补 PC 按钮级合同和测试，不在 live 环境点击真实自由移动 start，不发送 free-roam、Nav2、manual、keyboard、stop 或 `/cmd_vel`。
- 真实自由移动和建图仍需要现场安全确认后执行，并用 free-roam latest、雷达 proof、地图预览和相机首帧读数验收。
