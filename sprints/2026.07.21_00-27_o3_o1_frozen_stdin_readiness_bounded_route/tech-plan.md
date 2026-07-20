# Tech Plan

- sprint_type: epic
- 状态：planning
- 主责：`robot-software-engineer`

## 执行门

Phase A 仅执行 start/proof/latest/owned-stop exactly once，no retry。只有 same-current natural final 的 map/amcl/planner/controller、current/persisted pose、dynamic TF、planner-only path、obstacle clear 全绿且 `READINESS_GO=true`，才进入 Phase B；否则 NO-GO、owned cleanup 并封存。

## OKR 最低优先级核对

最低 Objective 为 O5（约 85%），但 provider/runtime 已 2/2 且暂停；本 sprint 转向可行动的 O3/O1 frozen stdin readiness 与 bounded route，避免继续消费同一 blocker。

## 传输合同

本地用 `jq -c` 做 JSON 提取、parse/hash/count，仅 stdin pipe 给远端 curl，禁止 inline JSON。

## Owner 与串行依赖

- 单线 owner：`robot-software-engineer`，负责实现、离线验证、一次现场 Phase A、条件式 Phase B、清理和 `tech-done.md` 留档。
- `robot-algorithm-engineer` 不并行改代码；仅当 Phase A 形成 same-current natural final 后，条件只读复核 map、AMCL、planner、controller、pose、TF、path 与 obstacle gate。
- `rober-hardware-engineer` 不并行改代码；仅当 Phase B 被 `READINESS_GO=true` 解锁或出现 `T=1001` 时，条件只读复核底盘反馈和停止边界。
- `full-stack-software-engineer` 本轮不派发；本 sprint 不涉及手机/Web/API 用户触点。
- 串行依赖固定为：离线实现与测试 -> Phase 0 -> 冻结请求 -> Phase A -> readiness 判定 -> 条件式 Phase B -> cleanup -> Engineer 留档 -> Product closeout。
- Phase A 未形成有效 final 时不得让 Algorithm 或 Hardware 把 partial artifact 解释为 ready。
- Product 仅在 Engineer 完成证据留档后更新 `side2side_check.md`、`final.md`、`OKR.md` 和 progress log。

## Engineer 允许改动范围

- 本 sprint 后三文档：`sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route/tech-done.md`、`side2side_check.md`、`final.md`。
- 本 sprint Robot Software artifact：`sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route/artifacts/robot-software/`。
- Upper server 与 tests：现有 Upper readiness/start transport 服务文件及其直接测试文件，不扩散到无关 workstation 功能。
- O10 helper 与 tests：现有 no-motion readiness helper、bounded route helper 及其直接测试文件。
- 相关 `docs/`：只同步 frozen stdin、readiness、bounded route、cleanup 与真实证据边界。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 仅由 Product 在 closeout 阶段改动；Engineer 不提前改百分比或归档 KR。
- 不修改 WAVE ROVER 固件、串口参数、launch 默认控制参数、手机端或云端业务代码。
- 如实际修复需要越出上述范围，立即停止并回报，不在本 sprint 临时扩 scope。

## Phase 0 命令级预检

Phase 0 只读、无控制；以下命令由 Robot Software 在获得 fresh authorization 后按顺序执行并落盘 stdout、stderr、exit code：

```bash
set -euo pipefail
SPRINT=sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route
ART="$SPRINT/artifacts/robot-software"
mkdir -p "$ART"
LOCAL_UPPER_SHA="$(shasum -a 256 onboard/scripts/upper_robot_api.py | awk '{print $1}')"
LOCAL_O10_SHA="$(shasum -a 256 onboard/scripts/o10_amcl_nav2_runtime_proof.py | awk '{print $1}')"
ssh -p 37878 root@192.168.1.11 'git -C /root/rober rev-parse HEAD || true'
REMOTE_UPPER_SHA="$(ssh -p 37878 root@192.168.1.11 "sha256sum /root/rober/onboard/scripts/upper_robot_api.py | awk '{print \$1}'")"
REMOTE_O10_SHA="$(ssh -p 37878 root@192.168.1.11 "sha256sum /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py | awk '{print \$1}'")"
test "$REMOTE_UPPER_SHA" = "$LOCAL_UPPER_SHA"
test "$REMOTE_O10_SHA" = "$LOCAL_O10_SHA"
ssh -p 37878 root@192.168.1.11 'cd /root/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py'
ssh -p 37878 root@192.168.1.11 'systemctl is-active --quiet trashbot-upper-robot-api.service && systemctl show -p MainPID --value trashbot-upper-robot-api.service'
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/health | python3 -m json.tool'
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/status | python3 -m json.tool'
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/nav2/status | python3 -m json.tool'
```

