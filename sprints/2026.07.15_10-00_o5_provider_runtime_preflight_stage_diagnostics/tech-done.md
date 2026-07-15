# Tech Done - O5 Provider Runtime Preflight Stage Diagnostics

## 1. 状态与证据边界

- `sprint_type: epic`
- Delivery owner：`full-stack-software-engineer`
- 实现状态：独立的 provider runtime preflight stage diagnostics、成功/逐阶段失败矩阵、离线 dry artifact 与稳定接口文档均已完成。
- Dry gate 状态：`passed_offline_dry_gate`。
- Proof boundary：`software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`。
- 本轮没有执行上一 sprint live helper，没有 SSH/SCP/network/tunnel/public capture/probe/relay/proxy/机器人控制，也没有读取 production DB/queue/worker/OSS/CDN。
- 本轮只证明本地 fixture、official-release-shaped metadata 合同与阶段机；不证明真实 official binary 下载、真实 SHA/权限/version 执行、remote runtime、public HTTPS 或 production readiness。

## 2. 用户旅程变化与触点收益

部署/验收人员现在可以根据脱敏的 `completed_stages` 有序前缀、`last_reached_stage`、`next_expected_stage` 和固定 `failure_reason` 判断 preflight 停在 download、SHA command、SHA compare、chmod、version execution 还是 version match，不必再用一次整体 exit `1` 猜测失败原因。

失败输出不保存 raw reference、摘要原文、stderr/stdout、命令、绝对路径、credential、header/body 或 tunnel log；因此后续 Product/CEO 可以基于明确的安全阶段决定修复、切换 Objective 或是否另行授权 live，而不用重跑当前公网流程。本轮不改变普通手机用户界面，也不宣称公网控制面可用。

## 3. 实际改动

1. `artifacts/full-stack/provider_runtime_preflight_stage_diagnostics.py`
   - 固化 `download_started -> download_completed -> sha_command_completed -> sha_matched -> chmod_completed -> version_executed -> version_matched` 七阶段单调状态机。
   - 新增 `run_provider_runtime_preflight`、`advance_stage`、白名单 `build_artifact` 与只允许系统临时目录的 `LocalFixtureRunner`。
   - metadata 精确检查 provider、version、ARM64 asset name、官方 GitHub HTTPS owner/prefix 和 `sha256:<64hex>` 形状；reference/digest 只在内存中参与检查。
   - SHA command/match 与 version execution/match 分阶段记录；失败只输出 `download_failed`、`sha_command_failed`、`sha_mismatch`、`chmod_failed`、`version_execution_failed`、`version_mismatch`、`invalid_stage_transition`。
   - CLI 只接受 `--offline-dry-gate --output`；没有 SSH、URL、tunnel、relay、proxy 或 control 参数。
2. `artifacts/full-stack/test_provider_runtime_preflight_stage_diagnostics.py`
   - 新增 18 个测试，覆盖 happy path、六个逐阶段失败边界、跳级/重复/回退/完成后推进、hostile metadata、非本地 runner、非临时 root、路径逃逸、危险 true claim、白名单 key、脱敏和 offline dry gate。
3. `artifacts/full-stack/provider-runtime-preflight-dry-gate.json`
   - 保存七阶段完整成功 artifact；`official_provenance_contract_checked=true`，所有 external/live/user/production/mission/control/route/delivery/HIL 字段保持 false，tunnel/public 计数为 0。
4. `docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`
   - 固化 schema、完整字段类型/必填性/fail-closed 默认值、阶段语义、failure-prefix 矩阵、metadata/runner 合同、脱敏白名单与 offline-only 禁止边界。
5. `tech-done.md`
   - 记录实际改动、全部验证、失败修复、剩余风险与 proof boundary。

## 4. 接口影响与联调结果

- 新增稳定 schema：`trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1`。
- `passed_offline_dry_gate` 只在 metadata 合同检查完成、七阶段完整且 `failure_reason=null` 时成立；其他组合统一 `blocked_offline_dry_gate`。
- `completed_stages` 只能是固定阶段列表的有序前缀；`last_reached_stage` 是前缀末项，`next_expected_stage` 是紧邻下一项。
- 所有输出从固定白名单构造，调用方不能注入任意字段或将 production/mission/control claim 设为 true。
- 本轮为纯本地/离线合同验证，没有前后端、ROS2、上位机或真实 provider 联调；这是计划明确的安全边界，不是 live 联调成功。

## 5. 验证结果与失败修复

### 5.1 首轮失败与修复

