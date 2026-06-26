# Free Roam 雷达可降级启动

sprint_type: micro

## 实际改动

- 上位机 `free_roam_motion_readiness` 不再把雷达 latest scan proof 作为低速自移动硬门禁；相机 ready 时允许 start，雷达状态以 `optional=true`、`blocking=false`、`degraded_without_radar=true` 回传。
- 上位机固定 `ros2` argv 会自动 source `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash`，避免裸 `python3 upper_robot_api.py` 时找不到 ROS2 CLI。
- 上位机固定命令改为独立进程组执行；ROS2 CLI 超时时会杀掉整组进程并结构化返回，避免 HTTP API 被 orphan `ros2 param set` 卡死。
- PC free-roam start/stop 代理对 `/api/free-roam/autonomy/*` 使用 60s timeout；manual/stop 等其它固定 POST 仍保持 8s。
- PC 普通首屏自动扫图不再把 `雷达待刷新` 放入 start blocker，gate 文案改为 `雷达监看 / 雷达障碍监看 / 可降级`。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 和 `docs/product/pc_tools_workstation.md`，明确雷达待刷新不阻止低速自动扫图 start。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py && python3 -m unittest onboard.tests.test_upper_robot_api`，47 tests OK。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build OK；仅保留 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、223 tests OK。
- 已部署：上位机 API 重启为 PID `127018`；PC Node 通过 detached screen 绑定 `0.0.0.0:7001`，PID `57641`。
- 真机 smoke：summary 显示 camera `ready`、LiDAR `latest_scan_proof_fresh=false`、`free_roam_autonomy_start_ready=true`；POST PC `/api/robot-control/free-roam/autonomy/start` 返回 HTTP 200、`proxy_status=autonomy_forwarded`、`command_result.ok=true`、`motion_unlock_requested=true`，`sensor_readiness.ready=true` 且雷达 `optional=true/blocking=false/degraded_without_radar=true`。
- 真机 stop 收口：POST PC `/api/robot-control/free-roam/autonomy/stop` 返回 HTTP 200、`proxy_status=autonomy_forwarded`、`command_result.ok=true`；随后 latest 显示 `artifact_only=true`、`cmd_vel_publish_enabled=false`、`decision_state=stopping`。

## 剩余风险

- ROS2 `param set` 现场单条约 4s，start/stop 需要 30-40s 才返回；本轮已把 PC 代理 timeout 提升到 60s，但后续应考虑上位机内部批量参数写入或服务化接口来降低等待。
- 本轮证明的是固定 start/stop 参数链路和 free-roam runtime 双锁打开/关闭；没有用外部里程计或人工视频声明证明物理位移距离。
- 雷达被降级后，真实低速自移动更依赖现场 operator 监看、相机画面和停止兜底；真车 HIL 仍需记录低速移动、避障和停止响应时间。