- 远端 Git HEAD 仅记录为 provenance，不要求等于本地 commit；本轮部署身份由两份原子部署脚本 SHA 决定。
- 两份 remote script SHA 必须逐一等于本地已验证脚本 SHA，remote `py_compile`、service 和 health/status 必须全绿；任一失败立即 NO-GO。
- `trashbot-upper-robot-api.service` 必须 active，且初始 `/api/nav2/status` 必须是 stopped、无 owned PID、无残留 lifecycle ownership。
- Phase 0 不调用 start、proof、goal、manual、`/cmd_vel` 或 UART；任何意外运行态都先清理并停止本轮。
- Phase 0 失败不消费 authorization；但一旦发出 start attempt，authorization 立即消费，不以 HTTP、parse 或 semantic 结果为转移。

## Frozen stdin transport 命令级合同

- 唯一请求来源为本轮 `frozen_requests.json`；冻结后不得手工重写 body、字段或 key 顺序。
- 本地链固定为 `jq -c` -> parse/hash/count -> `ssh ... curl --data-binary @-` stdin。
- 禁止 inline JSON、远端 shell 变量拼 JSON、`echo '{...}'`、heredoc 内嵌请求体或二次 quoting。
- start body 在发送前和落盘 receipt 后都必须可独立 parse，并记录同一 SHA-256、byte count 与 newline count。

```bash
set -euo pipefail
SPRINT=sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route
REQ="$SPRINT/artifacts/robot-software/frozen_requests.json"
BODY="$SPRINT/artifacts/robot-software/phase_a_start.compact.json"
jq -c '.phase_a_start' "$REQ" | tee "$BODY" | python3 -m json.tool >/dev/null
sha256sum "$BODY"
wc -c -l "$BODY"
jq -c '.phase_a_start' "$REQ" | ssh -p 37878 root@192.168.1.11 \
  "curl -fsS -X POST -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:8787/api/nav2/start"
```

- `phase_a_start` 的 pipe 创建即视为唯一 start attempt；即使 SSH、curl、HTTP、JSON parse 或 remote handler 失败，也禁止 retry。
- start/proof/latest/owned-stop 每类 exactly once、总计 `1/1/1/1`；不得 fallback 到替代 endpoint 或第二次 curl。
- 四个固定 endpoint 依次为 POST `/api/nav2/start`、POST `/api/nav2/proof/refresh`、GET `/api/nav2/proof/latest`、POST `/api/nav2/stop`；POST body 均由本地 `jq -c` 后经 stdin 发送。
- 请求 hash/count 与 transport receipt 不一致时，结论固定为 transport NO-GO，不继续 Phase B。

## Phase A / Phase B 状态机

