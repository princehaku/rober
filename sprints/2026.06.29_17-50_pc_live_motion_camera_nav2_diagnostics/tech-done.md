# Tech Done

sprint_type: micro

## 实际改动

- 修复 PC `GET /api/robot-control/summary` 的慢读预算：HTTP route 不再把所有 Robot API readback 压到全局 2.4s，保留 `robotControlSummary.ts` 里相机/底盘等端点自己的 4-8s 只读预算，避免直连上位机正常但 PC 汇总误报 `fetch_timeout_2400ms`。
- `free_roam` summary 新增 `external_stop_request` 运行诊断 gate：`external_stop_requested=true` 时明确显示这是停止请求，下一步是勾选现场安全确认后开始自由移动并清除停止请求；雷达 stale 仍只作为建图验收缺项，不阻塞低速自由移动入口。
- 上车 `free_roam_autonomy` 的 `mapping_active` gate 文案同步说明地图记录未启动不影响现场监看的低速自由移动。
- 文档同步更新 `docs/navigation/free_roam_autonomy.md` 与 `pc-tools/README.md`，记录摄像头共享预览非独占、自由移动不依赖雷达、Nav2 PWM 零轮速后按 ROS 重跑复验的现场口径。

## 验证结果

- `PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m unittest onboard.src.ros2_trashbot_nav.test.test_free_roam_autonomy`：通过，`Ran 10 tests OK`。
- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "slow base readback|free-roam stop request|rerun ROS Nav2|free-roam autonomy runtime"`：通过，4 个相关用例通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个 test files、372 个用例通过。
- `npm --prefix pc-tools/workstation run build`：通过，`tsc` app/server 与 Vite build 均完成；仅保留既有 chunk size warning。
- `python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`：通过。
- 7001 本机 Node 已重启到新代码，`lsof` 显示监听 `TCP *:7001`；`GET http://127.0.0.1:7001/api/robot-control/summary` 只读 live summary 返回 `robot_api_connection.status=readable`、15 个端点 loaded、0 failed。
- 真实只读观测：`/api/camera/health` 显示 `/dev/video1` `source_first_frame_failed`、`source_usage.status=not_in_use`、`source_diagnosis.status=uvc_no_frame_not_exclusive`，结论不是页面独占，而是 UVC/输入/供电无首帧。
- 真实只读观测：`/api/free-roam/autonomy/latest` 显示 `external_stop_requested=true`、`state=stopping`、`lidar_age_s` 已过期；这是停止请求状态，不是雷达阻止低速自由移动。
- 真实只读观测：`/api/nav2/status` 显示路线已生成且 `path_point_count=18`；`/api/nav2/goal/execution/latest` 显示上次 `base_command_mode=pwm`、非零命令数 49、T=1001 wheel L/R 仍 0/0、IMU 姿态变化已观察，下一次应按 ROS 重跑复验 wheel raw L/R。

## 剩余风险

- 本轮没有发真实运动命令，因为当前聊天轮次没有新的现场安全确认；未执行 `/api/nav2/goal/execute`、manual、keyboard、free-roam start、radar start 或 `/cmd_vel`。
- 摄像头仍未出真实首帧；当前软件只能明确不是浏览器/页面独占，仍需现场检查 USB、摄像头输入/供电或换 known-good UVC。
- Nav2 真实路线是否完成仍未闭环；上一轮只证明 action succeeded、底盘命令非零和 IMU 有变化，wheel raw L/R 未非零，delivery success 未完成。
