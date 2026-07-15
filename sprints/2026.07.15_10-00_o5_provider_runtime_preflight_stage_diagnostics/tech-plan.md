# Tech Plan - O5 Provider Runtime Preflight Stage Diagnostics

## 1. 方案概览

由 `full-stack-software-engineer` 单 owner 闭环。基于上一轮 helper 的 provider runtime 边界，在本 sprint 新建独立、可测试的离线 stage diagnostics 实现；不修改已关闭 sprint，不执行其 live helper。实现把七个阶段建模为只增不减的有限状态机，并用注入式本地 runner 完成 official provenance contract dry gate 与失败矩阵。

## OKR 最低优先级核对

1. `OKR.md` 4.1 节当前完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 直接针对 O5 的 `provider_runtime_preflight` blocker，不偏离最低 Objective。
3. O1 约 `94%`、O6/O7 各约 `93%`；本轮只消费同一 blocker 最后一轮，不安排 O6/O7 support wrapper。
4. 本轮无 live/external delta，O5 必须保持约 `85%`，KR `不归档`。若 stage 仍不能定位或离线 gate 失败，下轮必须切换 Objective 或升级 CEO。

## 2. Owner 与精确文件范围

主责 owner：`full-stack-software-engineer`。

Engineer 仅允许新增或修改：

- `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider_runtime_preflight_stage_diagnostics.py`
- `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/test_provider_runtime_preflight_stage_diagnostics.py`
- `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider-runtime-preflight-dry-gate.json`
- `sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/tech-done.md`
- `docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md`

不得修改上一 sprint helper、cloud-relay、PC workstation、ROS2、硬件、launch/config、`OKR.md`、`docs/process/okr_progress_log.md` 或其他 sprint。不得预生成 `side2side_check.md` / `final.md`。

### 2.1 文档同步契约

`full-stack-software-engineer` 必须在 `docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md` 固化稳定接口，内容必须与实现和测试一致：

- 完整 schema、字段类型、必填性及 fail-closed 默认值；
- `download_started -> download_completed -> sha_command_completed -> sha_matched -> chmod_completed -> version_executed -> version_matched` 固定顺序；
- 全部 failure enums 及每个失败点允许出现的 `completed_stages` 前缀；
- artifact 脱敏白名单、禁止字段和不允许拼接原始异常的规则；
- proof boundary `software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`；
- offline-only 边界，以及禁止 SSH/live、禁止启动 tunnel、禁止 public capture/probe、禁止 robot control。

文档同步属于本轮验收门槛，不得以 `tech-done.md` 或代码注释代替。

## 3. Stage 状态机与接口

固定顺序常量：

```text
download_started -> download_completed -> sha_command_completed -> sha_matched
-> chmod_completed -> version_executed -> version_matched
```

模块暴露纯函数/可注入接口：

- `run_provider_runtime_preflight(release_metadata, runner) -> dict`
- `advance_stage(stage)` 只接受紧邻下一 stage，重复、跳级、回退均抛安全枚举错误。
- `build_artifact(...)` 只从白名单字段构造 `trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1`。
- CLI `--offline-dry-gate --output <path>` 只能使用本地 fixture/stub 与临时目录；不得接受 SSH target、public URL 或 tunnel 参数。

阶段语义：发起本地 download stub 前记 `download_started`；成功落盘后记 `download_completed`；SHA 命令成功并得到格式合法摘要后记 `sha_command_completed`；常量时间比对成功后记 `sha_matched`；本地权限调整成功后记 `chmod_completed`；version 命令 exit `0` 后记 `version_executed`；输出包含 metadata version 后记 `version_matched`。

失败只输出安全 reason enum，例如 `download_failed`、`sha_command_failed`、`sha_mismatch`、`chmod_failed`、`version_execution_failed`、`version_mismatch`、`invalid_stage_transition`；不得拼接异常文本、exit stderr、URL、路径或 checksum。

## 4. Offline official provenance dry gate

- 用 test-owned 临时目录生成 deterministic local provider stub 与 official-release-shaped metadata fixture；metadata 必须通过 provider、version、ARM64 asset name、HTTPS owner/prefix 和 `sha256:<64hex>` 形状校验。
- fixture URL/digest 只在内存中参与合同验证；primary artifact 不写 raw URL 或 checksum 原文。
- runner 必须由测试注入，且只允许 temp-root 下的本地文件/命令；任何 SSH/SCP、network、cloudflared tunnel、relay/proxy 或 public probe 调用令测试立即失败。
- 覆盖成功和每一失败边界，断言 `completed_stages` 始终是固定 stage 列表的有序前缀。
- 成功 artifact 仍固定所有 delta、production、mission、control、route、delivery、HIL、安全字段为 false。

