# Nav2 路线地图叠加 Micro Sprint

- sprint_type: micro
- owner: full-stack-software-engineer
- started_at: 2026-06-25 15:20 CST
- finished_at: 2026-06-25 15:21 CST
- scope: PC 普通用户首屏真实地图上的 Nav2 路线预览可视化；不新增运动控制入口。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - ComputePathToPose 成功后新增 `path_preview_points`、`path_preview_point_count`、`path_preview_source_point_count`、`path_preview_frame_id`。
  - 路线预览点最多保留 64 个，超长路线等距抽样并保留首尾，避免 artifact 过大拖慢 PC 首屏。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `RobotApiProofSummary` 增加结构化 `RobotApiPathPreviewPoint` 和路线预览计数字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 `nav2_proof_latest` 原始 payload 提取并清洗路线预览点。
  - Nav2 no-motion proof refresh 的短摘要增加路线预览计数字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在真实地图 overlay 内按 map origin/resolution 将路线点转换为 SVG polyline。
  - 仅在路线点属于 `map` frame 且至少两个有效点时显示路线，不伪造坐标。
- `pc-tools/workstation/src/styles.css`
  - 增加路线 overlay 样式，路线层不接收鼠标事件，目标点和机器人/雷达标记保持在上层。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展终点 overlay 用例，断言真实地图上同时绘制路线 polyline，且不调用导航执行、送达确认或手控接口。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 summary 对 `path_preview_points` 的结构化透出断言。

## 验证结果

- `cd pc-tools/workstation && npm test`
  - 通过：2 个 test files，154 个用例全部通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过：ESLint 无报错。
- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 通过：Python 语法检查无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部通过。
- `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py && ssh -p 37878 root@192.168.1.11 'python3 -m py_compile /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py'`
  - 通过：上位机 proof 脚本已部署并通过远端语法检查。
- 上位机 API 重启
  - 通过：`upper_robot_api.py` 以原参数重启，监听 `0.0.0.0:8787`，新 PID 为 `78061`。
- `curl -X POST http://192.168.1.11:8787/api/nav2/proof/refresh ...`
  - 收口：`status=blocked_with_root_cause`，`robot_control_executed=false`，没有执行 NavigateToPose、底盘运动或 `/cmd_vel`。
  - 根因：当前 `/scan_once_not_observed`、`/amcl_pose_once_not_observed`，因此 `path_generation_boundary=path_generation_blocked_by_localization_not_ready`，`path_preview_point_count=0`。
- PC 端 `screen -dmS rober-pc-7001 ... npm run api:public`
  - 通过：Node API 监听 `0.0.0.0:7001`，进程 PID 为 `30133`。
- 浏览器 DOM smoke：`http://127.0.0.1:7001`
  - 通过：普通用户首屏加载成功，默认小车地址为 `192.168.1.11:8787`。
  - 通过：真实地图 `fixed_free_cells_20260622_0112` 显示为“地图可见”，目标点 marker 显示。
  - 预期未显示：路线 polyline 未显示，因为真实上位机当前 `path_preview_point_count=0`；单测已覆盖有路线点时 polyline 绘制。

## 剩余风险

- 本轮只完成 no-motion ComputePathToPose 路线结果的地图可视化；没有触发真实 Nav2 goal、底盘运动、雷达 start、地图 start 或 `/cmd_vel`。
- 上位机已部署新的 `o10_amcl_nav2_runtime_proof.py`；但当前真实环境 scan/amcl_pose 未准备好，重新刷新 Nav2 no-motion proof 后仍没有路线点。待 `/scan` 和 `/amcl_pose` 恢复后，真实 `path_preview_points` 才会出现在 PC 首屏。
- “小车自由跑动建图，像扫地机一样”仍需要单独设计安全 gate、运行态和验收证据；本轮没有新增该运动能力。
