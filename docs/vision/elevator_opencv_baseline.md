# Elevator OpenCV Baseline

## 目标和边界

本页记录 O2 电梯 assisted delivery 的最小视觉 baseline。它只建立
taxonomy、ROI/rule helper、offline eval artifact 和测试护栏，不证明真实电梯
识别、真实楼层 OCR、真实进出电梯或跨楼层送达完成。

实现入口：

```bash
python3 -m ros2_trashbot_vision.elevator_opencv_baseline <manifest.json>
```

manifest 必须保留真实图片目录输入：

```json
{
  "schema": "trashbot.elevator_image_manifest.v1",
  "image_dir": "/path/to/real-or-fixture-images",
  "samples": [
    {
      "sample_id": "elevator_open_inside_f3_001",
      "image": "frame001.jpg",
      "target_floor": "3",
      "expected_floor": "",
      "expected_door_state": "open",
      "expected_inside_outside": "inside",
      "expected_safe_to_exit": "safe"
    }
  ]
}
```

当前单元测试使用合成 PGM fixture。JPEG/PNG 等真实图片输入会在运行环境安装
`cv2` 后走 OpenCV 灰度读取；没有 `cv2` 时只支持 PGM fixture，因此不能把
测试通过解释成真实相机材料通过。

## Taxonomy

`elevator_opencv_baseline.py` 输出 `trashbot.elevator_opencv_baseline.v1`：

- `door_state`: `open`、`closed`、`uncertain`。
- `inside_outside`: `inside`、`outside`、`uncertain`。
- `floor_roi`: 楼层显示屏候选 ROI，只给状态链和采样工具定位，不做 OCR。
- `target_floor_candidate`: manifest 提供或 ROI 规则给出的候选字符串；为空表示未确认。
- `safe_to_exit`: `safe`、`unsafe`、`uncertain`。
- `confidence`: 多个规则的最小置信度，状态机应按 fail-closed 使用。
- `uncertain_reasons`: 门未开、楼层未确认、出口 ROI 异常、光照不可判定等原因。
- `not_proven`: 固定包含真实相机识别、楼层 OCR、安全驶出、跨楼层送达等未证明项。

taxonomy 现在显式给出样本类，供采集和 eval manifest 对齐：

| 样本类 | 最低数量 | 正例定义 | 负例/失败边界 |
| --- | ---: | --- | --- |
| `door_open_positive` | 20 | 电梯门完全打开，中央门缝/亮带可解释 | 半开、反光、遮挡不并入正例 |
| `door_closed_positive` | 20 | 电梯门关闭，门板/门缝可见 | 开门亮带、玻璃反光需单独标负例 |
| `inside_positive` | 20 | 摄像头在轿厢内，门板/内壁视角明确 | 阈值附近或门槛位置降级 uncertain |
| `outside_negative` | 20 | 电梯厅外视角 | 站在门槛线附近不算 inside 正例 |
| `floor_target_positive` | 20 | 楼层屏 ROI 可见且人工标注 target/expected 一致 | 这是 manifest truth，不是 OCR truth |
| `safe_exit_positive` | 20 | 门开、目标楼层候选匹配、出口 ROI 无明显暗障碍 | 不等于 Nav2 动态避障或真实可驶出 |
| `safe_exit_negative` | 20 | 门关、楼层不符、出口障碍或视野过暗 | 必须保留具体 unsafe reason |
| `uncertain_or_bad_light` | 10 | 强反光、低照度、遮挡、过曝、倾斜 | 不允许强行归入 open/safe |

## ROI 和规则

默认 ROI 使用归一化坐标，避免不同分辨率直接破坏阈值：

| ROI | 用途 |
| --- | --- |
| `door_gap` | 中央门缝/开门亮带或暗带候选 |
| `door_panel_left` / `door_panel_right` | 门板背景亮度，对比 `door_gap` |
| `floor_display` | 楼层显示屏候选框 |
| `exit_path` | 画面下方可驶出区域的低成本 guard |

门开/关只比较 `door_gap` 与左右门板均值差。差异足够大时输出 `open`，差异很
小时输出 `closed`，中间区间输出 `uncertain`。`safe_to_exit` 需要门开、画面
判断在轿厢内、目标楼层候选匹配、出口 ROI 均值达标；任一缺失都输出
`unsafe` 或 `uncertain`。

## Offline Eval Artifact

`evaluate_manifest()` 输出 `trashbot.elevator_offline_eval.v1`，包含：

- `predictions`: 每张图片的 schema、ROI stats、阈值、预测、置信度和原因。
- `confusion.door_state`: `tp/tn/fp/fn/uncertain`。
- `confusion.safe_to_exit`: `tp/tn/fp/fn/uncertain`。
- `confusion.inside_outside`: `matches/mismatches/uncertain`。
- `sample_coverage`: 每个 taxonomy class 的样本数量、最低数量和缺口。
- `quality_metrics`: door/safe 的 precision、recall、FP/FN rate、uncertain_total。
- `acceptance_gates.software_guard`: 只证明 fixture/offline guard 是否通过。
- `acceptance_gates.field_eval`: 要求真实或受控图片 manifest 满足最低数量，当前 fixture 必定不通过。
- `operator_summary`: 给 PC/手机状态页消费的简短安全摘要。
- `not_proven`: 明确 offline eval 不等于真实电梯识别完成。

当前可复跑 fixture：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision \
python3 -m ros2_trashbot_vision.elevator_opencv_baseline \
  pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
```

该 fixture 覆盖门开安全、门关外部、低光不可判定三类 software guard。它只用于
回归测试和工作站 evidence 索引，不得写成真实电梯现场完成。

建议真实采集最小样本要求：

- 门开正例不少于 20 张。
- 门关正例不少于 20 张。
- 轿厢内正例不少于 20 张。
- 轿厢外负例不少于 20 张。
- 低照度、遮挡、反光、画面倾斜等不可判定样本不少于 10 张。

## Nav2 / Map Quality 指标

Worker C 同步增加 `trashbot.nav2_map_quality.v1` 离线指标：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_nav \
python3 -m ros2_trashbot_nav.map_quality_metrics \
  pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/map.yaml \
  --waypoints pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/waypoints.json
```

输出指标包括：

- `coverage_area_m2`、`free_ratio`、`occupied_ratio`、`unknown_ratio`。
- `save_load_consistency`: YAML/image/resolution/origin/dimension 是否可离线加载。
- `waypoint_reachability`: 每个 waypoint 落在 free、occupied、unknown 或 out_of_bounds。
- `quality_gates.software_guard_pass`: coverage、unknown ratio、waypoint reachable ratio 的离线门槛。
- `failure_samples`: 可以直接给 operator/debug 页展示的失败原因。

该指标只证明 map artifact 形状和路线候选的离线质量，不证明 SLAM Toolbox 已输出
真实 `/map`、AMCL 已恢复定位、Nav2 已消费 `/scan` + map，也不证明固定路线实跑。
导航侧复跑命令、预期 `exit_code=1` 的 fail-closed fixture 语义和真实 map artifact
切换入口见 `docs/navigation/nav2_map_quality_metrics.md`。

## 当前风险

当前 baseline 是可解释软件抓手，不是鲁棒模型。强反光、玻璃门、低照度、楼层屏
过曝、摄像头角度变化和出口障碍物都可能触发误判。进入 ROS2 状态链前，必须把
`uncertain_reasons`、`not_proven` 和原始图片引用写入 task record，并让状态机
默认人工接管或等待更多证据。