## 5. 中文注释与质量要求

- 两个 Python 文件的技术注释全部使用中文，解释状态机单调性、脱敏原因、runner 隔离和 fail-closed 边界。
- 按“含中文的纯 `#` 注释行 / 非空行”统计，每个 Python 文件必须严格 `>20%`。
- 不留 TODO/FIXME，不读取环境 credential，不创建范围外持久文件；临时文件必须自动清理。

## 6. 禁止动作与 proof boundary

- 不得 SSH/live，不得运行上一 sprint live helper。
- 不得启动 tunnel，不得公网 capture/probe，不得访问 public URL。
- 不得启动 relay/proxy，不得读写 command/task/archive/production state。
- 不得执行机器人控制、`/cmd_vel`、`/api/base/manual`、UART、route、delivery 或 HIL。

Proof boundary 固定为 `software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only`。它只证明本地阶段诊断与 official provenance contract dry gate，不证明真实 official binary provenance、远端 runtime、public HTTPS 或 production readiness。

## 7. Engineer 验收命令

Engineer 必须运行并把 exit code/关键日志写入 `tech-done.md`：

```bash
python3 -m py_compile \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider_runtime_preflight_stage_diagnostics.py \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/test_provider_runtime_preflight_stage_diagnostics.py

python3 -m unittest \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/test_provider_runtime_preflight_stage_diagnostics.py

python3 sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider_runtime_preflight_stage_diagnostics.py \
  --offline-dry-gate \
  --output sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider-runtime-preflight-dry-gate.json

python3 -m json.tool \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider-runtime-preflight-dry-gate.json >/dev/null
```

结构、脱敏与 proof boundary 断言：

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path('sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack/provider-runtime-preflight-dry-gate.json')
text = p.read_text(encoding='utf-8')
d = json.loads(text)
stages = ['download_started', 'download_completed', 'sha_command_completed', 'sha_matched', 'chmod_completed', 'version_executed', 'version_matched']
assert d['completed_stages'] == stages
assert d['provider_runtime_preflight_status'] == 'passed_offline_dry_gate'
assert d['proof_boundary'] == 'software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only'
for key in ('network_access_attempted', 'ssh_attempted', 'production_ready', 'mission_objective_0_satisfied', 'route_execution_success', 'delivery_success', 'hil_pass', 'safe_to_control'):
    assert d[key] is False
for key in ('tunnel_start_attempt_count', 'public_capture_count', 'public_probe_attempt_count'):
    assert d[key] == 0
for forbidden in ('raw_url', 'token', 'authorization', 'checksum', 'stderr', 'stdout', 'response_body', 'tunnel_log', '/users/', '/tmp/'):
    assert forbidden not in text.lower()
print('o5_provider_runtime_preflight_stage_diagnostics_ok')
PY
```

中文注释 `>20%` 检查：

```bash
python3 - <<'PY'
import re
from pathlib import Path

root = Path('sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics/artifacts/full-stack')
for name in ('provider_runtime_preflight_stage_diagnostics.py', 'test_provider_runtime_preflight_stage_diagnostics.py'):
    lines = root.joinpath(name).read_text(encoding='utf-8').splitlines()
    nonempty = [line for line in lines if line.strip()]
    comments = [line for line in nonempty if line.lstrip().startswith('#') and re.search(r'[\u4e00-\u9fff]', line)]
    ratio = len(comments) / len(nonempty)
    assert ratio > 0.20, (name, ratio)
    print(name, f'chinese_comment_ratio={ratio:.1%}')
PY
```

最终锚点与 diff：

```bash
rg -n 'trashbot\.o5\.provider_runtime_preflight_stage_diagnostics\.v1|download_started|download_completed|sha_command_completed|sha_matched|chmod_completed|version_executed|version_matched|download_failed|sha_command_failed|sha_mismatch|chmod_failed|version_execution_failed|version_mismatch|invalid_stage_transition|offline|proof_boundary|不得启动 tunnel|不得公网|robot control' \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics \
  docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md
git diff --check -- \
  sprints/2026.07.15_10-00_o5_provider_runtime_preflight_stage_diagnostics \
  docs/interfaces/o5_provider_runtime_preflight_stage_diagnostics.md
```

## 8. Product 验收与后续路由

Product 只接受：stage 成功/失败矩阵、离线 dry artifact、脱敏、中文注释、targeted tests 与 scoped diff 全绿。即使全绿也保持 O5 flat、KR 不归档，不产生 external/current-run/live-control/user-action delta。

若 stage 仍不能定位或离线 gate 失败，不允许 live 补测；下一轮必须切换 Objective 或升级 CEO。只有以后新的明确授权才可规划一次新的 public capture，本 sprint 不包含该动作。
