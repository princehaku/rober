# Tech Plan - Board Live Evidence Capture

## 计划状态

本轮是 Epic sprint 的设计阶段，状态为 `design_ready_for_engineer_dispatch`。当前只允许修改本 sprint 三个设计文档；不写产品代码、不改测试、不改硬件配置、不改 launch、不改 `OKR.md`。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低完成度为：

- O7：PC 端运营调试平台，约 12%。
- O6：云端核心后端，约 30%。

本 sprint **不直接针对 O7/O6 surface**，而是优先真实上位机/O3 lane。理由：

1. `OKR.md` 第 5 节已把“现场 O3 验证 lane（归档 Objective 临时激活）”列为当前最高优先级，要求优先产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
2. CEO 已再次提供真实上位机入口 `ssh root@192.168.1.11 -p 37878`，且明确要求先设计完整功能点再写代码。
3. 最近 O6/O7 sprint 已形成 preflight、manifest、consumer detail 的 local/mock software proof；继续做 surface、handoff 或 safe summary 不能解锁真实路线材料。
4. O7 的历史回放、标注、实时地图最终都依赖真实 route/map/keyframe 数据源；本轮补 O3 现场材料，实际是为 O7/O6 补上游证据链。

方向判断：**继续真实上位机/O3 lane，暂停新增 O6/O7 surface 小切片**。若 SSH 仍不通，必须产出 fallback evidence 和 CEO 决策点，不能再把同一 root cause 包装成新交付。

## 最近 blocker/root cause 复盘

已扫描最近相关 final：

- `2026.06.09_14-15_board-live-route-preflight-and-capture`：真实路线采集未完成，`192.168.1.11:37878` 路由/ARP/端口层不可达。
- `2026.06.09_15-04_board-field-evidence-preflight`：SSH 模式输出 `blocked_ssh_unreachable`，但成功交付 local/dry-run JSON preflight。
- `2026.06.09_18-19_board-evidence-to-archive-consumer`：SSH 不可达不阻断软件闭环；manifest->consumer detail mock 链路已通，但真实材料仍缺。

红线判断：如果下一阶段仍是 SSH 不通，必须视为同一 blocker 第三次触碰。后续执行必须给出可执行 fallback 或 CEO 决策点。

## 功能点完整性

本轮定义的功能点为 `board_live_evidence_capture`。完整性门槛如下：

1. **Live SSH gate**：必须明确使用 `ssh root@192.168.1.11 -p 37878`，并保存命令、退出状态、错误摘要。
2. **Board runtime gate**：SSH 成功后必须检查 hostname/date、ROS2、setup、workspace package 和关键 topic。
3. **Capture gate**：必须尝试或给出可复制命令产出 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL。
4. **Manifest gate**：必须用 `field_route_evidence_manifest.py` 对真实或 fallback artifact root 生成 `trashbot.field_evidence_manifest.v1`。
5. **Fail-closed gate**：preflight-only、mock-only、SSH blocked 或 artifact missing 必须保持 `not_proven=true`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
6. **Code-write gate**：只有既有脚本无法满足上述 gate，且失败根因已记录，才允许后续 Engineer 提议改代码。
7. **Hardware fact gate**：涉及 WAVE ROVER、ESP32、Orange Pi、UART、串口、波特率、JSON 指令、反馈协议、引脚、电压、机械尺寸时，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。

功能点不完善时禁止开写的代码范围：

- 新增 O6/O7 UI、handoff、review、safe summary。
- 改动 `delivery_success`、`safe_to_control`、`primary_actions_enabled` 语义。
- 改动硬件配置、launch 默认硬件参数或 WAVE ROVER/Orange Pi 协议。
- 未先复用既有 preflight/manifest/capture 入口而新增重复 CLI。

## 后续派工设计

### 主责任务：robot-algorithm-engineer

目标：在真实上位机路径上产出 O3 evidence，或产出分层 fallback。

允许改动（实施阶段另行派发时再开放）：

- `sprints/2026.06.09_20-21_board-live-evidence-capture/tech-done.md`
- `sprints/2026.06.09_20-21_board-live-evidence-capture/side2side_check.md`
- `sprints/2026.06.09_20-21_board-live-evidence-capture/final.md`

默认只执行既有命令，不改产品代码。

### 条件介入：robot-software-engineer

仅当 `robot-algorithm-engineer` 证明既有脚本缺口阻塞 evidence 产出时介入。允许改动范围必须在新实现任务中重新列出，优先限于：

