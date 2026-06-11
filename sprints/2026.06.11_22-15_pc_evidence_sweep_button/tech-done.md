# PC Evidence Sweep Button

## sprint_type

micro

## 背景

继续推进真实上车 evidence capture：雷达、摄像头、建图、定位移动、手动移动、实时图传都要能从
PC 页面进入闭环。上一轮已经把相机首帧探针接入 PC 高级诊断；本轮继续不调用 subagent，
在 PC 高级诊断新增“一键证据巡检（高级）”，把当前安全可执行的固定代理串起来。

本轮不放行非 stop 运动，不调用 `/api/base/manual` 成功路径，不发布 `/cmd_vel`，不执行
NavigateToPose。

## 设计

一键巡检只复用已有固定代理，顺序为：

1. `GET /api/robot-control/summary`
2. `POST /api/robot-control/camera/first-frame/probe`
3. `POST /api/robot-control/radar/scan-proof/refresh`
4. `POST /api/robot-control/map/proof/refresh`
5. `POST /api/robot-control/nav2/proof/refresh`
6. `POST /api/robot-control/base/stop`

该按钮只放在默认关闭的 `高级诊断 / 任务与证据` 中，普通 `.simple-user-console` 首屏不新增
工程文案。巡检结果只展示短摘要；各子系统完整 payload 仍保留在对应高级卡片和 artifacts。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `evidenceSweepPending`、开始/完成时间和短结果行；
  - 新增 `runEvidenceSweep()`，串行调用 summary、camera probe、radar、map、Nav2 no-motion、stop；
  - 新增 “一键证据巡检（高级）” 按钮；
  - 普通用户首屏未改。
- 新增真实 PC proxy smoke artifacts：
  - `artifacts/01_summary.json`
  - `artifacts/02_camera_probe.json`
  - `artifacts/03_radar_refresh.json`
  - `artifacts/04_map_refresh.json`
  - `artifacts/05_nav2_refresh.json`
  - `artifacts/06_stop.json`
  - `artifacts/07_summary_after_sweep.json`
  - `artifacts/08_sweep_summary.json`
  - `artifacts/09_cleanup.txt`

## 验证结果

本地验证：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
git diff --check
```

结果：

- PC workstation：92 tests passed
- PC workstation build：通过
- `git diff --check`：通过

真实 PC proxy smoke 使用临时 `PORT=18808 npm run api`，连接真实上位机
`http://192.168.1.11:8787`，按一键巡检同序调用固定代理。

结果摘要：

| 步骤 | proxy/status | 关键结果 |
| --- | --- | --- |
| summary | `console_status=blocked` | 仍因危险字段/未完成材料保持 blocked |
| camera_probe | `probe_failed` / `first_frame_timeout` | `/dev/video1 open_ok=true read_ok=false failure_reason=capture_read_call_timeout` |
| radar | `refresh_forwarded` / `refreshed` | HTTP 200，no-motion scan proof refresh 返回 |
| map | `refresh_forwarded` / `map_once_artifact_metadata_observed` | HTTP 200，map proof refresh 返回 |
| nav2 | `refresh_forwarded` / `refreshed` | HTTP 200，no-motion Nav2 proof refresh 返回 |
| stop | `command_forwarded` / `stopped` | HTTP 200，`evidence_capture_status=captured` |

收尾：

- 临时 PC API `127.0.0.1:18808` 已关闭；
- `trashbot-upper-robot-api.service=active`；
- `trashbot-local-webrtc-camera.service=active`；
- `/api/camera/health active_peer_count=0`；
- `fuser /dev/video0 /dev/video1 /dev/video2 /dev/ttyS5` 无残留 holder 输出。

## 剩余风险

- 一键巡检证明 PC 页面可以串起当前固定代理证据采集，但不等于完整真实任务闭环完成。
- 相机仍卡在 `/dev/video1` 首帧 timeout，实时图传可见内容未恢复。
- 手动非 stop 运动仍缺现场材料：`visible_content_proven=true`、外部视频、轮速反馈非零和
  LiDAR motion delta；因此本轮只调用 stop，不放行前进/后退/转向。
