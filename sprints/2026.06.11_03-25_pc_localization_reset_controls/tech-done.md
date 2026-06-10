# PC Localization Reset Controls Micro Sprint

## sprint_type

micro

## 自主能力目标和本轮抓手

目标：继续推进真实上车 evidence capture 的定位/导航前置能力，新增一个高级诊断专用的 no-motion 定位重置/AMCL proof 入口。

本轮抓手：

- 上位机 `POST /api/localize/reset` 默认调用 `o10_amcl_nav2_runtime_proof.py`，写 `runtime/localization_reset_latest.json`。
- `GET /api/localize/proof/latest` 摘要 helper artifact 中的 `/initialpose`、`/amcl_pose`、localization TF、managed runtime 和 root causes。
- PC workstation 新增固定代理 `POST /api/robot-control/localize/reset?baseUrl=...`，浏览器不能传任意 body 或 endpoint。
- UI 只在默认关闭的 `高级诊断 -> Nav2 规划详情` 放 `定位重置（高级）`，普通首屏仍保持 5 张卡片和普通动作。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `POST /api/localize/reset` 改为默认调用内置 `o10_amcl_nav2_runtime_proof.py`，输出 `runtime/localization_reset_latest.json`。
  - `GET /api/localize/proof/latest` 新增 helper artifact 摘要：`initialpose_published`、`amcl_pose_observed`、`localization_tf_observed`、`managed_runtime_started`、`managed_runtime_cleanup_ok`、`root_causes`。
  - 修复 helper timeout 后 latest missing 和 managed runtime 残留问题：wrapper timeout 会写 blocked fallback artifact，并按项目 localization runtime 命令特征清理残留进程组。
- `pc-tools/workstation/src/server/*`、`src/client/workstationApi.ts`、`src/shared/contracts.ts`
  - 新增固定代理 `POST /api/robot-control/localize/reset?baseUrl=...`，固定 body，浏览器不能传任意 body/endpoint。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 只在默认关闭的 `高级诊断 -> Nav2 规划详情` 新增 `定位重置（高级）` 按钮和摘要。
  - 普通首屏仍保持 5 张卡片：连接、画面、雷达、地图、移动/导航。
- `onboard/tests/*`、`pc-tools/workstation/test/*`
  - 覆盖上位机 reset 默认 helper 参数、latest 摘要、安全字段、timeout fallback artifact、PC fixed proxy body、UI 首屏禁词。
- `docs/navigation/fixed_route_workflow.md`、`docs/product/pc_tools_workstation.md`、`docs/hardware/board_sensor_stack_smoke.md`
  - 同步 no-motion localization reset 边界和 vendor/source boundary。

接口影响：

- 新增/强化上位机 `POST /api/localize/reset` 行为：默认 helper，不再依赖 `ROBER_LOCALIZE_RESET_COMMAND`。
- 新增 PC 代理 `POST /api/robot-control/localize/reset?baseUrl=<upper-api>`。
- 所有响应继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 本轮不触碰底盘驱动、launch 硬件配置、`docs/vendor/**`。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 通过：`Ran 33 tests ... OK`
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 通过，无输出。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc` + `vite build` + server `tsc`。
- `cd pc-tools/workstation && npm run test`
  - 通过：`Test Files 2 passed (2)`, `Tests 80 passed (80)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无输出。
- `git diff --check`
  - 通过，无输出。

真实上位机 smoke：

- SSH `root@192.168.1.11 -p 37878` 可用，`trashbot-upper-robot-api.service` 重启后 `active`。
- 远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- 直连上位机 final2：
  - `POST http://192.168.1.11:8787/api/localize/reset` 在 PC 预算内返回结构化结果。
  - `status=blocked_with_root_cause`，`fallback_artifact_written=true`。
  - root cause：`helper_process_timeout_before_artifact`。
  - `GET /api/localize/proof/latest` 返回 HTTP 200 语义的 loaded artifact 摘要：`status=blocked_with_root_cause`，`artifact.status=loaded`。
  - 安全字段保持 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。
- PC 代理 final2：
  - `POST http://127.0.0.1:8791/api/robot-control/localize/reset?baseUrl=http://192.168.1.11:8787`
  - 返回 `proxy_status=refresh_forwarded`、`remote_endpoint=/api/localize/reset`、`remote_http_status=200`、`last_result_status=blocked_with_root_cause`。
- 最终远端清场：
  - `trashbot-upper-robot-api.service=active`。
  - 无残留 `o10_amcl_nav2_runtime_proof`、`lidar_driver`、`map_server`、`amcl`、`planner_server` 目标进程；`pgrep` 只匹配当前检查 shell。
  - `/dev/ttyS5` 和 `/dev/ttyACM0` 无 `lsof`/`fuser` 占用。

## 真实上位机 smoke artifact 路径

- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_deploy_restart.log`
- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_localize_reset_post_final2.json`
- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_localize_proof_latest_final2.json`
- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/pc_proxy_localize_reset_final2.json`
- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_final_cleanup_final2.log`
- `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_final_cleanup_after_pc_proxy_final2.log`
- 失败定位和修复过程保留：
  - `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_manual_cleanup_after_timeout.log`
  - `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_manual_cleanup_pgid.log`
  - `sprints/2026.06.11_03-25_pc_localization_reset_controls/artifacts/remote_manual_cleanup_after_fixed_wrapper_failure.log`

## 剩余风险

- 本轮真实上位机 localization reset 仍未观察到 `/initialpose` 成功发布、`/amcl_pose` 或 localization TF；当前 root cause 是 wrapper 预算内 helper timeout。已修复为结构化 blocked artifact 和无残留清场，不再 missing 或占用设备。
- 该入口只证明 PC/上位机 no-motion AMCL proof 入口和安全边界，不证明 Nav2 path execution、fixed-route、真实运动、HIL pass 或 delivery success。
- WAVE ROVER base UART vendor/source boundary：事实来源是 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料；底盘 UART 是 newline JSON，项目证据使用 `/dev/ttyS5 @ 115200`。本轮没有打开 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131`，没有触碰底盘运动。
