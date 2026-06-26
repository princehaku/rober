# 上车端自由扫图 HTTP 与运动解锁入口

sprint_type: micro

## 实际改动

- 为 `operator_gateway_http` 增加固定 `GET /api/free-roam/autonomy/latest`、`POST /api/free-roam/autonomy/start`、`POST /api/free-roam/autonomy/stop` 路由。
- 为 `OperatorGateway` 增加 free-roam 状态机参数服务驱动：start 只设置 `operator_confirmed/mapping_active/external_stop_requested`，stop 设置 `external_stop_requested=true`；HTTP 请求体不允许打开 `enable_cmd_vel_publish`、`motion_hil_unlocked` 或修改 `cmd_vel_topic`。
- 为 `learn.launch.py` 与 `bringup.launch.py` 暴露 `free_roam_autonomy_enable_cmd_vel_publish=false`、`free_roam_autonomy_motion_hil_unlocked=false` 两个显式 launch 参数。默认仍 artifact-only，现场必须同时传 true 才能让 `free_roam_autonomy_node` 发布受限 `/cmd_vel`。
- 同步更新 free-roam 产品设计文档，明确“车能低速自由移动”不硬依赖雷达；相机和雷达 readiness 只决定本轮是否可视为可建图。

## 验证结果

- 通过：`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`，`Ran 60 tests in 32.424s OK`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`，`Ran 17 tests in 0.025s OK`。
- 通过：`PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`，`Ran 15 tests in 0.037s OK`。
- 通过：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`。
- 通过：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，`Summary: 6 packages finished [43.1s]`。
- 通过：`git diff --check`。
- live smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 HTTP 200、Robot API `readable`、`free_roam_autonomy_start_ready=true`、label `自动扫图（勾确认后可启动）`；当前现场 runtime 仍是 `artifact_only=true`、`cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮给上车端补齐 free-roam HTTP 控制面和显式运动解锁入口，但没有在真实车上打开 launch 双参数，也没有声明 wheel raw L/R 已非零。
- 当前 live 摄像头仍是 `capture_read_returned_false` 且雷达 latest 不新鲜；这不阻止低速自由移动入口，但仍阻止“雷达和摄像头都 ready 后可建图”的现场验收。
