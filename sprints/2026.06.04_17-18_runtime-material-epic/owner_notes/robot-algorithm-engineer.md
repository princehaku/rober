# Robot Algorithm Engineer Owner Note

## 自主能力目标和本轮抓手

- 目标 Objective：O2 `KR-O2-Real-Image-Manifest-Eval`。
- 本轮抓手：只查找真实或受控电梯图片 manifest / evidence artifact；找到才运行 OpenCV field eval，找不到只输出 blocker，不用 fixture eval 冒充真实材料。
- 证据类型：`blocked_with_root_cause`。附带 `software_guard` 护栏结果，但不建议 O2 涨分。
- 本轮复核时间：2026-06-04 18:14:06 CST。

## 查找结论

本地 repo 和上位机都没有可验收的真实/受控电梯图片 manifest。2026-06-04 18:14 CST 复核后，现有材料只有：

- `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json`：`source=software_proof` 的 PGM fixture。
- `sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json`：现场材料提交模板，不是已回填图片。
- 多个 mobile/browser `.png` 截图 evidence：不是电梯场景图片，不可进入 OpenCV field eval。
- 上位机更深层图片搜索只找到 `docs/vendor/waveshare_wave_rover/...` 的 vendor 图片，不是 elevator field material。

Root cause：

1. 真实/受控电梯图片没有落到本地 repo、上位机 `/root`、`/tmp` 或 `/ws` 的可搜索路径。
2. 已有 `trashbot.elevator_image_manifest.v1` schema 和 OpenCV evaluator，但没有被 field owner 回填的 `image_dir` + `samples[]`。
3. 上一轮 `16-17_o2-elevator-opencv-state-integration` 已把 OpenCV artifact 接入状态链 adapter，但输入仍缺真实/受控 eval artifact。

## 验收命令和关键输出

### 本地查找

```bash
find . -iname '*elevator*' -o -iname '*manifest*' | head -80
```

关键输出：

```text
./docs/vision/elevator_opencv_baseline.md
./onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
./sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json
```

更精确图片/manifest 查找：

```bash
find . \( -path './pc-tools/workstation/node_modules' -o -path './build' -o -path './install' -o -path './log' -o -path './docs/vendor' \) -prune -o -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.pgm' \) -print | head -200
```

关键输出：

```text
./mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_followup_escalation_status.json
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/ambiguous_bad_light.pgm
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/closed_outside_unsafe.pgm
./pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/open_inside_safe_f3.pgm
./pc-tools/evidence/fixtures/field_evidence_material_blocker_escalation_pack/blocked_all_real_materials_missing.json
./pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/map.pgm
./sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_390x844.png
...
```

解释：仅有 OpenCV PGM fixture 和浏览器截图；没有真实/受控电梯 `.jpg/.png`。

### SSH 查找

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 root@192.168.1.11 -p 37878 'find /root /tmp /ws -maxdepth 5 \( -iname "*elevator*" -o -iname "*manifest*" -o -iname "*.jpg" -o -iname "*.png" \) 2>/dev/null | head -120'
```

关键输出：

```text
/root/rober/docs/product/elevator_assisted_delivery.md
/root/rober/onboard/ros2_trashbot_vision/ros2_trashbot_vision/vision_sample_manifest.py
/root/rober/onboard/ros2_trashbot_nav/ros2_trashbot_nav/elevator_assist.py
/root/rober/onboard/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_elevator_assist.py
```

补充深度搜索：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 root@192.168.1.11 -p 37878 'find /root/rober /tmp /ws -maxdepth 8 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*elevator*manifest*.json" -o -iname "*real*material*.json" \) 2>/dev/null | head -200'
```

关键输出：

```text
/root/rober/docs/vendor/waveshare_wave_rover/ugv_rpi/media/RaspRover-LED-screen.png
/root/rober/docs/vendor/waveshare_wave_rover/ugv_rpi/media/UGV-Rover-details-23.jpg
/root/rober/docs/vendor/waveshare_wave_rover/ugv_rpi/templates/pictures/placeholder_3.jpg
/root/rober/docs/vendor/waveshare_wave_rover/wiki_assets/600px-WR-web%E7%95%8C%E9%9D%A2.png
/root/rober/docs/vendor/waveshare_wave_rover/wiki_assets/360px-WAVE-ROVER-1.jpg
...
```

解释：远端没有电梯实景图片；返回的图片均为 vendor 文档资源或占位图。