- `onboard/scripts/board_live_route_preflight.sh`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/field_route_evidence_manifest.py`
- 对应 tests 与 `docs/navigation/` 同步文档

### 条件介入：robot-hardware-engineer

仅当失败指向硬件事实时介入，例如真实串口、WAVE ROVER、Orange Pi 设备、传感器安装、供电、电压或机械安全。介入前必须读取：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
```

并在交付说明中引用具体本地 vendor 文件。

### 暂不派发：full-stack-software-engineer

O6/O7 只有在真实材料或 manifest gate 已形成后再消费。本轮不排 UI/surface，避免继续 WIP 漂移。

## SSH live 成功路径

后续 Engineer 必须按以下顺序执行，并把关键输出写入 `tech-done.md`。

### 1. 本机工作区状态

```bash
git status --short --branch
```

### 2. 真实 SSH preflight

macOS 没有 GNU `timeout` 时可用 Perl 包裹命令，后续执行阶段优先记录两种之一：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo board_live_ssh_ok && hostname && date"
```

```bash
perl -e 'alarm 8; exec @ARGV' ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo board_live_ssh_ok && hostname && date"
```

### 3. Board runtime preflight

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 '
set -e
hostname
date
command -v ros2
find / -maxdepth 4 -name setup.bash 2>/dev/null | head -20
'
```

### 4. ROS2 workspace/package/topic smoke

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 '
set -e
source /opt/ros/humble/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
if [ -f ~/rober/onboard/install/setup.bash ]; then source ~/rober/onboard/install/setup.bash; fi
if [ -f ~/apps/rober/onboard/install/setup.bash ]; then source ~/apps/rober/onboard/install/setup.bash; fi
ros2 pkg list | egrep "ros2_trashbot_(bringup|nav|hardware|behavior)"
ros2 topic list | egrep "/scan|/camera/image_raw|/odom|/tf|/map" || true
timeout 12s ros2 topic hz /scan --window 5 || true
timeout 12s ros2 topic hz /odom --window 5 || true
timeout 12s ros2 topic hz /camera/image_raw --window 5 || true
timeout 12s ros2 topic echo /tf --once || true
'
```

### 5. Live capture

优先复用既有入口：

```bash
bash onboard/scripts/board_live_route_preflight.sh --skip-capture
```

SSH 成功且现场安全允许移动时，在上位机按时间戳目录采集：

```bash
RUN_ID="field_map_$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$HOME/.ros/trashbot_runs/${RUN_ID}"
mkdir -p "$OUT_DIR"
source /opt/ros/humble/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
if [ -f ~/rober/onboard/install/setup.bash ]; then source ~/rober/onboard/install/setup.bash; fi
ros2 launch ros2_trashbot_bringup learn.launch.py \
  route_recorder:=true \
  route_output_dir:="$OUT_DIR" \
  route_id:=trash_station_route \
  route_camera_topic:=/camera/image_raw \
  route_odom_topic:=/odom
```

另一个 SSH session 保存地图、转换路线并 dry-run：

```bash
source /opt/ros/humble/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
if [ -f ~/rober/onboard/install/setup.bash ]; then source ~/rober/onboard/install/setup.bash; fi
ros2 service list | egrep "/trashbot/save_map|map"
ros2 service call /trashbot/save_map std_srvs/srv/Trigger {}
find "$HOME/.ros/trashbot_runs" -maxdepth 4 -type f | sort | tail -120
ROUTE_CSV="$(find "$HOME/.ros/trashbot_runs" -name "*.csv" | sort | tail -1)"
ROUTE_YAML="${ROUTE_CSV%.csv}.yaml"
ros2 run ros2_trashbot_nav route_csv_to_yaml "$ROUTE_CSV" "$ROUTE_YAML"
ros2 run ros2_trashbot_nav fixed_route_autonomy --ros-args -p route_file:="$ROUTE_YAML" -p dry_run:=true
```

可选 rosbag：

```bash
timeout 30s ros2 bag record -o "$OUT_DIR/rosbag_minimal" /scan /odom /tf /camera/image_raw
```

## SSH 不通时的降级产物

若 SSH 失败，后续 Engineer 必须产出以下文件或输出片段：

1. SSH 命令、退出码、stderr 摘要。
2. `field_route_evidence_preflight.py` SSH 模式 JSON，状态应标记 `blocked_ssh_unreachable` 或更具体状态。
3. local/dry-run preflight JSON，证明工具链仍可复跑。
4. manifest local fixture JSON，证明 artifact gate 可消费材料目录。
5. CEO 决策点：确认上位机在线、局域网、端口、SSH 服务、host/port 是否需要更新，或是否由现场人工导出材料。

命令：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --dry-run \
  --output /tmp/trashbot_field_preflight_local.json
python3 -m json.tool /tmp/trashbot_field_preflight_local.json >/tmp/trashbot_field_preflight_local.pretty.json
```

