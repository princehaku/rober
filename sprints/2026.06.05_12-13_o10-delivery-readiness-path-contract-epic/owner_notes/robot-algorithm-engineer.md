# Robot Algorithm Engineer Owner Note

## sprint_type

sprint_type: epic

## 本轮结论

本轮算法侧只做 readiness 判断和证据边界确认，不修改 Robot Software 正在锁定的
upper API/path contract。结论是：在 Robot Software 没有返回 canonical
`map_lifecycle_latest.json` 路径、远端 refresh/latest/readback 同链路证据、以及真实
map artifact 之前，算法侧不能把 O10 推进到 AMCL/Nav2 readiness；当前只能保留
`blocked_with_root_cause`，等待 path contract lock 后进入下一步。

Nav2/map quality 当前只有 ROS-free offline guard。`docs/navigation/nav2_map_quality_metrics.md`
明确该工具只读取 map YAML/PGM 和 waypoint JSON，不连接 ROS graph，不证明真实
`/map`、AMCL、TF、`/scan` 消费或固定路线实跑。fixture 还被设计成
fail-closed：4 个 waypoint 只有 1 个在 free cell，预期退出码为 1。

电梯 OpenCV 当前没有真实/受控图片 manifest。仓库证据只包含
`pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json`、
PGM fixture，以及
`pc-tools/evidence/fixtures/elevator_real_image_manifest_blocker/blocked_missing_manifest.json`。
这些只能证明 software guard 和 blocker，不能作为 O2/O10 field material 或 OpenCV
field eval 证据。

## AMCL/Nav2 readiness 判断

当前不进入 AMCL/Nav2 readiness，原因如下：

- path contract 尚由 Robot Software owner 锁定中；算法侧不能猜 canonical runtime root。
- no-motion `/map` once 和 PGM/YAML 落盘只能作为前置材料，不等于地图可导航。
- 离线 map quality fixture 当前 `software_guard_pass=false` 是预期 fail-closed，不是可用路线候选。
- 尚未看到真实 map artifact + 同一 `map` frame waypoint manifest 的可达性通过记录。
- 尚未看到 AMCL `/initialpose`、`/amcl_pose`、Nav2 lifecycle active、planner/controller、TF freshness、`/scan` + map 消费证据。

进入下一步的最小可验收抓手：

1. Robot Software 先交付 canonical latest path，并在远端 8787 同一命令链证明
   `POST /api/map/proof/refresh`、`GET /api/map/proof/latest` 和文件 readback 一致。
2. Algorithm 使用该 canonical latest 指向的真实 `trashbot_map.yaml`，配合同一 `map`
   frame 的 route/waypoint JSON，运行 map quality metrics；若 waypoint reachability
   仍失败，输出失败 cell 和阻止进入 Nav2。
3. 通过离线 guard 后，再进入 no-motion AMCL/Nav2 readiness：启动 map server、
   AMCL、planner/controller，采集 lifecycle active、`/amcl_pose`、TF、planner path
   或 fixed-route dry-run 证据；仍不得发布 `/cmd_vel`。

## 电梯 image eval 判断

当前不进入 OpenCV field eval，状态为 `blocked_with_root_cause`：

- root cause：仓库没有真实或受控电梯 JPEG/PNG/WebP 图片 manifest。
- fixture PGM 只能用于回归测试，不接受为真实电梯材料。
- 不补 synthetic fixture 冒充 field material，也不把 fixture eval 写成 O2/O10 涨分。

进入下一步的最小可验收抓手：

1. 使用 `pc-tools/evidence/templates/elevator_image_manifest_collection_template.json`
   采集真实/受控电梯图片 manifest，替换 placeholder `image_dir` 和图片引用。
2. 至少覆盖门开、门关、轿厢内、轿厢外、目标楼层、安全/不安全出口、低照度/遮挡/反光等 taxonomy。
3. 先运行 template checker；只有图片引用真实存在且不再是 fixture-only 时，才运行
   `python3 -m ros2_trashbot_vision.elevator_opencv_baseline <real_or_controlled_manifest.json>`。
4. eval 输出必须保留 false positive、false negative、uncertain 样本、人工接管策略和
   `not_proven` 边界。

## 验证结果

本轮指定命令已复跑：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.map_quality_metrics pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/map.yaml --waypoints pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/waypoints.json || test $? -eq 1
python3 -m unittest onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py
git diff --check -- sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-algorithm-engineer.md
```

结果：

- Nav2 map quality fixture 输出 `schema=trashbot.nav2_map_quality.v1`、
  `proof_status=not_proven`、`quality_gates.software_guard_pass=false`、
  `reachable_ratio=0.25`，failure samples 覆盖 occupied、unknown、
  out_of_bounds；预期退出码 1 已被 `|| test $? -eq 1` 接受，命令整体通过。
- Elevator OpenCV baseline unittest：`Ran 7 tests in 0.587s`，`OK`。
- diff check：通过，无 whitespace error。

## 剩余风险

- 当前算法侧没有真实 map artifact、真实 route waypoint 或 AMCL/Nav2 runtime 证据。
- 当前电梯侧没有真实/受控图片 manifest，OpenCV field eval blocked。
- 本轮不触碰底盘、不发布 `/cmd_vel`、不改 upper API/path contract；O10 仍需 Robot
  Software 的 path contract lock 作为下一步入口。
