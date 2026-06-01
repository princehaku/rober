# O5/O6 Python External Probe Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- 新增 `cloud-relay/scripts/o5_o6_external_live_probe.py`：Python 3 标准库 O5/O6 external live probe，输出 `trashbot.o5_o6.external_live_probe.v1`，并标记 `runner=python_stdlib`。
- 新增 `cloud-relay/tests/test_o5_o6_external_live_probe.py`：覆盖未配置 URL 的 fail-closed 输出、GET-only/bearer redaction、HTTP 401/503、坏 JSON、schema mismatch、危险 true 字段、敏感 marker 和网络不可达分类。
- 更新 `cloud-relay/README.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/o6_cloud_archive_core_api.md`、`docs/interfaces/o1_o5_90_evidence_boundary.md`：记录 Python runner 的运行方式、stdin/SSH 入口和证据边界。
- 更新 `OKR.md`：O5/O6 保持约 93%，口径从 Node external probe 扩展为 `external live probe entry + Python stdlib runner`，并保留 `real material not_proven`。

## 用户旅程变化和触点收益

- O5/O6 外部健康探测不再被上位机缺 Node.js 阻塞；Orange Pi / 上位机可以直接用系统 Python 通过 stdin 运行同一类只读 probe。
- 运维和手机/支持链路后续能区分“脚本无法运行”“网络不可达”“URL 未配置”“HTTP/JSON/schema 漂移”“上游越界声明控制/生产能力”等问题。
- 本轮只推进外部可观测入口，不开放任何发车、ACK、机器人控制或硬件读取能力。

## 接口影响

- CLI：`cloud-relay/scripts/o5_o6_external_live_probe.py`
- 输出 schema：`trashbot.o5_o6.external_live_probe.v1`
- runner：`python_stdlib`
- 只读 endpoint：
  - `GET /api/o5/readiness/health`
  - `GET /api/o6/archive/health`
  - 可选 PC aggregate：`GET /api/o5-o6/cloud-relay-health?baseUrl=<cloud-base-url>`
- 参数：`--once-json`、`--pc-base-url`、`--cloud-base-url`、`--timeout-ms`
- 环境变量：`ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`、`ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL`、`ROBER_CLOUD_RELAY_BASE_URL`、`TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN`、`ROBER_CLOUD_RELAY_BEARER_TOKEN`
- 固定边界：`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`reads_hardware=false`、`delivery_success=false`

## 验证结果

```text
$ python3 -m py_compile cloud-relay/scripts/o5_o6_external_live_probe.py
pass: exit 0, no output
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest cloud-relay/tests/test_o5_o6_external_live_probe.py
Ran 4 tests ... OK
```

```text
$ python3 cloud-relay/scripts/o5_o6_external_live_probe.py --once-json || true
schema=trashbot.o5_o6.external_live_probe.v1
runner=python_stdlib
probe_status=fail_closed
token_status=absent
summary.reachable_count=0
blocked_reasons=[base_url_not_configured, base_url_not_configured, base_url_not_configured]
safe_to_control=false
sends_commands=false
robot_control_executed=false
reads_hardware=false
delivery_success=false
```

```text
$ python3 - <<'PY'
from pathlib import Path
p = Path('cloud-relay/scripts/o5_o6_external_live_probe.py')
lines = [line for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
comments = [line for line in lines if line.lstrip().startswith('#') and any('\u4e00' <= ch <= '\u9fff' for ch in line)]
print({'chinese_technical_comment_lines': len(comments), 'nonblank_code_lines': len(lines), 'comment_ratio': round(len(comments) / len(lines), 3)})
PY
{'chinese_technical_comment_lines': 88, 'nonblank_code_lines': 386, 'comment_ratio': 0.228, 'passes': True}
```

```text
$ ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < cloud-relay/scripts/o5_o6_external_live_probe.py
exit 2
```

远端 SSH 最新结论：用户恢复供电后，SSH 已连上，远端 Python 已执行脚本；输出结构化 `probe_status=fail_closed`，三个 endpoint 的 `failure_category=base_url_not_configured`，安全字段仍为 false。这不是旧的 `remote_network_unreachable` blocker，当前 blocker 是远端尚未配置 `pc_base_url` / `cloud_base_url`。

```text
$ git diff --check -- cloud-relay/scripts/o5_o6_external_live_probe.py cloud-relay/tests/test_o5_o6_external_live_probe.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/interfaces/o6_cloud_archive_core_api.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/process/okr_progress_log.md OKR.md sprints/2026.06.01_21-22_o5-o6-python-external-probe/tech-done.md
pass: exit 0, no output
```

## 失败定位

- 代码和本地测试没有 blocker。
- 远端上位机不再卡在没电/SSH 不通；本轮已证明 `python3 -s - --once-json` stdin 执行路径可达。
- 当前远端正向 probe 仍未观察到 O5/O6 endpoint，因为没有传入或配置 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` / `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` / `ROBER_CLOUD_RELAY_BASE_URL`。

## Product Closeout

- 用户价值和产品北极星：O5/O6 的外部健康观察入口现在可在缺 Node.js 的上位机运行，降低现场采证门槛，服务于“普通用户只通过手机看到云端/数据层是否可用、缺什么证据”的产品方向。
- OKR 映射和方向判断：映射 Objective 5 与 Objective 6；方向继续，不暂停、不替换；完成度保持约 93%，因为仍缺真实公网、真实 4G、production DB/queue、OSS/CDN、真实 phone/browser 和上车数据。
- KR 更新：O5 KR1/KR5/KR6 与 O6 KR6 获得软件侧 external probe runner 补强；没有 KR 可移入真实材料历史归档。
- 本轮核心抓手：把 Node external probe 的能力补成 Python stdlib runner，并用本地 unittest + 远端 stdin 执行证明脚本可在上位机运行。
- 下一步：给远端设置 cloud/PC base URL 与 bearer 环境变量，再采集正向 endpoint 可达性；若进入 production 材料，必须继续按 `docs/interfaces/o1_o5_90_evidence_boundary.md` 收集真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser。
- 责任 Engineer：后续仍由 `full-stack-software-engineer` 主责；如涉及上车事件数据或 robot ACK，再由 `robot-software-engineer` 补接口事实。

## 剩余风险

- 不证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser、robot ACK、HIL 或 delivery success。
- 不读取硬件、不发送控制、不访问 `/robots/*`、不 POST。
- 远端现在只证明 Python runner 可执行和未配置 URL 时 fail-closed；尚未证明 O5/O6 endpoint 从上位机可达。