1. 计划原命令：

   ```bash
   python3 -m unittest sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/test_provider_runtime_preflight_stage_diagnostics.py
   ```

   - exit `1`，关键日志：`ModuleNotFoundError: No module named 'sprints.2026'`、`Ran 1 test ... FAILED (errors=1)`。
   - 根因：`unittest` 把含点的 sprint 目录路径转换为模块名 `sprints.2026.07...`，在加载测试文件之前就失败；不是 test case failure。在限定五文件范围内不能通过新增 `sprints/2026/...` 包层级修复。
   - 复验采用等价且稳定的文件入口与 canonical discover 入口，二者均实际加载全部 18 个测试并通过；主节点已接受保留该命令解析偏差证据。
2. 中文注释比例首轮检查：实现 `20.4%` 通过，测试 `19.7%` 未达到严格 `>20%`。
   - 根因：测试代码增长后，有意义中文围栏注释数量不足。
   - 修复：补充 metadata checked、next stage、stable schema/failure enum 等测试原因说明；没有用空注释或无意义填充。
   - 复验：实现 `21.5%`、测试 `21.1%`，均严格 `>20%`。

### 5.2 逐条验收

1. `python3 -m py_compile ...provider_runtime_preflight_stage_diagnostics.py ...test_provider_runtime_preflight_stage_diagnostics.py`
   - exit `0`，无输出。
2. 计划 `python3 -m unittest <含点 sprint 路径/test.py>`
   - exit `1`，为上一节记录的路径转模块解析缺陷，测试文件未加载。
   - 等价修复入口 `python3 .../test_provider_runtime_preflight_stage_diagnostics.py`：exit `0`，`Ran 18 tests in 0.009s`，`OK`。
   - canonical 复验 `python3 -m unittest discover -s .../artifacts/full-stack -p 'test_provider_runtime_preflight_stage_diagnostics.py'`：exit `0`，`Ran 18 tests in 0.009s`，`OK`。
3. `python3 .../provider_runtime_preflight_stage_diagnostics.py --offline-dry-gate --output .../provider-runtime-preflight-dry-gate.json`
   - exit `0`；只使用受控内存 metadata、local fixture 与自动回收临时目录。
4. `python3 -m json.tool .../provider-runtime-preflight-dry-gate.json >/dev/null`
   - exit `0`。
5. tech-plan 第 7 节结构、脱敏与 proof-boundary Python 断言
   - exit `0`，输出 `o5_provider_runtime_preflight_stage_diagnostics_ok`。
6. tech-plan 第 7 节中文注释比例检查
   - exit `0`；`provider_runtime_preflight_stage_diagnostics.py chinese_comment_ratio=21.5%`，`test_provider_runtime_preflight_stage_diagnostics.py chinese_comment_ratio=21.1%`。
7. 完整 schema/stage/failure/offline/proof-boundary/禁止边界 `rg`
   - exit `0`；实现、测试、artifact、PRD/tech-plan 与稳定接口文档均命中要求锚点。
8. `git diff --check -- sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`
   - exit `0`，无 whitespace error。
9. `git status --short --untracked-files=all`
   - 仅列出本 sprint 的 Product 计划文档、获准的三个 full-stack artifact、`tech-done.md` 和稳定接口文档；没有本 sprint/接口文档之外的新改动。本 Engineer 未修改既有 `pre_start.md`、`prd.md`、`tech-plan.md`。

## 6. 完成前反思

- 需求满足：七阶段固定顺序、失败枚举、逐阶段矩阵、local runner、official-release-shaped metadata 合同、脱敏 artifact 和稳定接口文档均已实现并验证。
- 范围满足：本 Engineer 只新增或修改计划允许的五个文件，没有修改上一 sprint、工程代码、`OKR.md`、progress log、`side2side_check.md` 或 `final.md`。
- 无遗留 `TODO/FIXME`；没有为了通过测试放宽 metadata、runner、path、artifact 或 safety gate。
- 验证偏差仅为计划 unittest 路径被 Python 解析为非法模块层级；已用直接文件入口与 discover 双重证明全部 18 个测试真实通过，并保留原失败事实。

## 7. Delta、OKR 建议与剩余风险

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `production_ready=false`
- `mission_objective_0_satisfied=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

建议 O5 保持约 `85%`，KR `不归档`。本轮只允许接受为 stage diagnostics contract ready，不形成 Mission Objective 0 或 success-class external evidence。

剩余风险：

1. 没有真实 official binary download/SHA/chmod/version 结果；本地 fixture 成功不能定位上一轮 live exit `1` 的真实子阶段。
2. 没有 SSH/remote runtime、tunnel/public URL、TLS/certificate、GET/HEAD 或公网负向隔离证据。
3. 没有 production cloud、真实手机/browser、4G、route、delivery、HIL 或机器人控制证据。
4. 这是同一 `provider_runtime_preflight` blocker 的第二轮也是最后一轮消费；下一轮不得再包装本地 stage/readback。按 sprint 红线必须切换 Objective，或由 CEO 明确决策是否授权全新的 live 取证方向。
