# PC WYSIWYG Camera Probe Refresh Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-wysiwyg-evidence-refresh` 从只串联雷达扫描 proof，扩展为同时复测相机首帧和刷新 MJPEG 状态。
  - 新增 `refreshCameraFirstFrameProbeForWysiwyg()`，只刷新后端首帧证据、summary 和 MJPEG status，不覆盖相机“只读检查”按钮的本地结果卡，避免普通刷新把相机卡误显示为操作失败。
  - `plain-wysiwyg-evidence-refresh` 增加固定相机首帧 probe endpoint 和 `data-refreshes-camera-first-frame-probe=true` DOM 合同。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 `/api/robot-control/camera/first-frame/probe` fixture。
  - 锁定“刷新当前所见（含雷达贴图）”点击后会 POST 固定相机首帧 probe endpoint，同时继续禁止 radar start、Nav2 execute、manual、keyboard、free-roam、delivery、stop 等运动或生命周期动作。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明当前所见刷新现在同时覆盖雷达贴图和相机首帧复测，且仍为 no-motion 只读证据刷新。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过，222 个测试按筛选跳过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CZMk6oFx.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `740`，新监听进程为 `node` PID `15930`，地址 `TCP *:7001`。
- 7001 只读 bundle smoke：`http://127.0.0.1:7001/` 已引用 `index-CZMk6oFx.js` / `index-BBcFFzNr.css`；JS 资源命中 `plain-wysiwyg-evidence-refresh`、`data-refreshes-camera-first-frame-probe`、`camera/first-frame/probe` 和“刷新当前所见（含雷达贴图）”。
- 7001 live summary 只读 GET：`/api/robot-control/summary?base_url=http://192.168.1.11:8787` 返回 `schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`live_status=needs_wheel_rerun`，`primary_status_source_card_id=nav2_route`，`sends_motion_when_clicked=false`。

## 剩余风险

- 本轮没有触发真实相机首帧 probe 或任何运动 POST；live smoke 仅做首页、静态 bundle 与 summary GET。
- 真实相机仍需现场点击 no-motion “刷新当前所见（含雷达贴图）”或“只读检查画面”复测首帧；如果上位机 UVC 仍无首帧，页面会继续显示 camera blocked。