1. `P0_PRECHECK`：完成 SHA、service、health、initial stopped、owned residual 五项 gate。
2. `A_FROZEN`：冻结 start/proof/latest/owned-stop 请求与预期 hash/count。
3. `A_START_ATTEMPTED`：通过 stdin 唯一 POST `/api/nav2/start`；进入此状态即消费本轮 fresh authorization。
4. `A_PROOF_ONCE`：通过 stdin 只 POST 一次 `/api/nav2/proof/refresh`，等待 helper 自然返回；禁止 parent timeout 后用 partial 冒充 final。
5. `A_LATEST_ONCE`：只 GET 一次 `/api/nav2/proof/latest`，核对它与 start request、run id、自然 final 都是 same-current。
6. `A_OWNED_STOP_ONCE`：无论 proof GO/NO-GO，都通过 stdin 只 POST 一次 `/api/nav2/stop` 并记录 cleanup receipt。
7. `A_DECIDE`：只有 artifact 为 natural final，且 map/amcl/planner/controller、current pose/persisted pose、dynamic TF、planner-only path、obstacle clear 全绿，才写 `READINESS_GO=true`。
8. 任一字段缺失、stale、跨 run、partial、timeout、fallback、transport mismatch 或 semantic false，固定 `READINESS_GO=false`。
9. `B_CONDITIONAL`：Phase B 仅在 `READINESS_GO=true` 且 fresh authorization 已明确覆盖 bounded motion 时进入。
10. Phase B 固定执行 pre-base-stop -> bounded route goal once -> post-base-stop，不允许 goal retry。
11. Phase B 的任何异常都优先 post-base-stop 和 owned cleanup；不因需要补证据而重复 goal。
12. `T=1001` 仅在 Phase B 实际解锁且当前 run 出现反馈时条件采集；Phase A 不以制造 `T=1001` 为目标。
13. 未出现 `T=1001` 不得借用历史反馈；出现时由 Hardware 条件只读复核，不自动推出 HIL pass 或 safe-to-control。
14. `NO_GO_CLEANUP`：任何 NO-GO 都跳过 Phase B，确认 lifecycle stopped、owned PID null、residual process count 0 后封存。
15. 最终状态只有 `GO_PHASE_B_CLOSED`、`NO_GO_CLEAN` 或 `STOPPED_UNCLEAN_NEEDS_CEO`，不得留下隐含运行态。

## Artifact 与计数合同

- 冻结输入：`frozen_requests.json` exactly 1；必须通过 `python3 -m json.tool` 和 `jq -e`。
- Phase A：start request/response、proof request/final、latest response、owned-stop request/response 各 exactly 1。
- Phase A 计数字段固定为 `start_attempt_count=1`、`proof_attempt_count=1`、`latest_attempt_count=1`、`owned_stop_attempt_count=1`、`retry_count=0`。
- Readiness artifact 必须记录 same-current id、natural final、每个 readiness 子 gate、`READINESS_GO` 和失败原因。
- Phase B NO-GO 时 pre-stop/goal/post-stop artifact count 必须是 `0/0/0`。
- Phase B GO 时 pre-stop/goal/post-stop attempt count 必须是 `1/1/1`，且 goal retry count 为 `0`。
- cleanup artifact 必须记录 lifecycle stopped、owned PID null、residual count 0；任何一项不满足都不能标 clean。
- SHA-256、byte count、line count 必须同时覆盖 frozen source 提取 body 与实际发送 body。
- partial/interrupted artifact 可保留诊断价值，但不得计作 natural final、readiness 或 route execution success。
- 所有 artifact 必须保留 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`，除非本轮对应直接证据逐项满足。

## 验收命令

以下是 Engineer 实现后的可复制验收矩阵；先在本地运行离线项，只有离线全绿且 fresh authorization 有效时才运行远端项：

```bash
set -euo pipefail
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_parent_absolute_deadline_starts_before_popen
python3 -m unittest onboard/tests/test_upper_robot_api.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
```

```bash
set -euo pipefail
SPRINT=sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route
ART="$SPRINT/artifacts/robot-software"
python3 -m json.tool "$ART/frozen_requests.json" >/dev/null
jq -e '.phase_a_start | type == "object"' "$ART/frozen_requests.json" >/dev/null
jq -c '.phase_a_start' "$ART/frozen_requests.json" > /tmp/phase_a_start.compact.json
sha256sum /tmp/phase_a_start.compact.json "$ART/phase_a_start.compact.json"
wc -c -l /tmp/phase_a_start.compact.json "$ART/phase_a_start.compact.json"
cmp -s /tmp/phase_a_start.compact.json "$ART/phase_a_start.compact.json"
```

```bash
set -euo pipefail
LOCAL_UPPER_SHA="$(shasum -a 256 onboard/scripts/upper_robot_api.py | awk '{print $1}')"
LOCAL_O10_SHA="$(shasum -a 256 onboard/scripts/o10_amcl_nav2_runtime_proof.py | awk '{print $1}')"
ssh -p 37878 root@192.168.1.11 'git -C /root/rober rev-parse HEAD || true'
test "$(ssh -p 37878 root@192.168.1.11 "sha256sum /root/rober/onboard/scripts/upper_robot_api.py | awk '{print \$1}'")" = "$LOCAL_UPPER_SHA"
test "$(ssh -p 37878 root@192.168.1.11 "sha256sum /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py | awk '{print \$1}'")" = "$LOCAL_O10_SHA"
ssh -p 37878 root@192.168.1.11 'cd /root/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py'
test "$(ssh -p 37878 root@192.168.1.11 'systemctl is-active trashbot-upper-robot-api.service')" = active
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/health | python3 -m json.tool >/dev/null'
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/status | python3 -m json.tool >/dev/null'
ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/nav2/status' | jq -e '.state == "stopped" and (.owned_pid == null)'
```

```bash
set -euo pipefail
ART=sprints/2026.07.21_00-27_o3_o1_frozen_stdin_readiness_bounded_route/artifacts/robot-software
test "$(find "$ART" -maxdepth 1 -name 'phase_a_start*.json' | wc -l | tr -d ' ')" -ge 1
jq -e '.start_attempt_count == 1 and .proof_attempt_count == 1 and .latest_attempt_count == 1 and .owned_stop_attempt_count == 1 and .retry_count == 0' "$ART/attempt_counts.json"
jq -e 'if .READINESS_GO then (.same_current == true and .natural_final == true and .map_ready == true and .amcl_ready == true and .planner_ready == true and .controller_ready == true and .current_pose_ready == true and .persisted_pose_ready == true and .dynamic_tf_ready == true and .planner_only_path_ready == true and .obstacle_clear == true) else true end' "$ART/readiness_decision.json"
jq -e '.lifecycle_stopped == true and .owned_pid == null and .residual_process_count == 0' "$ART/cleanup.json"
rg -n 'READINESS_GO|same_current|natural_final|start_attempt_count|owned_stop_attempt_count|T=1001|route_execution_success|safe_to_control' "$ART" "$SPRINT/tech-done.md"
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py docs "$SPRINT"
```

## 中文注释与文档同步

- 若代码改动，所有新增或修改的技术注释必须使用中文，并解释冻结、exactly once、fail-closed 与 cleanup 的原因。
- 若代码改动，改动范围内有意义中文技术注释比例必须 `>20%`，由 Engineer 在 `tech-done.md` 记录统计方法和结果。
- Upper transport 合同变化同步到相关 workstation/Upper 文档；O10 helper 状态机变化同步到相关导航/现场验证文档。
- Engineer 先记录实际改动、完整命令输出、失败定位和剩余风险，不得把计划命令写成已执行证据。
- Product closeout 再更新 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`，并保持 O1/O3/O5/O6/O7 证据边界诚实。
- 若本轮仅 NO-GO cleanup，没有 route、delivery、HIL 或 user action 证据，则 OKR 百分比保持 flat、KR 不归档。

