# Tech Plan

## 元数据

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- 主责/集成/live owner：`robot-software-engineer`
- 并行独立 owner：`robot-algorithm-engineer`
- 条件 owner：`rober-hardware-engineer`（Phase B execute=`1` 后）
- authorization：`ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`
- 目标：实现、测试、部署 `sensor-enabled/base-disabled` lifecycle 与 O10 localization/readiness 修复；只在九门全绿后执行一次 bounded mission。

## OKR 最低优先级核对

`OKR.md` 当前最低 Objective 是 O5（约 `85%`）。O5 provider/runtime blocker 已连续消费 `2/2` 并明确暂停，本 sprint 不再开 provider、preflight、tunnel、readback 或 wrapper。CEO 给出新的 bounded mission fresh authorization，且上一轮已关闭 deadline/transport，因此本 sprint 转向可行动的 O3/O1 current Nav2 readiness repair + bounded mission；O6/O7 各约 `93%`、O1 约 `94%`，planning 阶段全部 flat。

## 执行拓扑与接口边界

```text
Robot offline Upper/O11 repair ----\
                                   -> Robot integrated tests/build -> deploy -> Phase A once
Algorithm offline O10 gate repair -/                                      |
                                                                           +-- NO-GO -> owned cleanup
                                                                           +-- 9/9 GO -> Phase B once -> Hardware frozen review
```

- 两个实现 owner 可并行，因为源码、测试、文档与 artifact 目录不重叠；Robot 在合并后承担统一回归、Docker build、部署、live 调用与 `tech-done.md`。
- 若任何共享文件必须双写，立即停止并收敛为 Robot 单主责；Algorithm 改为只读 frozen artifact review，不得并行修改。
- Product 不写产品代码/测试、不运行 live；只在 Engineer 留档后做验收和 OKR closeout。

## 文件范围与 owner

### Robot Software（可写）

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/tests/test_upper_robot_api.py`
- `onboard/tests/test_o11_nav2_lifecycle_script.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission/artifacts/robot-software/`
- `sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission/tech-done.md`

Robot 不得修改 Algorithm 范围、WAVE ROVER firmware/vendor 文件、手机/云代码、`OKR.md`、progress log、`side2side_check.md` 或 `final.md`。

### Algorithm（可写且不得与 Robot 重叠）

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`
- `onboard/tests/test_nav2_params_contract.py`
- `docs/navigation/same_window_route_readiness_precheck.md`
- `sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission/artifacts/algorithm/`

Algorithm 不得改 Upper/O11、live orchestration、Robot artifact 或 `tech-done.md`；若无需 params 变更则保持不动，不为制造 diff 而修改。

### Hardware（Phase B execute=`1` 后才可写）

- `sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission/artifacts/hardware/`

Hardware 不改产品代码、配置或 vendor 文件；只消费 Robot 已冻结的本 run Phase B raw/manifest，输出 `T=1001`/HIL review。Robot 汇总其事实到 `tech-done.md`。

## Upper/O11 sensor-enabled/base-disabled 合同

`/api/nav2/start` 的五字段 body 保持 exact-field 校验，但新增安全组合：

```json
{
  "strict_no_motion": true,
  "base_enabled": false,
  "lidar_enabled": true,
  "reuse_existing_scan": false,
  "timeout_s": 20
}
```

- 只接受两种明确模式：既有 legacy no-new-open `false/false/true`，以及本轮 sensor-owned `false/true/false`；拒绝 `base_enabled=true`、`auto`、`true/true`、`lidar=false/reuse=false` 和 `lidar=true/reuse=true`。
- 本轮 frozen request 必须使用 sensor-owned 模式。O11 start 前确认 base UART 未被本轮打开、LiDAR port 可用、无非 owned `/scan` publisher/holder、canonical map 文件存在、初始 owned lifecycle stopped。
- O11 launch 保持 `nav2_stack_only:=true`、`base_enabled:=false`、`lidar_enabled:=true`；status 增加 sensor ownership、publisher/port pre/post、map identity 与 base UART zero-open 事实。
- Upper semantic success 必须同时依赖 command ok、lifecycle running、effective base=false/lidar=true、owned LiDAR holder、current `/scan` publisher 和 base UART new-open=`0`；HTTP `200` 不是成功。
- start 失败只调用 O11 owned cleanup；stop 只终止 PID 文件归属的 process group，不发 base stop、不访问 UART、不 broad kill。

## O10 current readiness 修复

Phase A proof body 必须冻结 `managed_runtime_opt_in=true`、canonical `managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`、`initialpose_opt_in=true`、canonical free-cell opt-in、`path_generation_opt_in=true` 和固定 goal。`managed_runtime_opt_in=true` 在本轮表示验证并复用同一 O11-owned runtime；不得再启动第二套 LiDAR/Nav2 runtime。

