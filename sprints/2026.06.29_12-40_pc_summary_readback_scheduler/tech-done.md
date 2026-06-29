# PC Summary Readback Scheduler

## sprint_type

micro

## 实际改动

- 调整 `pc-tools/workstation/src/server/robotControlSummary.ts` 的 summary readback 调度：先并发读取地图、定位、Nav2、相机、雷达、free-roam、底盘 feedback latest 等快端点，再串行读取 `/api/base/status` 和 `/api/status`。
- 将浏览器侧 `/api/robot-control/summary` 等待窗口从 3.5s 提升到 12s，避免 Node summary 已经在等待真实慢读数时，页面先报错。
- 新增串行上位机 fixture 测试，覆盖真实 HTTP 服务接近单 worker 时，慢 `/api/status` 不再拖垮 Nav2/地图/相机等快端点。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，记录只读调度变化与安全边界。

## 验证结果

- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "fast endpoints before serial slow aggregate endpoints"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- App.test.ts -t "browser-side summary request times out"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "slow base readback budget"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "slow status and camera endpoints"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- Pass: `npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 通过；Vite 仍提示既有 chunk size warning。
- Pass: PC API 已重启到 `0.0.0.0:7001`，监听 PID 57289。
- Pass: 只读 curl `http://127.0.0.1:7001/api/robot-control/summary` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`、`base_status=loaded`，不再出现全端点 `fetch_timeout_*`。
- Pass: 只读 7071 诊断仍返回 `robot_api_port_7071_mismatch_use_8787` 作为首位 blocker，并保持 `safe_to_control=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮没有调用 manual、Nav2 执行、keyboard、free-roam、delivery、stop 或 `/cmd_vel`，只做只读 GET 验证。
- 现场只读事实显示：相机不是页面独占，`USB Composite Device: DV20 USB` 当前没人占用，但 UVC 没有输出视频帧；需要检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
- 现场只读事实显示：自由移动和键盘入口在安全确认后可处理，低速移动不依赖雷达；雷达当前 `radar_stopped`，只影响雷达贴图/建图验收。
- 现场只读事实显示：Nav2 图上路线 ready，下一次执行会用 ROS 模式重跑；上次 route result succeeded 但执行窗口 wheel L/R=0/0，不能宣称实车已移动。真实重跑属于危险动作，需要现场安全确认后再执行。