## 风险与停止条件

- 最大已知风险是 shell quoting 再次损坏 start JSON；stdin binary pipe、hash/count/cmp 是强制阻断门。
- start attempt 已消费授权；任何失败都 no retry，必须申请下一轮 fresh authorization 才能再尝试。
- remote SHA、service、health 或 initial stopped 任一失败：Phase 0 停止，不消费授权，不进入 frozen transport。
- proof 非 same-current natural final，或 current/persisted pose、dynamic TF、planner-only path 任一不绿：`READINESS_GO=false`。
- map、AMCL、planner、controller 或 obstacle clear 任一不绿：`READINESS_GO=false`，Phase B 不执行。
- cleanup 不能证明 lifecycle stopped、owned PID null、residual 0：立刻停止，把状态升级给 CEO，不开下一轮。
- Phase B 被条件解锁后，pre-stop 失败则不得发 goal；goal 后无论结果如何都必须尝试 post-stop，但不得重发 goal。
- `T=1001` 缺失、stale 或跨 run 只形成未证明边界，不能用历史 artifact 补当前 run。
- 任何 unexpected motion、非零残留控制、manual/`cmd_vel`/UART 越界都立即 stop、cleanup、封存并升级。
- 本 sprint 用户价值是获得一次语义完整、可审计且可安全停止的 readiness 决策；NO-GO clean 是有效安全结果，但不是 mission attempt 或 OKR credit。
