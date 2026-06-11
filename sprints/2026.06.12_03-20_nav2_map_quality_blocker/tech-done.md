# 2026.06.12 03:20 Nav2 Map Quality Blocker

## sprint_type

micro

## 实际改动

- 不使用 subagent，主会话直接修正 Nav2 no-motion proof 的地图质量判定。
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `map_has_free_cells_for_path_proof`。
  - 当当前 map YAML/PGM 分析结果显示 `free=0` 时，在调用
    `ComputePathToPose` action 前稳定 fail-closed。
  - 新 root cause 为 `map_has_no_free_cells_for_nav2_path_proof`，边界为
    `path_generation_blocked_by_map_has_no_free_cells`。
  - 保持 no-motion 边界：不调用 NavigateToPose、不发布 `/cmd_vel`、不调用
    `/api/base/manual`、不打开 WAVE ROVER UART `/dev/ttyS5`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC key values 对 object/array 改用短 JSON 摘要，避免高级诊断显示
    `[object Object]`。
  - Nav2 fixed proxy key fields 增加 `path_generation_boundary` 与 `root_causes`。
- 补充回归测试：
  - `onboard/tests/test_nav2_runtime_proof_helper.py`
  - `pc-tools/workstation/test/catalog.test.ts`
- 真实验证 artifact：
  - `artifacts/01_upper_nav2_refresh_after_map_quality_guard.json`
  - `artifacts/02_upper_nav2_latest_after_map_quality_guard.json`
  - `artifacts/03_pc_proxy_nav2_refresh_after_map_quality_guard.json`

## 验证结果

- 本地：
  - `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：32 tests OK。
  - `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：通过。
  - `cd pc-tools/workstation && npm run test -- catalog.test.ts`：77 passed。
  - `cd pc-tools/workstation && npm run test`：94 passed。
  - `cd pc-tools/workstation && npm run build`：通过。
  - `cd pc-tools/workstation && npm run lint`：通过。
  - `git diff --check`：通过。
- 真实上位机 `root@192.168.1.11:37878`：
  - 已部署 helper，远端 sha256 与本地一致：
    `31cf632fa70442f75a4aab497af741d5c68e6193c8c0873812ae4182c2234990`。
  - 远端 map inventory 显示 `runtime/maps/*.yaml` 对应 PGM 均为 `free=0`。
  - 直接 `POST /api/nav2/proof/refresh` 返回：
    `status=blocked_with_root_cause`，
    `root_causes=[{"layer":"map quality","reason":"map_has_no_free_cells_for_nav2_path_proof"}]`，
    `path_generation_boundary=path_generation_blocked_by_map_has_no_free_cells`，
    `path_generation_attempted=false`，`path_generated=false`，`path_point_count=0`。
  - PC fixed proxy `POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
    返回 `refresh_forwarded`，`remote_http_status=200`，高级诊断 key values 中
    `root_causes` 为可读 JSON，不再是 `[object Object]`。
  - 收尾：`trashbot-upper-robot-api.service` 与
    `trashbot-local-webrtc-camera.service` 均 active；未观察到 helper/Nav2/LiDAR 残留进程。

## 剩余风险

- 本轮没有把 Nav2 变成可真实移动，只是把软件证明从偶发空路径收敛为稳定地图质量 blocker。
- 当前所有已保存 map 都没有 free cell，因此还不能宣称可导航地图、真实路径执行或定位移动完成。
- 下一步要推进“建图/定位移动”，需要获得带 free cell 的真实地图；这通常依赖真实传感器姿态、
  更充分的 SLAM 采集窗口，或受控物理移动材料。
- Camera `/dev/video1` 仍是首帧 timeout；非 stop 手动移动 gate 仍缺可见图传、外部视频、
  左右轮非零反馈和 LiDAR motion delta。
