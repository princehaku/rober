# 2026.06.28 12:07 Nav2 dynamic TF stamp0 path proof

sprint_type: micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 放宽 ROS2 preflight：`command -v ros2` 从 3 秒改为 6 秒，避免真实上位机 API 子进程首次 source ROS/workspace 时误判 ROS2 不可用。
- `/initialpose` payload 显式设置 `header.stamp={sec:0,nanosec:0}`，让 AMCL/TF 使用 latest transform，避免 managed runtime 刚启动时 initialpose 时间早于 TF buffer 被拒。
- TF source diagnostics 现在同时接受 `/tf` 动态 `odom->base_link` 和 `/tf_static` no-motion 兜底 `odom->base_link`；artifact 额外输出 dynamic/static 两个来源布尔，避免真实 bridge 动态 odom 被误报为缺 static TF。
- `onboard/tests/test_nav2_runtime_proof_helper.py` 增加 3 个回归测试：preflight 预算、initialpose stamp=0、动态 odom->base_link 识别。
- 已把同一 helper 同步到真实上位机 `/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 并完成 no-motion live proof。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 通过：43 tests。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover onboard/tests` 通过：208 tests。
- 真实上位机 py_compile 通过，并确认脚本包含 `ROS2_PREFLIGHT_TIMEOUT_S=6.0`、initialpose `stamp=0` 和动态 odom TF 识别逻辑。
- 真实上位机固定 no-motion refresh：`POST http://127.0.0.1:8787/api/nav2/proof/refresh` 返回 `status=refreshed`、`proof_state=nav2_no_motion_path_generation_runtime_observed`、`evidence_type=robot_runtime_material`、`path_generated=True`、`path_point_count=18`、`tf_chain` 四段全 true、`root_causes=[]`。回包仍声明 `blocked_commands_not_sent` 包含 `T=1/T=13/T=130/T=131`、`/cmd_vel` 和 `/api/base/manual`。
- 真实上位机 `/api/nav2/status` 随后显示 `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`、`latest_path_generated=True`、`latest_path_point_count=18`、TF chain 四段全 true。

## 剩余风险

- 本轮没有执行 NavigateToPose、PC 行程按钮、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实完整路线执行、wheel raw L/R 非零和 delivery success 仍未完成。
- 最新 proof 证明自动驾驶服务、AMCL/TF 和 planner 能 no-motion 生成路线；如果下一次真实发车 wheel raw L/R 仍为 `0/0`，问题应继续定位到底盘命令模式、bridge feedback 或 WAVE ROVER 反馈链路，而不是再归咎于相机/雷达/TF 路线准备。