O10 natural-final 必须显式产生以下九门与原始依据：

1. `map_ready`：map_server active；YAML/image hash、metadata 与 current `/map` canonical proof clean。
2. `amcl_ready`：AMCL active，current scan subscription/pose processing成立。
3. `planner_ready`：planner_server active 且 planner action/service ready。
4. `controller_ready`：controller_server active 且 controller action/service ready；Phase A 不调用控制 action。
5. `current_pose_ready`：`/amcl_pose` stamp parsed、receipt/age fresh、frame/covariance valid。
6. `persisted_pose_ready`：persisted pose 绑定 canonical map，timestamp fresh，并被本 runtime live consumed；pre/post audit 不冲突。
7. `dynamic_tf_ready`：fresh dynamic `map->odom` 唯一归因 AMCL，同一时点 `map->base_link` 可解析；禁止 static/fake/历史替代。
8. `planner_only_path_ready`：fixed goal materialized，ComputePathToPose attempted/succeeded/generated，point_count>0、frame/time fresh；不得发送 NavigateToPose/FollowPath。
9. `obstacle_clear`：使用同一 current `/scan` 的 stamp/receipt/finite points/min range/threshold；stale、空、NaN/Inf fail closed。

`/initialpose` 最多一次且 no retry；只有 canonical map hash/free-cell audit clean 才允许。任何 clock basis 不一致、publisher 多义、TF attribution ambiguous、pose conflict、path fallback 或 scan stale 都写具体 blocker 并 `READINESS_GO=false`。

## 离线验收与工程质量

Robot 与 Algorithm 分别在自己的范围实现、修复并重跑；Robot 最后跑集成：

```bash
set -euo pipefail
bash -n onboard/scripts/o11_nav2_lifecycle.sh
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_o11_nav2_lifecycle_script.py
python3 -m unittest onboard/tests/test_upper_robot_api.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m unittest onboard/tests/test_nav2_params_contract.py
python3 -m unittest onboard/tests/test_o11_nav2_lifecycle_script.py onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py onboard/tests/test_nav2_params_contract.py
bash onboard/scripts/docker_humble_build.sh
git diff --check
```

- 新增/修改技术注释必须全部中文；每个 owner 在 `tech-done.md` 报告修改代码的中文注释行、代码行与比例，比例严格 `>20%`。
- Robot tests 必须覆盖两种合法 start 组合、所有非法布尔组合、base UART zero-open、owned LiDAR open/publisher、semantic failure cleanup。
- Algorithm tests 必须覆盖 canonical map mismatch、scan stale/no publisher/multi publisher、pose timestamp/freshness、persisted conflict、TF static/ambiguous/stale、planner/controller inactive、path failure、obstacle threshold与 9/9 GO fixture。
- 任何失败必须定位、在 owner 范围修复并重跑 targeted + full；不得把第一轮失败直接交差。

## 部署与 Phase 0

只有离线与 Docker 全绿后，Robot 才能使用授权目标部署。部署文件限 Upper、O11、O10 和实际改动的 Nav2 params；先传临时文件、remote py_compile/bash syntax/内容 SHA 通过后原子替换，再 restart Upper service。禁止部署未验证文件或整仓覆盖。

Phase 0 必须落盘：local/remote SHA、remote py_compile/bash syntax、service active/MainPID、`/api/health`、`/api/status`、`/api/nav2/status`、初始 stopped/PID null/owned residual=`0`、base UART holder delta=`0`、LiDAR holder/publisher pre-state。任一失败时 Phase A counts=`0/0/0/0`，授权未消费。

## Frozen request 与 exactly-once Phase A

所有 body 先写入本 sprint `artifacts/robot-software/frozen_requests.json`，通过 `python3 -m json.tool`、`jq -e`、SHA/bytes/lines 后，固定使用 `jq -c | ssh ... curl --data-binary @-`。禁止 inline JSON、heredoc 拼 body、远端变量拼 JSON或现场改 key。

```bash
set -euo pipefail
SPRINT=sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission
REQ="$SPRINT/artifacts/robot-software/frozen_requests.json"
python3 -m json.tool "$REQ" >/dev/null
jq -c '.phase_a_start' "$REQ" | ssh -p 37878 root@192.168.1.11 \
  "curl -sS -X POST -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:8787/api/nav2/start"
jq -c '.phase_a_proof' "$REQ" | ssh -p 37878 root@192.168.1.11 \
  "curl -sS -X POST -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:8787/api/nav2/proof/refresh"
ssh -p 37878 root@192.168.1.11 'curl -sS http://127.0.0.1:8787/api/nav2/proof/latest'
jq -c '.phase_a_owned_stop' "$REQ" | ssh -p 37878 root@192.168.1.11 \
  "curl -sS -X POST -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:8787/api/nav2/stop"
```

