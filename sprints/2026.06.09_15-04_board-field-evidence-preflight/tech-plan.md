# Board Field Evidence Preflight Sprint Tech Plan

## 责任 Engineer

派发给：`robot-algorithm-engineer`。

理由：本轮功能服务 SLAM、Nav2、固定路线、topic smoke、route evidence packet 和下一次现场路线采集。单 owner 闭环，避免假并行。

## 允许改动文件范围

允许改动：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/tech-done.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/side2side_check.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`

不得改动：

- WAVE ROVER、ESP32、UART、串口、底盘协议、launch 默认硬件参数。
- `OKR.md` 进度百分比，除非 Product Owner 单独要求。
- 无关 PC/mobile/cloud surface。

## 接口设计

CLI：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local|ssh \
  [--dry-run] \
  [--ssh-target root@192.168.1.11] \
  [--ssh-port 37878] \
  [--timeout-s 8] \
  --output <path>
```

输出 schema：`trashbot.board_field_evidence_preflight.v1`。

`--dry-run` 必须不执行 SSH、不要求 ROS2、不要求 topic 存在，只生成命令模板、路径模板和 `dry_run_template_only_not_proven` 状态。

真实模式可以执行只读命令：

- `hostname`
- `date`
- `command -v ros2`
- `find` setup.bash 候选
- `ros2 pkg list`
- `ros2 topic list`
- bounded `timeout` topic smoke

禁止真实移动、禁止发布 `/cmd_vel`、禁止保存凭证。

## 实现要点

1. 使用 Python 标准库：`argparse`、`json`、`subprocess`、`datetime`、`platform`、`pathlib`。
2. 所有外部命令必须有 timeout，并记录 return code、stdout/stderr 的安全摘要。
3. SSH 命令必须通过参数数组构造，避免 shell 拼接。
4. JSON 输出必须稳定排序，便于进入云端 archive 或 PC 端消费。
5. 代码技术注释必须使用中文，并解释为什么要 fail closed、为什么 dry-run 不能声称真实通过。

## Vendor 资料边界

本轮默认不涉及 WAVE ROVER UART、baudrate、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸。

如果 Engineer 扩展到硬件参数或串口 smoke，必须先读取：

```bash
sed -n '1,180p' docs/vendor/VENDOR_INDEX.md
```

并在代码注释或 `tech-done.md` 引用实际采用的 vendor 文件。本轮设计不允许扩大到串口控制。

## 验收命令

实现前确认工作区：

```bash
git status --short
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
```

单元测试：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
```

dry-run 证据：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_field_preflight.json
python3 -m json.tool /tmp/trashbot_field_preflight.json >/tmp/trashbot_field_preflight.pretty.json
```

收尾状态：

```bash
git status --short
```

Engineer 必须在 `tech-done.md` 粘贴关键输出摘要，并在验证通过后提交、推送：

```bash
git add onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md sprints/2026.06.09_15-04_board-field-evidence-preflight
git commit -m "Add board field evidence preflight CLI"
git push
```

## OKR 最低优先级核对

`OKR.md` 4.1 当前数字最低的是 O7（约 12%），其次是 O6（约 30%）。本 sprint 直接服务 O3 现场验证 lane，同时为 O7 历史路线回放和 O6 evidence archive 准备标准证据入口。

不直接做 O7 PC UI 的理由：上一轮真实 route/map/keyframe 材料仍缺失；继续做 PC surface 会违反 WIP 限制。本轮先补下一次现场材料采集的标准入口，避免 O7 后续继续依赖 fixture。

## 成功标准

成功完成至少需要：

- 新 CLI dry-run 输出合法 JSON。
- 单元测试通过。
- JSON 明确 `not_proven=true`、`delivery_success=false`、`primary_actions_enabled=false`。
- JSON 包含下一次真实上位机采集 map、route、keyframe、rosbag、replay 的命令模板。
- 文档说明真实 SSH 恢复后如何使用。
- sprint 收口文档记录验证结果、未完成事项和风险。

## 风险

- 当前运行时子 agent 工具若不可用，主节点不能越权实现产品代码。
- 真实 SSH 仍可能不可达；本工具只能让下一次失败更快定位，不能替代网络修复。
- macOS 本地没有 ROS2 时只能验证 dry-run 和 JSON contract；真实 topic smoke 仍要等上位机或 Docker/Humble。

