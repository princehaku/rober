# PC 雷达外参地图 Overlay

sprint_type: micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：新增 `tf2_echo` transform 数值解析，从 `Translation [...]` 与 quaternion `Rotation [...]` 提取 `base_link_to_laser_frame_transform` 的平移和 yaw；缺完整数值时保持空值，不写默认偏移。
- `onboard/scripts/upper_robot_api.py`：`/api/localize/proof/latest` 与 `/api/localize/reset` 透出只读 `base_link_to_laser_frame_transform`。
- `pc-tools/workstation/src/shared/contracts.ts`、`src/server/robotControlSummary.ts`：Robot Control summary 新增 `frame_transforms.base_link_to_laser_frame`，只从 localization proof 的显式外参字段标准化。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图渲染 `laser/laser_frame` scan 点时，若外参存在，先从雷达坐标转 base_link，再按 `robot_pose` 转 map-frame；短状态显示 `已套用雷达外参`。外参缺失时仍使用旧相对点位逻辑，不声称已校准安装偏移。
- `onboard/tests/test_nav2_runtime_proof_helper.py`、`onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖 tf2_echo 外参解析、upper API 透出、PC summary 标准化和地图点位套用外参后的坐标变化。
- `docs/product/pc_tools_workstation.md`：同步记录雷达外参 overlay 合同和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、154 个 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，完成 app/server TypeScript 与 Vite production build。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_upper_robot_api`：通过，74 个 tests。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 smoke：`/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`；真实上位机 summary 当前返回 `robot_pose=null`、`frame_transforms.base_link_to_laser_frame=null`、`scan_preview_point_count=0`、`safe_to_control=false`，所以 PC 会保持安全回退，不画校准外参或假 scan 点。

## 剩余风险

- 真实外参显示依赖上位机 O10 localization artifact 里存在 `base_link_to_laser_frame_transform`；如果现场走 source inventory fast path 但没有 tf2_echo 数值，PC 会继续不显示“已套用雷达外参”。
- 当前只处理 2D 平移和 yaw；若后续真实安装存在明显 roll/pitch 或高度影响，需要上位机提供已经投影到 map-frame 的 scan 点。
- 本轮没有启动雷达、Nav2 execute、manual、keyboard、stop、delivery 或 `/cmd_vel`。
