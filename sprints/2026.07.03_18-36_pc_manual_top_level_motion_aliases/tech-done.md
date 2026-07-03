# PC 手控回包顶层运动证据

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `baseManualMotionTopLevelAliases()`，把 manual/first-jog 的本次点动窗口关键值从 `remote_motion_key_values` 提升到响应顶层。
  - 覆盖字段包括 `base_command_mode`、`feedback_mode`、`command_result_ok`、`stop_result_ok`、`wheel_feedback_lr_nonzero_proven`、`wheel_feedback_latest_raw_left/right`、`imu_attitude_delta_observed`、`motion_signal_observed`、`motion_signal_source` 和 T1001 帧数。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `RobotControlBaseCommandProxyResponse` 补齐这些可选顶层 alias。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 realtime manual 与 first-jog 两条代理，要求嵌套材料和顶层 alias 同步。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步说明 PC 手控回包现在能直接读本次命令、stop、IMU 运动信号和 wheel raw 缺口。

硬件协议复核来源：`docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料，`T=11` 为 direct PWM input；本轮只提升 PC 回包字段，不改变底盘控制协议。

## 验证结果

- 通过：`npm test -- robotControlSummary.test.ts`，13 tests passed。
- 通过：`npm test -- catalog.test.ts`，188 tests passed。
- 通过：`npm run build`，TypeScript、Vite build、server TypeScript 均通过；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：本地 7001 已重启并监听 `0.0.0.0:7001`。
- 通过：真实 PC 7001 后退点动 `direction=back,speed=0.06,duration_ms=360` 返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`、`wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left/right=0/0`。
- 通过：上位机 `wave_rover_command_debug.jsonl` 同窗口新增 `/cmd_vel -> esp32_bridge -> HTTP -> WAVE ROVER` vendor `T=11,L=-255,R=-255`，随后 stop `T=11,L=0,R=0`。

## 剩余风险

- 顶层 alias 只是让 PC/脚本更直接读取本次手控事实；它不把 IMU 姿态变化升级成 WAVE ROVER `T=1001` wheel raw L/R 非零。
- `T=1001` wheel raw L/R 仍未证明非零，完整 Nav2 路线执行和 delivery success 仍未完成。
- 实时图传仍未可见，仍需摄像头输入、线/口/供电或 known-good UVC 复测。
