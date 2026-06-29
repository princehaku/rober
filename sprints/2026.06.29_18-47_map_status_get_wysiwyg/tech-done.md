# 2026.06.29 18:47 map status GET WYSIWYG

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `ROUTE_PATHS["map_status"]=/api/map/status`。
  - 新增 aiohttp `GET /api/map/status` handler，直接返回既有 `api.map_status()` 只读结果。
  - `map_status.routes.status` 自描述该只读入口，方便现场脚本发现。
- `onboard/tests/test_upper_robot_api.py`
  - 补充 `map_status.routes.status`、非运动边界和 `create_app()` GET route 注册断言。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 `/api/map/status` 作为地图所见即所得只读入口，不触发建图、保存、proof refresh 或运动命令。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_o11_nav2_goal_execution_proof`
  - 结果：`Ran 96 tests in 0.204s / OK (skipped=1)`；skip 原因是本机轻量单测环境未安装 `aiohttp`，route 注册断言在具备 aiohttp 的上车服务部署验证覆盖。
- 已通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o11_nav2_goal_execution_proof.py`
- 已通过：`git diff --check`
- 已部署并通过上位机只读验证：
  - `scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`
  - `systemctl restart trashbot-upper-robot-api.service` 后服务 `active`
  - `GET http://127.0.0.1:8787/api/map/status` 返回 200 JSON：
    `status=map_once_artifact_metadata_observed`、`routes.status=/api/map/status`、`sends_commands=false`、`sends_motion_commands=false`、`sends_base_motion_commands=false`

## 剩余风险

- 本轮只补地图状态只读入口，不刷新地图画面、不启动雷达、不启动建图，也不证明 Nav2 实车路线或摄像头首帧已恢复。
- 当前 live 仍显示相机 UVC 无首帧、雷达 lifecycle stopped；建图启动仍应保持 `free_roam_mapping_start_ready=false`。
