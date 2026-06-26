# PC 键盘零轮速诊断提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘轮速短状态新增“点动已发但仍未非零”分支。
  - 键盘轮速摘要新增“已发送点动并自动停止，但 L/R 仍未读到非零；运动帧=N；检查电机使能、供电、模式和现场空间后重试”提示，避免把 PC/上位机请求成功误说成底盘 wheel raw L/R 非零。
  - 修复 advanced wheel progress 摘要对 `operator_report_preflight` 的空值假设，避免普通 keyboard/manual 回包缺少该字段时产生异步渲染异常。
- `pc-tools/workstation/test/App.test.ts`
  - 新增键盘 pulse 零轮速回归：manual proxy 返回成功、自动 stop 已执行、T1001 运动帧存在，但 L/R=0/0 时，wheel raw 目标仍不通过，UI 给出底盘侧排查提示。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏键盘轮速证据边界：请求转发成功、自动 stop、底盘 L/R 非零是三层不同证据。

## 现场诊断依据

- 上位机 `root@192.168.1.11 -p 37878` 可连通。
- PC proxy `POST /api/robot-control/base/manual` 能转发到上位机，返回 `command_forwarded`。
- 上位机 `/api/base/manual` 真实写入 WAVE ROVER `{"T":1,"L":0.12,"R":0.12}`，随后写入 stop `{"T":1,"L":0,"R":0}`，未观察到串口写失败。
- `T=1001` 底盘反馈可读，电压和 IMU 有变化，但 during/after motion 中 `L/R` 均为 `0/0`。
- 直接尝试 vendor `T=11` PWM 与 `T=13` ROS ctrl 诊断，反馈 `T=1001` 仍为 `L/R=0/0`。

采用的硬件资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "keyboard"`
  - `Test Files 1 passed`
  - `Tests 13 passed | 112 skipped`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 224 passed`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仅保留 Vite chunk size warning。
- 通过：`curl -sS --max-time 5 http://127.0.0.1:7001/api/health`
  - 返回 `schema=trashbot.pc_tools_workstation.health.v1`
  - 返回 `mode=pc_only_readonly_workstation`
  - 返回 `safe_to_control=false`、`delivery_success=false`

## 剩余风险

- 本轮修复的是 PC 端可见诊断，不等于 wheel raw L/R 非零已完成。
- 真机手控仍未证明物理轮子转动。下一步需要现场确认电机使能、供电、电机模式、轮子是否悬空或受阻，以及固件当前 `mainType`/反馈口径。
- 自动驾驶不能动的直接软件链路已部分排除：PC proxy、上位机 manual endpoint、串口写入、T1001 读取都活着；剩余阻塞更像底盘实际执行或固件模式问题。
