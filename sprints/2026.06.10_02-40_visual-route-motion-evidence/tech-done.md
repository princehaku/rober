# Visual Route Motion Evidence Micro Sprint

- sprint_type: micro
- owner: robot-algorithm-engineer
- time: 2026-06-10 02:40 Asia/Shanghai
- safe_to_control=false
- delivery_success=false
- not_proven=true

## 自主能力目标和本轮抓手

目标是消费上一轮真实上车采集素材，生成可复核的视觉运动证据包：

- 量化 `keyframes/` 相邻关键帧是否存在图像变化。
- 量化 `route.csv` 是否存在连续 odom 位移。
- 明确证据边界：验收人工视觉检查发现 `keyframe_contact_sheet.jpg` 与抽样原始帧几乎全黑，因此本轮只能证明 camera image 关键帧文件存在、存在微小像素/哈希变化、`command-integration` route odom 存在位移；不证明可用视觉路线内容、环境结构、encoder wheel speed、真实 Nav2 完成、垃圾收集送达闭环完成。

资料来源：

- 上一轮真实采集 sprint：`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/route.csv`
- 上一轮真实采集关键帧：`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/keyframes/`
- 上一轮路线 manifest：`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/manifest.json`
- 上一轮地图目录：`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/`
- 硬件事实边界：`docs/vendor/VENDOR_INDEX.md`。采用事实为 Orange Pi Zero 3 + WAVE ROVER + ESP32，下上位机链路为 UART newline-delimited UTF-8 JSON；vendor Raspberry Pi 默认 UART 为 `/dev/ttyAMA0` at `115200`，Orange Pi 实际设备名必须上车确认。本轮不新增串口、引脚、电压或底盘控制假设。

## 实际改动

新增文件：

- `sprints/2026.06.10_02-40_visual-route-motion-evidence/scripts/analyze_visual_route.py`
- `sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_summary.json`
- `sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/keyframe_diff_summary.csv`
- `sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/keyframe_contact_sheet.jpg`
- `sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_analysis.log`
- `sprints/2026.06.10_02-40_visual-route-motion-evidence/tech-done.md`

未修改产品代码、launch、驱动、测试或其它 sprint 目录。

## 接口影响

无 ROS2 接口影响。没有改动消息、action、launch 参数、硬件桥、Nav2 配置或行为状态机。

## 实现内容

- 使用一次性 Python 分析脚本读取上一轮 `route.csv`、`manifest.json` 和关键帧 JPEG。
- 因当前 macOS 环境没有 Pillow/OpenCV，脚本调用 `/usr/bin/sips` 将 JPEG 临时转为 BMP，再用 Python 标准库解析 BMP 做逐像素差分。
- 输出 `keyframe_diff_summary.csv`，包含相邻关键帧 SHA256 前缀、是否完全一致、mean absdiff、RMS diff、变化像素比例。
- 输出 `visual_motion_summary.json`，包含关键帧数量、相邻非同一 pair 数、route 行数、累计路径、端点位移、正位移 segment 数和边界 flag。
- 输出 `keyframe_contact_sheet.jpg`，用于人工快速复核 16 张关键帧序列；验收后确认该图可打开但画面几乎全黑。
- 输出 `visual_motion_analysis.log`，记录分析输入、解码器和核心结果。

## 验证结果

一次性分析命令：

```bash
python3 sprints/2026.06.10_02-40_visual-route-motion-evidence/scripts/analyze_visual_route.py
```

关键输出：

```text
source_route=/Users/m1/apps/rober/sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/route.csv
source_keyframes=/Users/m1/apps/rober/sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/keyframes
source_manifest=/Users/m1/apps/rober/sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/manifest.json
decoder=/usr/bin/sips
keyframe_count=16
non_identical_adjacent_pairs=6
visual_mean_absdiff_avg=0.179165
route_row_count=17
route_total_displacement_m=0.167998084
route_positive_segment_count=16
safe_to_control=false delivery_success=false not_proven=true
```

JSON 格式检查：

```bash
python3 -m json.tool sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_summary.json >/tmp/visual_motion_summary.check
```

关键输出：

```text
4288 /tmp/visual_motion_summary.check
{
    "schema": "trashbot.visual_route_motion_evidence.v1",
    "sprint": "2026.06.10_02-40_visual-route-motion-evidence",
    "source_sprint": "sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf",
```

summary 自检：

