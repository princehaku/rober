# PC free-roam latest 启动口径补齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：在只读 `GET /api/robot-control/free-roam/autonomy/latest` 里补齐 `stop_request_pending`、`start_will_clear_stop_request`、`motion_start_blocked_by_stop_request=false`、`safety_confirmed`、`mapping_start_ready`、`mapping_start_missing_reasons` 和 `missing_capabilities`。停止请求现在明确解释为“开始自由移动会先清除，不是启动阻塞”。
- `pc-tools/workstation/src/shared/contracts.ts`：同步固定 latest response contract，避免前端或脚本再读到空字段。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充 running/stopping 两种 latest fixture 和断言，确保自由移动启动、停止请求、建图启动缺口三层口径稳定。
- `docs/product/pc_free_roam_mapping_design.md`：记录 latest 代理的新结构化字段和只读边界；该入口仍只执行 GET，不启动/停止 free-roam、不发送 manual/Nav2/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- 重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，PID `32451`。
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest`：
  - `proxy_status=latest_loaded`
  - `motion_start_ready=true`
  - `motion_ready=false`
  - `stop_request_pending=true`
  - `start_will_clear_stop_request=true`
  - `motion_start_blocked_by_stop_request=false`
  - `mapping_start_ready=false`
  - `mapping_start_missing_reasons=[camera_first_frame,lidar_fresh]`
  - `robot_control_executed=false`
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - camera 仍为 `source_first_frame_failed / uvc_no_frame_not_exclusive`，`source_usage_owner_count=0`，说明不是页面独占。
  - free-roam 仍为 `status=start_ready`、`motion_start_ready=true`、`motion_ready=false`。
  - map 路线和位姿可见：`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`；雷达 overlay 当前 `not_loaded`。

## 剩余风险

- 本轮只修 PC 只读契约和展示口径，没有发送真实运动命令；真车是否实际移动仍需要 CEO 在现场勾选安全确认后做 HIL。
- 摄像头当前不是独占问题，而是 UVC 无首帧；仍需现场检查 USB、摄像头输入或供电，或换 known-good UVC 复测。
- 雷达当前没有新鲜 overlay，建图启动缺 `camera_first_frame,lidar_fresh`，可先低速自由移动，但不能按可验收建图收口。
