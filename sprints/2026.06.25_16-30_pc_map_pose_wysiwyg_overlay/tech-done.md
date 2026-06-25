# PC 地图真实 Pose Overlay

sprint_type: micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：新增 `/amcl_pose` YAML 解析，提取 `frame_id/x/y/z/yaw/source` 并写入 localization proof 的 `amcl_pose`。解析失败保持空值，不伪造坐标。
- `onboard/scripts/upper_robot_api.py`：`/api/localize/proof/latest` 与 `/api/localize/reset` 透出只读 `amcl_pose`，让 PC 能消费定位坐标。
- `pc-tools/workstation/src/shared/contracts.ts`、`src/server/robotControlSummary.ts`：Robot Control summary 新增 `o3_proof_summary.robot_pose`，只从 localize proof 的结构化 pose 提取 map-frame 坐标。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`src/styles.css`：普通首屏地图在真实 map preview + `robot_pose.frame_id=map` 时，把机器人 marker、雷达扇区、雷达脉冲和 scan 点落到真实地图坐标；没有 x/y 时不再用地图中心冒充位置。
- `onboard/tests/test_nav2_runtime_proof_helper.py`、`onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补 O10 pose 解析、upper API 透出、PC summary 提取和地图 overlay 坐标渲染测试。
- `docs/product/pc_tools_workstation.md`：同步记录 pose 坐标贯通和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、154 个 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，完成 app/server TypeScript 与 Vite production build。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_upper_robot_api`：通过，74 个 tests。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 smoke：`/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`；真实上位机 summary 返回 `console_status=loaded_fail_closed_summary`、`robot_pose=null`、`amcl_pose_observed=false`、`localization_tf_observed=true`、`scan_preview_point_count=0`、`safe_to_control=false`。因此当前现场仍不会画假机器人坐标，需要上位机部署本轮 localization pose 合同并刷新 localization proof 后才会显示真实 pose。

## 剩余风险

- 真实地图坐标 overlay 依赖上位机 localization artifact 里有 `amcl_pose`；如果现场只读到 AMCL/TF observed 布尔但没有 x/y/yaw，PC 会继续显示“位置未读到”，不会画假坐标。
- scan 点目前按机器人局部坐标和 pose yaw 转到 map-frame，仍未处理 laser_frame 到 base_link 的外参偏移；后续若上位机提供 tf 后的 scan map 点，可替换为更精确的全局点云。
- 本轮没有启动雷达、Nav2 execute、manual、keyboard、stop、delivery 或 `/cmd_vel`。
