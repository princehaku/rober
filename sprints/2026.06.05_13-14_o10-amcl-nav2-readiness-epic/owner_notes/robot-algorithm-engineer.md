# Robot Algorithm Engineer Owner Note

## sprint_type

sprint_type: epic

## 自主能力目标

本轮算法侧目标是 `KR-O10-Elevator-Image-Eval` 的决策门：确认 OpenCV baseline 是否已有真实或受控电梯图片 manifest 可进入 field eval，并给出可执行的 FP/FN/uncertain、阈值、混淆项和人工接管策略。

## 现有材料结论

- 未发现可接受的真实/受控 `trashbot.elevator_image_manifest.v1`。
- 电梯图片候选仍只有 `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/*.pgm` fixture。
- `pc-tools/evidence/templates/elevator_image_manifest_collection_template.json` 仍是 placeholder 模板。
- 其他 JPG/PNG 来自 vendor 文档或手机/PC UI 截图，不是电梯 field eval 材料。

## 实际改动

- 新增 `pc-tools/evidence/fixtures/elevator_o10_image_eval_decision_gate/blocked_missing_real_or_controlled_manifest.json`。
- 更新 `docs/vision/elevator_opencv_baseline.md`，补充 2026-06-05 O10 决策门、checker 输出、fixture eval 输出、样本缺口和人工接管策略。
- 新增本 owner note。

## 接口影响

- 无 ROS2 topic/action/service 变更。
- 无 `TrashStatus` / action 契约变更。
- 无 Nav2、AMCL、behavior 状态机或硬件配置变更。
- 新增 evidence artifact 只用于 O10/O2 决策门和 Product 收口。

## Checker / Eval 输出

Template checker：

```text
command: PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline --check-template pc-tools/evidence/templates/elevator_image_manifest_collection_template.json
status: blocked_missing_real_or_controlled_images
evidence_type: blocked_with_root_cause
can_run_opencv_eval: false
field_eval_ready: false
template_placeholders: 8
image_kinds: fixture=0, real_or_controlled=0, missing_or_invalid=8
missing_to_field_minimum:
  door_open_positive=14
  door_closed_positive=19
  inside_positive=15
  outside_negative=18
  floor_target_positive=17
  safe_exit_positive=17
  safe_exit_negative=16
  uncertain_or_bad_light=9
```

Fixture eval：

```text
command: PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
evaluated_count: 3
software_guard_pass: true
field_eval_ready: false
door_state: tp=1, tn=1, fp=0, fn=0, uncertain=1
safe_to_exit: tp=1, tn=1, fp=0, fn=0, uncertain=1
inside_outside: matches=2, mismatches=0, uncertain=0
operator_uncertain_total: 2
thresholds: open_gap_delta=38.0, closed_gap_delta=16.0, dark_inside_mean=88.0, safe_exit_mean=105.0, floor_panel_delta=28.0, min_confidence=0.58
```

## CEO Blocker

`KR-O10-Elevator-Image-Eval` 当前 blocked。需要 CEO / 现场 owner 提供非运动采集的真实或受控电梯图片集，并回填一个解析到真实文件的 `trashbot.elevator_image_manifest.v1`。

最低样本要求：

- `door_open_positive`: 20
- `door_closed_positive`: 20
- `inside_positive`: 20
- `outside_negative`: 20
- `floor_target_positive`: 20
- `safe_exit_positive`: 20
- `safe_exit_negative`: 20
- `uncertain_or_bad_light`: 10

采集要求：

- 先做非运动采集，不发送底盘运动命令。
- manifest 必须写 `site_ref`、`camera_ref`、`route_ref`、collector、time window、lighting/reflection notes 和 safety notes。
- 场景必须覆盖电梯厅外、轿厢内、门开、门关、目标楼层屏、非目标楼层屏、安全出口、不安全出口、低光、反光、遮挡和倾斜画面。
- 图片文件必须是可解析的 JPEG/PNG/WebP/BMP；PGM fixture 不作为 O10/O2 field material。

为什么不能继续涨 O10/O2：

- 当前没有真实/受控图片 manifest。
- fixture FP/FN 不测真实相机视角、镜头高度、光照、反光、楼层屏曝光、人流遮挡或门槛几何。
- 没有 field eval 就不能给行为状态机提供真实电梯门、目标楼层或安全驶出证据。

## 人工接管策略

- `door_state != open`：等待或请求人工开门/协助。
- `inside_outside == uncertain`：停车，请求人工确认是否已在轿厢内。
- `target_floor_candidate != target_floor`：继续等待，并请求人工确认楼层。
- `safe_to_exit != safe` 或 `confidence < min_confidence`：停止，进入人工接管。
- task record 必须保留 `image_ref`、`uncertain_reasons`、阈值和 `not_proven`。

## evidence_type

`blocked_with_root_cause`。本轮只证明 checker/eval 决策门可复跑，不证明真实电梯识别、楼层 OCR、安全驶出、跨楼层送达、Nav2 消费或 delivery success。
