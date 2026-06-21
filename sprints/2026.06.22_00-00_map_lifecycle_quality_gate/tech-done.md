# 2026-06-22 00:00 Map Lifecycle Quality Gate

## sprint_type

micro

## 功能设计

目标：推进“能建图”，修正当前 map lifecycle proof 只证明 `/scan`、`/map` 和文件存在，却不评估刚保存地图是否有 free cell 的缺口。真实上位机当前 13 张 runtime map 的 PGM 像素只有 `205` unknown 和少量 `0` occupied，没有 `254` free；这不是 parser 误判，而是保存出的地图不可导航。

本轮设计：

- `o3_map_lifecycle_proof.py` 保存地图后，分析本轮 `map_name.yaml/.pgm`。
- 输出 `slam_map_quality`：map yaml、image、width/height、cell_counts、top_pixel_values、has_free_cells、navigation_quality。
- `algorithm_boundary.slam_map_quality_evaluated=true`。
- `algorithm_boundary.map_usable_for_navigation` 只有 free cell > 0 时才为 true。
- 若 free cell 为 0，在 `root_causes/blockers` 追加 `map_has_no_free_cells_after_slam_save`。
- 不改变 no-motion 边界：不发 `/cmd_vel`、不调用 `/api/base/manual`、不打开 WAVE ROVER UART。

## 实际改动

- `onboard/scripts/o3_map_lifecycle_proof.py`
  - 新增保存后地图质量分析：读取本轮 `map_name.yaml` 与对应 PGM，统计 `254/free`、`205/unknown`、`0/occupied` 以及 top pixel values。
  - 新增 `slam_map_quality` 输出，包含 map 路径、尺寸、像素统计、`has_free_cells` 与 `navigation_quality`。
  - `algorithm_boundary` 新增 `slam_map_quality_evaluated` 和 `map_usable_for_navigation`，只有 free cell 数量大于 0 才允许后者为 true。
  - 当本轮保存出的地图没有 free cell 时，`proof_status=blocked_with_root_cause`，并追加 `map_has_no_free_cells_after_slam_save`。
- `onboard/scripts/upper_robot_api.py`
  - map lifecycle latest/readback 摘要新增 `latest_map_quality_status`、`latest_map_free_cell_count`、`latest_map_usable_for_navigation`。
- `onboard/tests/test_map_lifecycle_proof_helper.py`
  - 增加 unknown-only PGM 和含 free cell PGM 的离线质量判定测试。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 map lifecycle readback 摘要对质量字段的契约测试。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC map proof refresh 的 readback key fields 纳入地图质量字段，便于高级诊断看到真实不可导航原因。
- 真实上位机 `root@192.168.1.11:37878` 已部署：
  - `onboard/scripts/o3_map_lifecycle_proof.py`
  - `onboard/scripts/upper_robot_api.py`
  - 部署后重启 `trashbot-upper-robot-api.service`，远端 sha256 与本地一致。

## 验证结果

- 本地验证：
  - `python3 -m unittest onboard.tests.test_map_lifecycle_proof_helper onboard.tests.test_upper_robot_api`：通过，39 tests OK。
  - `python3 -m py_compile onboard/scripts/o3_map_lifecycle_proof.py onboard/scripts/upper_robot_api.py`：通过。
  - `cd pc-tools/workstation && npm run test -- catalog.test.ts`：通过，79 tests OK。
  - `cd pc-tools/workstation && npm run test`：通过，98 tests OK。
  - `cd pc-tools/workstation && npm run build`：通过。
  - `cd pc-tools/workstation && npm run lint`：通过。
- 真实上位机验证：
  - `POST http://192.168.1.11:8787/api/map/proof/refresh` 输出 `proof_status=blocked_with_root_cause`。
  - `GET http://192.168.1.11:8787/api/map/proof/latest` 输出 `slam_map_quality.navigation_quality=no_free_cells`、`cell_counts.free=0`、`algorithm_boundary.map_usable_for_navigation=false`。
  - root cause 为 `map_has_no_free_cells_after_slam_save`，说明当前地图保存链路不再把“只有 unknown/occupied、没有 free cell”的 PGM 当成可导航地图。
- PC 代理验证：
  - `POST http://127.0.0.1:8787/api/robot-control/map/proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `remote_http_status=200`。
  - PC readback key values 显示 `latest_map_quality_status=no_free_cells`、`latest_map_free_cell_count=0`、`latest_map_usable_for_navigation=false`。
- 关键 artifacts：
  - `artifacts/01_upper_map_proof_refresh_quality.json`
  - `artifacts/02_upper_map_proof_latest_quality.json`
  - `artifacts/03_upper_map_list_after_quality.json`
  - `artifacts/04_pc_map_refresh_quality.json`

## 剩余风险

- 本轮只修正“建图证明”的质量门禁；没有发布 `/cmd_vel`，没有执行真实路线、Nav2 goal 或送达动作。
- 当前真实上位机保存出的 runtime maps 仍没有 free cell，结论是地图不可导航；下一步必须在安全门禁满足后进行真实移动建图，或者补齐可见相机/外部视频材料后做首次低速试动。
- `map_usable_for_navigation=false` 是当前正确 fail-closed 状态，不代表建图目标已经完成。
