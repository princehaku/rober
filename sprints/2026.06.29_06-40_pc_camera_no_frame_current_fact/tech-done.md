# PC camera no-frame current fact

## sprint_type

micro

## 实际改动

- 普通首屏“当前事实”的画面行在 `uvc_no_frame_not_exclusive`、后端多方式取帧失败或 `source_usage_owner_count=0` 时，不再只说“没有输出视频帧”，而是同步显示“检查 USB、摄像头输入、格式或供电，必要时换 known-good UVC 复测”。
- 保留原有共享预览口径：多人页面共用同一条上游流，不把相机源头无帧误判成浏览器独占。
- 补充 App 测试，覆盖 live 形态里只读到 `source_diagnosis_plain_hint`、usage/selected device 暂时 not_loaded 的首屏文案。
- 更新 `docs/product/pc_tools_workstation.md`，记录该变化只更新诊断文案，不触发任何运动或相机重启动作。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --runInBand` 未执行成功：当前 Vitest 不支持 `--runInBand`，返回 `Unknown option --runInBand`。随后改用项目现有命令重跑。
- `npm --prefix pc-tools/workstation test` 通过：2 个 test files、365 个 tests 全部通过。
- `npm --prefix pc-tools/workstation run build` 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。
- 7001 live 只读复核：`lsof` 显示 `node` PID `49853` 监听 `*:7001`；`GET /api/robot-control/summary` 返回 `camera.status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_plain_hint=不是页面独占...检查 USB...known-good UVC`、`keyboard_control_start_ready=true`、`free_roam_motion_start_ready=true`、`nav2_goal_ready=true`，未调用任何运动接口。
- Chrome/Playwright DOM 只读复核 `http://127.0.0.1:7001/`：首屏当前事实包含“本页共享预览暂时没有出画面；不是页面独占：没人占用，但 UVC 没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。”、“自由移动不受影响/低速自移动不依赖雷达新鲜度”、“自动驾驶服务当前未启动；点击执行图上路线会自动启动 runtime 并重跑，本轮成败以返回结果和 wheel raw L/R 非零为准”。

## 剩余风险

- 该轮只修 PC 首屏诊断显示；真实摄像头仍需要现场检查 USB、摄像头输入/供电或更换 known-good UVC。
- 不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`；无法在未获现场安全确认时验证小车实际移动或 Nav2 真车复跑。