- start pipe 创建即消费 v5 authorization；不论结果，start/proof/latest/owned-stop 各至多一次、no-retry。
- proof 必须自然形成 `artifact_kind=final`、`last_phase=final`、`current_command=null`、partial=false；latest 与 proof nested latest 的 canonical SHA/timestamp/lineage 相同。
- owned-stop 必须在 readiness decision 前后都保留 raw/receipt；decision 只能由冻结 natural-final 得出，不能 stop 后补采再洗白。
- Phase A 计数固定 `1/1/1/1`、retry=`0`；九门任一不绿则 Phase B `0/0/0`、final state=`NO_GO_CLEAN`。

## Phase B 准入、bounded mission 与 cleanup

Phase B 还必须在 goal 前只读确认 operator present、路线仍清空、物理限制仍有效、emergency stop ready、scan/pose/TF/path/obstacle freshness 未过期。该 readback 不得重跑 Phase A 或补发 `/initialpose`。

准入后由 Robot 严格串行：

1. POST `/api/base/stop` exactly once，必须有停止 semantic/feedback；失败则 execute=`0`。
2. POST `/api/nav2/goal/execute` exactly once，使用冻结 fixed goal/authorization/run/action/task/route；发送即 `execute_attempt_count=1`，永不 retry。
3. 不论 terminal success/fail/timeout/unknown，都 POST `/api/base/stop` exactly once 作为 post-stop，并执行一次 owned Nav2 cleanup。
4. 只读 GET terminal、feedback、status 各一次，冻结 current raw、transport receipt、counts 与 lineage。
5. cleanup 验证 lifecycle stopped、PID null、PID files=`0`、owned residual=`0`、broad kill=false；不满足则 `STOPPED_UNCLEAN_NEEDS_CEO`。

Phase B count 只有两种合法形态：NO-GO `0/0/0`，或 GO 后 pre-stop/execute/post-stop=`1/1/1`；goal retry 始终 `0`。Phase B 前必须 `physical_motion=false`，任何意外 motion/base UART open 立即进入安全收口。

## Hardware T=1001/HIL 条件复核

只有 Robot manifest 证明 Phase B `execute_attempt_count=1` 后才派 Hardware。Hardware 必须按顺序读取：

1. `docs/vendor/VENDOR_INDEX.md`
2. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
3. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
4. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
5. `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

随后只读审核本 run feedback：`T=1001` schema/数量、L/R motion-window 非零与方向、post-stop L/R 归零、r/p/y/v 字段、operator observed motion/stop、pre/post base stop、terminal lineage。无 current sample、invalid JSON、跨 run、方向不明、post-stop 未归零或 operator 未确认均固定 `hil_pass=false`、`safe_to_control=false`。Hardware 不补发 feedback request、goal、manual、UART 或 retry。

## Artifact 与最终验收合同

- Robot：frozen identity/requests、deployment manifest、Phase A/B invocation manifest、全部 raw/receipt、readiness decision、attempt counts、cleanup、terminal/status/feedback。
- Algorithm：current natural-final gate review，逐门列 raw basis、freshness、conflict 与 accepted/rejected claims。
- Hardware：仅 Phase B execute=1 后的 vendor source list、current `T=1001`/HIL review；execute=0 时 artifact count 必须为 0。
- 所有 JSON 运行 `python3 -m json.tool`，所有 lineage/count/safety invariant 用 `jq -e`；scoped anchors 用 `rg`；最终运行 `git diff --check`。
- `tech-done.md` 必须记录实际改动、命令输出、失败定位/修复、live counts、cleanup、中文注释比例、docs 同步、剩余风险。
- Product closeout 才能创建 `side2side_check.md`、`final.md` 并更新 `OKR.md`/progress log；没有 route/HIL/delivery direct evidence 时百分比 flat、KR `不归档`。

## 停止条件与剩余风险

- pre-existing holder、canonical map mismatch、base UART open、non-owned process、test/build/deploy SHA/service failure：Phase A 不执行。
- start 后任一 transport/semantic/readiness failure：no retry，owned cleanup，Phase B=0。
- execute 后任何 unknown：仍完成一次 post-stop 与 owned cleanup，不重发 goal。
- 最大技术风险是 base-disabled 阶段缺少可信 `odom->base_link`；禁止用 static/fake TF 冒充。若现场无法产生 current dynamic chain，本 sprint诚实 `NO_GO_CLEAN`，不得再开 readiness-only wrapper。
- route terminal 不等于 delivery；current `T=1001`/HIL 不等于长期 safe-to-control。Product 必须分别保留证据边界。
