# 现场雷达启动与地图所见即所得 micro sprint

- sprint_type: micro
- owner: mainline-no-subagent
- scope: live radar start/refresh evidence, PC WYSIWYG evidence record

## 实际改动

- 通过当前 `http://0.0.0.0:7001` PC Node 固定代理对上车端执行雷达启动和只读刷新：
  - `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787`
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`
- 更新 `docs/product/pc_free_roam_mapping_design.md`，记录 live 证据和边界。
- 本轮没有改动产品代码；当前代码已经有普通首屏 `startPlainRadarLifecycle()` 成功后自动调用 `refreshRadarProof()` 的实现和测试覆盖。

## 验证结果

- SSH 只读连通：
  - `ssh -p 37878 root@192.168.1.11 'hostname; date; uname -a'`
  - 返回主机 `op-z3-b6.home`，Linux aarch64。
- 雷达 start 结果：
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `command_result.mode=command`
  - `command_result.executed=true`
  - `command_result.ok=true`
  - `robot_control_executed=false`
- 雷达 refresh 结果：
  - `proxy_status=refresh_forwarded`
  - `last_result_status=refreshed`
  - `last_result_evidence_ref=o1-lidar-scan-proof-1782505841325`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
  - `lifecycle_running=true`
- PC summary 复核：
  - `readback_summary.lidar.continuous_scan_status=latest_proof_fresh_while_lifecycle_running`
  - `readback_summary.lidar.lifecycle_running=true`
  - `readback_summary.lidar.lifecycle_state=running`
  - `readback_summary.lidar.continuous_window_observed=true`
  - `readback_summary.lidar.latest_scan_proof_fresh=true`
  - `readback_summary.lidar.scan_preview_point_count=72`
  - `o3_proof_summary.robot_pose.frame_id=map`
- 代码验证：
  - 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "plain radar start|radar start fail|map radar-starting|refreshes radar"`
    - `Test Files 1 passed | 1 skipped (2)`
    - `Tests 5 passed | 255 skipped (260)`
  - 通过：`cd pc-tools/workstation && npm run lint`
  - 通过：`cd pc-tools/workstation && npm run build`
    - Vite 仍提示单个 chunk 超过 500 kB；这是既有打包体积警告，本轮未扩大处理范围。
  - 通过：`git diff --check`

## 剩余风险

- 相机仍是 `source_first_frame_failed/capture_read_returned_false`，本轮没有证明画面首帧。
- Nav2 仍是 action succeeded 但同窗口 `T1001 L/R` 非零未证明；完整路线 HIL 尚未完成。
- 雷达已保持 running；如现场需要静音或收车，应通过 `POST /api/robot-control/radar/stop` 或 PC 高级停止按钮关闭。
