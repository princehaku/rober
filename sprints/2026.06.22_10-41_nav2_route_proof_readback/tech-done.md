# 2026-06-22 Nav2 Route Proof Readback

sprint_type: micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - managed runtime 启动 `lifecycle_manager` 前增加 3 秒延迟，降低 map_server/AMCL service 发现竞态。
  - 默认 managed map 选择改为优先挑选包含 free cell 的 canonical map YAML/PGM，避免继续使用空 `trashbot_map.yaml`。
  - `map_yaml_runtime_analysis` 支持 inline `origin: [x, y, yaw]`。
  - 当本轮 managed runtime 已加载可用地图且 `/map` 被观测到时，用本轮运行时证据覆盖旧 canonical map proof blocker。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖 lifecycle 延迟、可用地图选择、inline origin、managed map 输入接管逻辑。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC fixed Nav2 proof body 不再写死空地图路径。
  - PC summary 的 proof 布尔和 path 点数聚合改为 proof-first，避免旧失败 readback 覆盖最新成功 proof。
- `pc-tools/workstation/test/catalog.test.ts`
  - 同步 fixed body 合同。
- `docs/product/pc_tools_workstation.md`
  - 记录默认上位机 Nav2 proof 已能展示 path 成功，但真实运动仍锁定。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 managed map Nav2 no-motion proof 的现场证据与安全边界。

## 验证结果

- 本地 helper：
  - `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：35 tests passed。
- 本地语法：
  - `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py`
  - 结果：通过。
- PC workstation：
  - `npm test`
  - 结果：2 files / 99 tests passed。
  - `npm run lint`
  - 结果：通过。
  - `npm run build`
  - 结果：通过。
- 上位机部署验证：
  - `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `ssh root@192.168.1.11 -p 37878 "python3 -m py_compile /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py"`
  - 结果：通过。
- 真实 PC proxy Nav2 proof：
  - `POST http://127.0.0.1:8787/api/robot-control/nav2/proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 结果：`last_result_status=refreshed`，`latest_proof_status=nav2_no_motion_path_generation_runtime_observed`，`evidence_ref=o10-amcl-nav2-runtime-1782095872075`。
  - 上位机 artifact：`managed_runtime_map_yaml=/root/rober/onboard/runtime/maps/fixed_free_cells_20260622_0112.yaml`，`managed_runtime_map_yaml_source=canonical_map_proof_usable_yaml_candidate`，`map_server_active=true`，`amcl_active=true`，`planner_server_active=true`，`initialpose_published=true`，`path_generation_succeeded=true`，`path_point_count=31`，`root_causes=[]`。
- PC summary 复验：
  - `GET http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 结果：`o3_proof_summary.path_generated=true`，`path_generation_succeeded=true`，`path_point_count=31`；同时 `safe_to_control=false`，`delivery_success=false`，`primary_actions_enabled=false`。

## 剩余风险

- 本轮只证明 Nav2 no-motion `ComputePathToPose` 可以生成路线，不证明真实 NavigateToPose、controller 执行或 fixed route delivery。
- `wheel_feedback_lr_nonzero_proven=false` 仍未完成；当前只读 T1001 样本的 `L/R` 仍为 `0/0`。
- `delivery_success=false` 仍未完成；缺真实路线执行、dropoff/cancel completion 和现场验收材料。
- PC `first_jog_readiness_summary.status=blocked_missing_visual_material`，缺 `external_video_or_visible_camera`。当前 `/dev/video1` 首帧探针仍失败，因此不应绕过门禁发送非 stop 手控。
