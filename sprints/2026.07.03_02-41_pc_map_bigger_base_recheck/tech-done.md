# PC 大地图放大与底盘手控链路复验

## sprint_type

micro

## 实际改动

- 修改 `pc-tools/workstation/src/styles.css`：普通 PC 驾驶台主地图列从 `1.65fr/0.9fr` 调整为 `2.35fr/0.75fr`，右列最小宽度收紧到 `330px`，图传/WASD 仍留在首屏右侧。
- 修改 `pc-tools/workstation/src/styles.css`：首页大地图画布改为 `clamp(600px, calc(100vh - 104px), 900px)`，并把“当前画布”图层条改成地图内横向浮层；直达 `/map` 地图画布改为 `calc(100vh - 44px)`，减少“地图太小”的默认感受。
- 更新 `docs/product/pc_tools_workstation.md`：同步 ROS2 配套工具口径（普通用户用 PC `/map`，工程观察用 RViz2/Foxglove）和本轮底盘命令/反馈复验证据。

## 验证结果

- 本机服务健康：`curl http://127.0.0.1:7001/api/health` 回读 `workstation_listen_address=http://0.0.0.0:7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- PC 工程验证：`npm run lint` 通过；`npm test` 通过，`3 passed / 432 passed`；`npm run build` 通过，产出 `dist/assets/index-B7px8esf.css` 与 `dist/assets/index-DDGPvHUH.js`。
- Chrome headless DOM smoke（1280x720 首页）：地图面板 `878x648`，地图画布 `848x616`，图层条为浮层 `840x38`；右侧相机卡 `330x331`，USB 诊断首屏可见；WASD 方向键在 motion 面板内 `top=523,bottom=641`。
- Chrome headless DOM smoke（1280x720 `/map`）：`data-direct-map-view-requested=true`，地图画布 `1272x676`，非地图卡片可见数 `0`。
- 上位机进程复核：`upper_robot_api.py` 运行在 `0.0.0.0:8787`，`esp32_bridge` 持有 `/dev/ttyS5`，参数为 `command_mode=pwm`、`pwm_min_abs=164`、`pwm_max_abs=164`。
- PC 手控复验：`POST /api/robot-control/base/manual`，body 为 `direction=forward,speed=0.08,duration_ms=240`，返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`manual_command_executed=true`、`auto_stop_executed=true`。
- PC 停车复验：`POST /api/robot-control/base/stop` 返回 `proxy_status=command_forwarded`、`status=stopped`、`remote_http_status=200`。
- PC first-jog 复验：`speed=0.08,duration_ms=500` 和 `speed=0.12,duration_ms=800` 均返回 `command_forwarded`，但 `wheel_feedback_latest_raw_left/right=0/0`。
- 上位机 command debug：`wave_rover_command_debug.jsonl` 出现同窗口 `T=11,L=164,R=164`，随后出现 `T=11,L=0,R=0` stop。
- 上位机 feedback debug：`wave_rover_feedback_debug.jsonl` 持续出现 `T=1001,L=0,R=0`，IMU 姿态变化未达到项目 1 度运动阈值。

## 剩余风险

- 地图视觉放大已通过 Chrome headless DOM smoke；仍建议现场用真实显示器主观确认地图缩放是否足够。
- 当前能证明 PC 到 WAVE ROVER `T=11/PWM164` 的软件命令链路和 stop 链路，但不能证明 wheel raw 非零、真实物理移动、Nav2 自动驾驶完成或 delivery success。
- 相机仍卡在 USB `12M` full-speed / V4L2 `STREAMON` I/O error，需要物理换高速 USB 口/线或带供电 Hub 后复测。
- 若要提高 PWM 或延长运动窗口，必须人工在车旁确认电机供电、急停、底盘模式、轮子是否离地和安全空间。
