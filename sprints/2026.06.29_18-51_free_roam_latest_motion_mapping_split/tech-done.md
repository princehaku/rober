# 2026.06.29 18:51 free roam latest motion/mapping split

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `GET /api/free-roam/autonomy/latest` 顶层暴露 `free_roam_motion_start_ready=true`、`motion_without_radar_allowed=true`、`free_move_without_camera_allowed=true`。
  - 同一 endpoint 顶层暴露 `mapping_readiness`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`、`free_roam_mapping_start_plain`、`free_roam_mapping_start_next_action`。
  - `free_roam_autonomy_status()` 复用 latest 的同一套分层字段，避免 PC summary 与直连 latest 口径不一致。
  - latest 内部只做只读 camera health/radar status 聚合；不调用 `free_roam_motion_readiness()`，避免递归。
- `onboard/tests/test_upper_robot_api.py`
  - 补齐 latest 在相机/雷达缺失时仍允许自由移动、但不允许建图启动的断言。
  - 补齐相机和雷达 ready 后 `free_roam_mapping_start_ready=true` 的断言。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 latest/status/PC summary 三者对“自由移动不依赖雷达/摄像头；建图才要求两者 ready”的统一口径。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_o11_nav2_goal_execution_proof`
  - 结果：`Ran 97 tests in 0.207s / OK (skipped=1)`；skip 原因仍是本机轻量单测环境未安装 `aiohttp`。
- 已通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o11_nav2_goal_execution_proof.py`
- 已通过：`git diff --check`
- 已部署并通过上位机只读验证：
  - `scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`
  - `systemctl restart trashbot-upper-robot-api.service` 后服务 `active`
  - `GET http://127.0.0.1:8787/api/free-roam/autonomy/latest` 摘要：
    `status=not_proven`、`free_roam_motion_start_ready=true`、`motion_without_radar_allowed=true`、
    `free_move_without_camera_allowed=true`、`free_roam_mapping_start_ready=false`、
    `free_roam_mapping_start_missing_reasons=[camera_first_frame_not_observed,radar_scan_proof_not_fresh]`、
    `sends_motion_commands=false`

## 剩余风险

- 本轮只统一自由移动/建图门禁读回，不实际点击 start，不发布 `/cmd_vel`，也不证明实车已自由移动。
- live 相机仍是 UVC 无首帧，雷达 lifecycle 仍 stopped；建图启动应继续保持 not ready。