```bash
rm -rf /tmp/trashbot_field_manifest_fixture_complete
mkdir -p /tmp/trashbot_field_manifest_fixture_complete/keyframes /tmp/trashbot_field_manifest_fixture_complete/route_bag
printf 'image: map.pgm\nresolution: 0.05\n' >/tmp/trashbot_field_manifest_fixture_complete/map.yaml
printf 'x,y,yaw\n0,0,0\n1,0,0\n' >/tmp/trashbot_field_manifest_fixture_complete/route.csv
printf '{"x":0,"y":0}\n' >/tmp/trashbot_field_manifest_fixture_complete/keyframes/0001.json
printf 'rosbag2_bagfile_information:\n' >/tmp/trashbot_field_manifest_fixture_complete/route_bag/metadata.yaml
printf '{"t":0,"x":0,"y":0,"yaw":0,"state":"dry_run_fixture"}\n' >/tmp/trashbot_field_manifest_fixture_complete/replay.jsonl
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_local.json \
  --output /tmp/trashbot_field_manifest_complete.json
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json >/tmp/trashbot_field_manifest_complete.pretty.json
```

## 后续子 agent 验收命令

后续执行阶段必须把以下命令原样或按现场路径等价运行，并在 `tech-done.md` 写关键输出。

### 真实 SSH preflight

```bash
git status --short --branch
ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo board_live_ssh_ok && hostname && date"
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
```

### Board evidence CLI

```bash
bash -n onboard/scripts/board_live_route_preflight.sh
bash onboard/scripts/board_live_route_preflight.sh --help
bash onboard/scripts/board_live_route_preflight.sh --dry-run --local-only
bash onboard/scripts/board_live_route_preflight.sh --skip-capture
```

### Manifest

```bash
python3 onboard/scripts/field_route_evidence_manifest.py --help
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json || true
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json >/tmp/trashbot_field_manifest_complete.pretty.json || true
```

### 单元测试

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/scripts/field_route_evidence_preflight.py \
  onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/tests/test_field_route_evidence_preflight.py \
  onboard/tests/test_field_route_evidence_manifest.py
```

### 文档检查

```bash
rg -n "board_live_evidence_capture|功能点完整性|ssh root@192.168.1.11 -p 37878|map.yaml|route.csv|keyframe|rosbag|replay JSONL|blocked_ssh_unreachable|CEO 决策点" \
  sprints/2026.06.09_20-21_board-live-evidence-capture
```

### git diff check

```bash
git diff --check -- \
  sprints/2026.06.09_20-21_board-live-evidence-capture \
  onboard/scripts/board_live_route_preflight.sh \
  onboard/scripts/field_route_evidence_preflight.py \
  onboard/scripts/field_route_evidence_manifest.py \
  onboard/tests/test_field_route_evidence_preflight.py \
  onboard/tests/test_field_route_evidence_manifest.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/field_route_evidence_manifest.md
git status --short --branch
```

## 成功退出条件

成功收口必须满足以下二选一。

路径 A：live 成功。

- SSH 登录成功。
- ROS2/package/topic 至少完成 smoke。
- 产出 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL 中至少一种真实材料。
- manifest gate 写明 artifact 状态。
- 明确 `delivery_success=false`，除非另有真实送达任务证据。

路径 B：live 失败但 fallback 合格。

- SSH 失败被分层记录。
- preflight SSH JSON、local JSON、manifest fixture JSON 均可复跑。
- 给 CEO 一个具体决策点，不再只写 `blocked_ssh_unreachable`。
- 后续不新增 O6/O7 surface，直到 live 材料或 CEO 改变方向。

## 风险与剩余阻塞

- `192.168.1.11:37878` 仍可能不可达；这是最大风险。
- macOS 默认缺少 GNU `timeout`，本机命令需用 Perl 或 Python 包裹，远端 ROS2 命令可继续用上位机 Linux `timeout`。
- 本设计不证明真实 SSH、ROS2 topic 或材料已存在；只完成设计 gate。
- 本设计不改 `OKR.md`，完成度不得因此上调。

## 需要创建或更新的 sprint 文档

本轮已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续执行完成后必须新增：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