```bash
python3 - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path('sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_summary.json').read_text(encoding='utf-8'))
assert summary['keyframe_count'] >= 2, summary['keyframe_count']
assert summary['non_identical_adjacent_pairs'] >= 1, summary['non_identical_adjacent_pairs']
assert summary['route_row_count'] >= 2, summary['route_row_count']
assert summary['route_total_displacement_m'] > 0, summary['route_total_displacement_m']
assert summary['manual_visual_review']['contact_sheet_appears_mostly_dark'] is True
assert '不能证明可用视觉内容' in summary['manual_visual_review']['claim_boundary']
print('keyframe_count=', summary['keyframe_count'])
print('non_identical_adjacent_pairs=', summary['non_identical_adjacent_pairs'])
print('route_row_count=', summary['route_row_count'])
print('route_total_displacement_m=', f"{summary['route_total_displacement_m']:.9f}")
print('route_positive_segment_count=', summary['route_positive_segment_count'])
print('contact_sheet_appears_mostly_dark=', summary['manual_visual_review']['contact_sheet_appears_mostly_dark'])
print('claim_boundary=', summary['manual_visual_review']['claim_boundary'])
print('safe_to_control=', summary['boundary_flags']['safe_to_control'])
print('delivery_success=', summary['boundary_flags']['delivery_success'])
print('not_proven=', summary['boundary_flags']['not_proven'])
PY
```

关键输出：

```text
keyframe_count= 16
non_identical_adjacent_pairs= 6
route_row_count= 17
route_total_displacement_m= 0.167998084
route_positive_segment_count= 16
contact_sheet_appears_mostly_dark= True
claim_boundary= 只能证明 camera image 文件存在且有微小像素/哈希变化，不能证明可用视觉内容/环境结构。
safe_to_control= False
delivery_success= False
not_proven= True
```

文件清单：

```text
sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/keyframe_contact_sheet.jpg
sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/keyframe_diff_summary.csv
sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_analysis.log
sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts/visual_motion_summary.json
sprints/2026.06.10_02-40_visual-route-motion-evidence/scripts/analyze_visual_route.py
```

`git status --short` 当时输出：

```text
?? sprints/2026.06.10_02-40_visual-route-motion-evidence/
```

## 数据、样本或调试输出变化

- 关键帧：`keyframe_count=16`，相邻 pair 共 15 组。
- 图像变化：`non_identical_adjacent_pairs=6`，平均 `mean_absdiff=0.179165`，最大 `mean_absdiff=0.452418`。验收人工视觉检查发现 `keyframe_contact_sheet.jpg`、原始 `001.jpg` 与 `011.jpg` 肉眼几乎全黑，因此该结论必须降级为 camera image 文件存在且有微小像素/哈希变化，不能称为可用视觉路线内容，也不能说明环境结构可被复核。
- route odom：`route_row_count=17`，`route_positive_segment_count=16`，`route_total_displacement_m=0.167998084`，`route_total_path_m=0.167998084`。
- route 时间：总时长约 179.15s，active route 段约 5.25s；首行到第一张关键帧之间存在约 173.90s 间隔，因此路线分析以位移存在为证据，不把总时长解释为连续实跑时长。

## 剩余风险

- safe_to_control=false：本轮没有执行控制命令，也没有验证可安全自主运行。
- delivery_success=false：本轮没有验证垃圾投递、到站、返回或用户任务闭环。
- not_proven=true：本轮不证明 encoder wheel speed、真实底盘反馈里程计、真实 Nav2 完成、避障成功、电梯场景完成或垃圾收集送达闭环完成。
- 图像差异幅度较小，只有 6/15 相邻 pair 文件非同一；contact sheet 可打开但画面几乎全黑，应仅作为 camera topic/关键帧文件存在和微小像素/哈希变化证据，不应作为可用视觉路线内容、视觉定位鲁棒性、环境结构或语义检测能力证据。
- route 位移来自上一轮 command-integration odom/TF 证据，仍需 encoder/底盘反馈来源接入后复核 wheel speed 与实际运动一致性。

## 下一步能力建设建议

- 下一轮优先把这一份 keyframe + route 证据接到固定路线 replay 或 PC 历史路线回放，避免只停留在离线摘要。
- 上车阶段补 encoder/WAVE ROVER feedback 对照：同一段 route 同时记录 `/odom`、底盘反馈、`/tf` 和相机帧，验证 command-integration 与实际轮速/位移的一致性。
- 若要推进 Nav2 完成度，需要输出 Nav2 goal/result log、costmap/TF/scan 证据和失败原因，而不是只复用本轮 route.csv。
