# Tech Plan: O10 Delivery Readiness Path Contract Epic

## sprint_type

sprint_type: epic

## 技术方案

P0 只做一条可验证路径：锁定 map lifecycle proof latest JSON 的 canonical runtime root。08-09 证明 upper API service cwd 会让相对路径落到 `/root/rober/runtime`，而 helper/map artifact 语义又以 `/root/rober/onboard` 为 workdir。本轮需要让 API/readback/helper 明确同一口径，并暴露兼容边界，避免 PC 或 Product 再猜路径。

建议实现方式由 Robot Software Engineer 在代码中确认后决定，但必须满足：

- 相对 `runtime/*` 路径按 onboard workdir 或显式 configured root 解析，不再受 upper API process cwd 漂移影响。
- 回包中能看见 `canonical_path` / `resolved_path` / `configured_path` / `compatibility_paths` 等可审计字段。
- 如果需要兼容旧 `/root/rober/runtime/map_lifecycle_latest.json`，只能作为 fallback/readback compatibility，不能继续作为唯一事实来源。
- no-motion 安全字段保持 false。

## Owner 任务

### Robot Software Engineer

文件范围：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o3_map_lifecycle_proof.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/navigation/nav2_map_quality_metrics.md`
- `sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-software-engineer.md`

验收命令：

```bash
python3 -m unittest onboard/scripts/test_upper_robot_api.py
python3 -m unittest onboard/scripts/test_o3_map_lifecycle_proof.py
python3 -m compileall -q onboard/scripts onboard/src
ssh root@192.168.1.11 -p 37878 'bash -lc "set -e; cd /root/rober; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; curl -fsS -X POST http://127.0.0.1:8787/api/map/proof/refresh; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest; echo; find /root/rober/onboard/runtime /root/rober/runtime -maxdepth 2 -name map_lifecycle_latest.json -o -name trashbot_map.yaml -o -name trashbot_map.pgm 2>/dev/null | sort"'
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py onboard/scripts/test_upper_robot_api.py docs/navigation/nav2_map_quality_metrics.md sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-software-engineer.md
```

输出要求：

- 写清实际 canonical path 和旧路径是否仍存在。
- 写清远端 8787 是否需要重启/部署；如果无法部署，不得把本地护栏写成 `robot_runtime_material`。
- 写清是否发布 `/cmd_vel` 或触碰底盘，预期必须为否。

### Full-stack Software Engineer

文件范围：

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/full-stack-software-engineer.md`

验收命令：

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm test -- --run test/App.test.ts
cd pc-tools/workstation && TMPDIR=/tmp npm run build
cd pc-tools/workstation && TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

如果启动 8788，由 agent 自己 curl：

```bash
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/status
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
```

输出要求：

- 只改必要 PC 消费/显示契约。
- 如果没有浏览器截图或按钮点击证据，只能写 API/workflow software guard。

### Robot Algorithm Engineer

文件范围：

- `docs/navigation/nav2_map_quality_metrics.md`
- `docs/vision/elevator_opencv_baseline.md`
- `sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-algorithm-engineer.md`

验收命令：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.map_quality_metrics pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/map.yaml --waypoints pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/waypoints.json || test $? -eq 1
python3 -m unittest onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py
git diff --check -- docs/navigation/nav2_map_quality_metrics.md docs/vision/elevator_opencv_baseline.md sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-algorithm-engineer.md
```

输出要求：

- 只判断本轮能否从 path contract 进入 AMCL/Nav2 readiness 或电梯 image eval。
- 无真实/受控图片时必须写 `blocked_with_root_cause`，不得补 fixture 冒充 field material。

### Hardware Infra Engineer

文件范围：

- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`
- `sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-hardware-engineer.md`

验收命令：

```bash
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
git diff --check -- docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.05_12-13_o10-delivery-readiness-path-contract-epic/owner_notes/robot-hardware-engineer.md
```

输出要求：

- 说明本轮 map proof/path contract 是否触碰 WAVE ROVER、UART、`T=1/T=130/T=1001`。
- 若没有现场看护、净空、急停/断电和 CEO/现场授权，必须写 stop-first HIL blocker。

## OKR 最低优先级核对

当前最低完成度 Objective 是 O10：0%。本 sprint 直接针对 O10 的 P0 Path Contract Lock，并把 O3/O7/O9 的已获材料串入 readiness chain 前置条件。O8 低于产品 Objective，但本轮只把 Epic 执行纪律作为护栏，不以治理替代功能推进。

## 风险边界

- 如果远端 8787 未部署新代码，本轮最多算 `software_guard`，不能算 `robot_runtime_material`。
- 如果 SSH 不通或上位机 ROS2 runtime 未启动，必须写明 root cause，不得改写为完成。
- 即使 map proof 成功，也不证明 continuous radar、AMCL、Nav2、PC WASD、HIL 或 delivery success。