### OpenCV fixture eval 护栏

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision python3 -m ros2_trashbot_vision.elevator_opencv_baseline pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/manifest.json
```

关键输出：

```json
{
  "evaluated_count": 3,
  "acceptance_gates": {
    "software_guard": {"pass": true},
    "field_eval": {"pass": false}
  },
  "operator_summary": {
    "software_guard_pass": true,
    "field_eval_ready": false,
    "field_eval_status": "needs_real_image_manifest"
  },
  "sample_coverage": {
    "image_kinds": {
      "fixture": 3,
      "real_or_controlled": 0
    },
    "field_minimum_met": false,
    "missing_to_field_minimum": {
      "door_closed_positive": 19,
      "door_open_positive": 18,
      "floor_target_positive": 19,
      "inside_positive": 19,
      "outside_negative": 19,
      "safe_exit_negative": 19,
      "safe_exit_positive": 18,
      "uncertain_or_bad_light": 9
    }
  }
}
```

解释：evaluator 可复跑，但 `real_or_controlled=0`，不能作为 O2 真实识别或真实楼层材料。

### Vision targeted tests / compile

```bash
python3 -m compileall onboard/src/ros2_trashbot_vision
python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test
```

关键输出：

```text
Listing 'onboard/src/ros2_trashbot_vision'...
Listing 'onboard/src/ros2_trashbot_vision/resource'...
Listing 'onboard/src/ros2_trashbot_vision/ros2_trashbot_vision'...
Listing 'onboard/src/ros2_trashbot_vision/test'...

Ran 18 tests in 1.036s
OK
```

## 改动文件和接口影响

- 实际改动文件：`sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/robot-algorithm-engineer.md`
- 代码改动：无。
- `docs/vision/` 改动：无。现有 `docs/vision/elevator_opencv_baseline.md` 已包含 `trashbot.elevator_image_manifest.v1` schema、fixture 命令、field eval gate 和 `not_proven` 边界。
- 接口影响：无公开 ROS2 / HTTP / action / message 契约变化。

## 下一轮最小采集命令和 manifest schema

下一轮应先在上位机确认 camera/odom topic 存在，再做受控采集。最小命令：

```bash
ssh root@192.168.1.11 -p 37878 '
set -eu
source /opt/ros/humble/setup.bash
test -f /root/rober/onboard/install/setup.bash && source /root/rober/onboard/install/setup.bash || true
ros2 topic list | grep -E "^/camera/image_raw$|^/odom$"
'
```

如果 `/camera/image_raw` 和 `/odom` 都存在，用固定路线 keyframe recorder 先采一组受控电梯关键帧：

```bash
ssh root@192.168.1.11 -p 37878 '
set -eu
RUN=/root/rober_runtime_material/o2_elevator_$(date +%Y%m%d_%H%M%S)
mkdir -p "$RUN"
source /opt/ros/humble/setup.bash
test -f /root/rober/onboard/install/setup.bash && source /root/rober/onboard/install/setup.bash || true
timeout 15s ros2 run ros2_trashbot_nav route_data_recorder --ros-args \
  -p camera_topic:=/camera/image_raw \
  -p odom_topic:=/odom \
  -p output_dir:=$RUN \
  -p min_distance_m:=0.0 \
  -p route_id:=o2_elevator_controlled \
  -p sample_manifest_name:=vision_samples.json \
  -p sample_manifest_max_entries:=160 || true
find "$RUN" -maxdepth 3 -type f | sort
'
```

随后人工按门开、门关、轿厢内、轿厢外、目标楼层、不可判定样本重命名/标注，生成 OpenCV eval manifest：

```json
{
  "schema": "trashbot.elevator_image_manifest.v1",
  "source": "controlled_field_material",
  "evidence_ref": "o2-elevator-controlled-YYYYMMDD-HHMM",
  "image_dir": "images",
  "samples": [
    {
      "sample_id": "door_open_inside_f3_001",
      "image": "door_open_inside_f3_001.jpg",
      "target_floor": "3",
      "expected_floor": "3",
      "expected_door_state": "open",
      "expected_inside_outside": "inside",
      "expected_safe_to_exit": "safe",
      "taxonomy_tags": [
        "door_open_positive",
        "inside_positive",
        "floor_target_positive",
        "safe_exit_positive"
      ]
    }
  ]
}
```

最低样本门槛沿用 evaluator 当前 gate：

- `door_open_positive >= 20`
- `door_closed_positive >= 20`
- `inside_positive >= 20`
- `outside_negative >= 20`
- `floor_target_positive >= 20`
- `safe_exit_positive >= 20`
- `safe_exit_negative >= 20`
- `uncertain_or_bad_light >= 10`

采集完成后运行：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_vision \
python3 -m ros2_trashbot_vision.elevator_opencv_baseline \
  /root/rober_runtime_material/o2_elevator_<run>/elevator_image_manifest.json
```

验收边界：

- `field_eval.pass=true` 才能进入 O2 OpenCV 真实/受控图片 eval 候选。
- 即使 field eval 通过，也只证明受控图片离线识别材料；仍不证明 ROS2 runtime、真实进出电梯、楼层 OCR、Nav2 安全驶出或跨楼层送达。

## 剩余风险和下一步建议

- 当前 blocker 不在算法代码，而在材料入口：没有真实/受控图片和人工标注 manifest。
- `route_data_recorder` 依赖 `/camera/image_raw` 与 `/odom`；若上位机缺任一 topic，需要 Robot Software Engineer 先补 runtime topic 或给出替代 frame capture 工具。
- JPEG/PNG 真实图片 eval 需要运行环境可用 `cv2`。当前 fixture eval 只证明 PGM/software guard。
- 建议下一轮由现场 owner 采集同一 `evidence_ref` 下的图片、目标楼层、门状态和人工协助记录，再由 Algorithm 运行 OpenCV eval，由 Robot Software 接入状态链 runtime。
