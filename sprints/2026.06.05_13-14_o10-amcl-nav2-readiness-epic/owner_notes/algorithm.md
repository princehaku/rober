# Algorithm Owner Note

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

本轮算法 owner 只验收 O10 AMCL/Nav2 readiness epic 中和自主能力相关的两条边界：

- 电梯图片 eval decision gate：确认真实/受控电梯图片 manifest 缺失被记录为 CEO blocker。
- AMCL/Nav2 readiness：确认当前材料仍是输入护栏和 `software_guard`，不外推为 runtime、路径生成或 path execution。

## 电梯图片 eval decision gate

结论：`KR-O10-Elevator-Image-Eval` 当前 blocked，blocker code 固定为
`real_controlled_image_manifest_missing`，evidence type 为 `blocked_with_root_cause`。

已核对材料：

- `pc-tools/evidence/fixtures/elevator_o10_image_eval_decision_gate/blocked_missing_real_or_controlled_manifest.json`
  记录 `status=blocked_missing_real_or_controlled_elevator_image_manifest`。
- checker 记录 `status=blocked_missing_real_or_controlled_images`、
  `can_run_opencv_eval=false`、`field_eval_ready=false`。
- fixture eval 只记录 `software_guard_pass=true` 和 `field_eval_ready=false`。

算法边界：

- fixture/checker 只能证明 software guard 和采集前置检查可复跑。
- PGM fixture 不代表真实相机视角、镜头高度、光照、反光、楼层屏曝光、人流遮挡或门槛几何。
- 在真实/受控 `trashbot.elevator_image_manifest.v1` 回填前，不能声明真实电梯识别、楼层 OCR、安全驶出、跨楼层送达或 delivery success。
- task record 必须保留 `image_ref`、`uncertain_reasons`、阈值和 `not_proven`。

CEO blocker：

- 需要 CEO / 现场 owner 提供非运动采集的真实或受控电梯图片集。
- manifest 必须解析到真实 JPEG/PNG/WebP/BMP 文件，且满足门开、门关、轿厢内、轿厢外、目标楼层屏、安全驶出、不安全驶出和低光/反光/遮挡/倾斜样本最低数量。
- blocker 解除前，状态机必须 fail-closed：等待、请求人工确认或人工接管，不允许把视觉输出作为真实送达依据。

## AMCL/Nav2 readiness 边界

结论：`GET /api/nav2/status.amcl_nav2_readiness` 当前仍是 readiness 输入护栏，
`evidence_type=software_guard`。它可以消费 canonical map lifecycle latest 的只读字段，
但不证明 AMCL/Nav2 runtime 或 path execution。

已核对边界：

- canonical latest JSON 固定为 `/root/rober/onboard/runtime/map_lifecycle_latest.json`。
- canonical map artifacts 固定为 `/root/rober/onboard/runtime/maps`。
- readiness 只检查 latest 载入、proof status、map once、metadata、YAML/PGM 输入齐备和 root cause。
- 不启动 ROS graph，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开底盘 UART。

仍是 `not_proven` 的项目：

- map quality pass。
- AMCL `/initialpose`、`/amcl_pose` 和定位恢复。
- map server、planner/controller lifecycle。
- Nav2 消费 `/scan` + map。
- 路径生成、fixed-route dry-run、真实路线执行和现场 path execution。

## 验收结果记录

本 note 为本轮指定验收路径补齐 Algorithm owner 复核记录；原
`owner_notes/robot-algorithm-engineer.md` 保持不动，避免覆盖已有 owner 材料。

本轮必须复跑并在最终结果中报告：

- `find pc-tools/evidence/fixtures/elevator_o10_image_eval_decision_gate -maxdepth 2 -type f -print -exec sed -n '1,180p' {} \;`
- `grep -R "real_controlled_image_manifest_missing\|blocked_with_root_cause\|not_proven\|software_guard" ...`
- `git diff --check -- docs/vision/elevator_opencv_baseline.md docs/navigation/nav2_map_quality_metrics.md pc-tools/evidence/fixtures/elevator_o10_image_eval_decision_gate sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/owner_notes/algorithm.md sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/tech-done.md`

## 剩余风险

- 真实/受控电梯图片 manifest 仍缺失，O2 不涨。
- AMCL/Nav2 runtime collector 仍未跑，O3 不涨。
- 本轮不证明 runtime、path execution、真实电梯识别、真实跨楼层送达、PC WASD、HIL、robot ACK 或 delivery success。
