# Tech Plan - O5 Public Health Tunnel External Evidence

## 1. 方案概览

由 `full-stack-software-engineer` 单 owner 闭环交付：先实现纯标准库 loopback allowlist proxy 和隔离测试，再做一次 helper-owned live run。数据路径固定为：

```text
Cloudflare public HTTPS quick tunnel
  -> http://127.0.0.1:<proxy_port>
  -> allowlist proxy（仅 GET/HEAD /healthz）
  -> http://127.0.0.1:<relay_port>/healthz
```

Cloudflare 绝不能直连 relay。relay 和 proxy 都只允许监听 `127.0.0.1`；command、task、manual control、`/cmd_vel`、UART、route、delivery、HIL 以及其他 relay API 全部不在本轮执行范围内。

## OKR 最低优先级核对

1. `OKR.md` 4.1 节当前完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 直接针对 O5，计划形成一次 current-run、真实公网、certificate-valid HTTPS external artifact。
3. O6/O7 约 `93%`、O1 约 `94%`；本轮无偏离最低 Objective 的理由。若所有 gate 通过，Product 可接受 O5 `85% -> 86%`；失败则 flat。
4. 无论结果如何，保持 `production_ready=false`、Mission Objective 0 未满足、KR `不归档`。

## 2. Owner 与文件范围

主责 owner：`full-stack-software-engineer`。

Engineer 仅允许修改：

- `cloud-relay/scripts/healthz_allowlist_proxy.py`
- `cloud-relay/test/test_healthz_allowlist_proxy.py`
- `cloud-relay/docker-compose.yml`
- `cloud-relay/README.md`
- `sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/tech-done.md`
- `sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/artifacts/**`

不得修改 relay handler、command contract、ROS2、硬件、launch/config、`OKR.md` 或其他 sprint。不得预生成 `side2side_check.md` / `final.md`。

## 3. 实现设计

### 3.1 Proxy contract

`healthz_allowlist_proxy.py` 使用 `http.server`、`http.client` / `urllib` 等 Python 标准库：

- CLI 必须显式配置 listen host/port 与 upstream host/port；listen host 和 upstream host 非 `127.0.0.1` 时启动失败。
- 对原始 request target 做精确比较，只允许 `/healthz`；任何 query、absolute URI、编码、点段、双斜杠、反斜杠或超长 target 都返回 `404`。
- `GET /healthz`：proxy 自己构造固定 upstream `GET /healthz`，只返回安全必要 headers 和 upstream status/body；不透传外部 header/body。
- `HEAD /healthz`：proxy 仍以固定 upstream `GET /healthz` 验证健康，但对公网只返回 status/安全 headers 和零长度 body。
- 精确 `/healthz` 的非 GET/HEAD method 返回 `405`，携带固定 `Allow: GET, HEAD`；其他 path 不因 method 暴露路由存在性，统一 `404`。
- upstream error/timeout 返回固定脱敏 `502/504`；不得返回 traceback、路径、token、header 或 upstream body 片段。
- 设置 body/header/target 上限并关闭不必要连接复用，避免负向 probe 形成资源放大。

### 3.2 Compose boundary

把 host publish 从所有接口改为 loopback：

```yaml
ports:
  - "127.0.0.1:${TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT:-8088}:${TRASHBOT_REMOTE_CLOUD_PORT:-8088}"
```

容器内 relay 可继续监听 `0.0.0.0`，但主机仅 `127.0.0.1` 可达。README 必须记录 quick tunnel 只能指向 proxy，直接 relay 为 `NO-GO`。

### 3.3 测试矩阵

单测启动 helper-owned fake upstream 与 proxy，覆盖：

- GET/HEAD 精确 `/healthz` 正向；HEAD body 为空。
- `/readyz`、`/preflightz`、`/api/status`、`/api/commands/collect`、`/api/o6/archive/tasks` 为 `404`，且 upstream request count 不变。
- `/healthz?x=1`、`//healthz`、`/%68ealthz`、`/healthz/..`、反斜杠、absolute-form、超长 target 为 `404`。
- POST/PUT/PATCH/DELETE/OPTIONS 精确 `/healthz` 为 `405`，upstream request count 不变。
- Authorization、Cookie、Host、Forwarded、X-Forwarded-* 与 body 不会进入 upstream。
- upstream timeout/error 只返回脱敏 `502/504`。
- proxy 非 `127.0.0.1` listen/upstream 配置拒绝启动。

## 4. 一次 live run

Engineer 在本地 gate 全绿后只执行一次 bounded live capture：

1. 用 SSH 确认目标架构仍为 `aarch64`；若漂移则停止。
2. capture helper 通过 Cloudflare 官方 HTTPS release/API 动态选择 `cloudflared-linux-arm64`，读取 version、asset HTTPS URL 与官方 `sha256:` digest。若 digest 缺失或 URL/owner/asset 不匹配，停止；不得硬编码未知 checksum。
3. 下载到 run-id 临时目录，计算 SHA256 与官方 digest 比对，再执行 `--version` 复核版本；任何 mismatch 禁止启动。
4. helper 在临时 staged tree 中启动 relay 和 proxy，二者只监听 `127.0.0.1`；记录 state 的运行前 checksum。token 仅存在内存/环境，不写 artifact。
5. helper 启动 cloudflared，target 只能是 proxy loopback URL。raw public URL 仅在进程内存/临时受控流中用于 probe，不写 stdout 留档、artifact、`tech-done.md` 或 git。
6. 开发机使用默认 CA/hostname verification 发起公网 HTTPS 请求，禁止 `-k`：
   - GET `/healthz`：certificate-valid HTTPS `2xx/3xx`。
   - HEAD `/healthz`：certificate-valid HTTPS `2xx/3xx`、无 body。
   - 负向 path/query/encoded target：`404`。
   - 精确 `/healthz` 的非允许 method：`405`。
7. 复算 relay state checksum，必须前后一致；负向请求不能形成 archive/command/status delta。
8. helper 在 `finally`/trap 中只清理本 run ownership 的 relay、proxy、cloudflared、container/process group 和临时目录；最终 inventory 必须 `cleanup residual=0`。
9. 生成脱敏 artifact：只含 host hash、TLS/cert 摘要、HTTP class、bucket timing、provider/version/SHA256 verification 与 negative matrix；禁止 raw URL/token/header/body/path/tunnel log。

建议 live helper 与结果位于：

- `artifacts/full-stack/live_capture_helper.py`
- `artifacts/full-stack/public-health-tunnel-evidence.json`

helper 是本 sprint 的可审计 capture 工具，不得成为长期 tunnel daemon。

## 5. 失败分支

- 本地 allowlist/compose gate 失败：Engineer 定位并修复后复验；未全绿不得 live。
- 官方 API/release HTTPS、asset owner/name、version、aarch64 或 SHA256 gate 失败：不运行 binary，cleanup，O5 flat。
- tunnel URL 超时或 edge 不可达：cleanup，记录 provider stage 和脱敏 reason，O5 flat。
- TLS/cert 无效、非 HTTPS、unexpected redirect、GET/HEAD 非 `2xx/3xx`：cleanup，O5 flat。
- 任一负向 probe 非预期 `404/405` 或 upstream 被命中：立即停止、cleanup、修复安全缺陷；本轮 live 只有一次，不以第二个 tunnel run 补证据。
- state checksum 改变、artifact 泄密或 cleanup residual 非零：验收失败、O5 flat。
- 所有失败都保持 `external_artifact_delta=false`、`production_ready=false`、Mission Objective 0 未满足、KR `不归档`。

## 6. 接口影响

- 新增本机 health-only proxy CLI，不改变 relay `/healthz` response schema。
- relay 原有 GET/POST route、bearer contract、state schema 和 ROS2 interface 不变。
- compose host publish 收紧到 `127.0.0.1`，可能影响过去依赖 LAN 直连 `8088` 的开发方式；README 必须给出显式迁移说明。
- 公网仅新增临时 `GET/HEAD /healthz` 观察能力；不新增 command/task/status/archive/control API。

## 7. 验收命令

Engineer 必须运行并在 `tech-done.md` 留下 exit code 与关键日志：

```bash
python3 -m py_compile cloud-relay/scripts/healthz_allowlist_proxy.py
python3 -m unittest discover -s cloud-relay/test -p 'test_healthz_allowlist_proxy.py'
docker compose -f cloud-relay/docker-compose.yml config >/tmp/rober-o5-compose-config.yml
rg -n '127\.0\.0\.1.*TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT|healthz|GET|HEAD|404|405|NO-GO|cloudflared' \
  cloud-relay/docker-compose.yml cloud-relay/README.md cloud-relay/scripts/healthz_allowlist_proxy.py
git diff --check -- cloud-relay/scripts/healthz_allowlist_proxy.py \
  cloud-relay/test/test_healthz_allowlist_proxy.py cloud-relay/docker-compose.yml cloud-relay/README.md \
  sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence
```

一次 live capture 的计划入口：

```bash
python3 sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/artifacts/full-stack/live_capture_helper.py \
  --ssh-target root@192.168.1.11 --ssh-port 37878 \
  --expected-arch aarch64 --provider cloudflare \
  --output sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/artifacts/full-stack/public-health-tunnel-evidence.json
```

artifact 结构与脱敏验收：

```bash
python3 -m json.tool sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/artifacts/full-stack/public-health-tunnel-evidence.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path

p = Path('sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/artifacts/full-stack/public-health-tunnel-evidence.json')
d = json.loads(p.read_text())
assert d['provider']['name'] == 'cloudflare'
assert d['provider']['architecture'] == 'aarch64'
assert d['provider']['sha256_verified'] is True
assert d['public_probe']['tls_certificate_valid'] is True
assert d['public_probe']['get_status_class'] in ('2xx', '3xx')
assert d['public_probe']['head_status_class'] in ('2xx', '3xx')
assert d['negative_matrix']['all_fail_closed'] is True
assert d['negative_matrix']['state_unchanged'] is True
assert d['negative_matrix']['cleanup_residual_count'] == 0
for forbidden in ('raw_url', 'token', 'authorization', 'headers', 'request_body', 'response_body', 'tunnel_log'):
    assert forbidden not in p.read_text().lower()
print('o5_public_health_tunnel_external_evidence_ok')
PY
```

## 8. Product 验收与计分

Product Owner 只在以上本地、live、negative、state、redaction、cleanup gate 全部通过后接受：

- `current_run_artifact_delta=true`
- `external_artifact_delta=true`
- O5 `85% -> 86%`

并继续保持：

- `production_ready=false`
- `mission_objective_0_satisfied=false`
- KR `不归档`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`
- `safe_to_control=false`

temporary tunnel 不等于稳定 DNS、凭证、4G、production DB/queue、worker、OSS/CDN 或真手机。任一验收失败则 O5 flat，Product 在 `final.md` 记录 exact blocker 和下一条 success-class 外部证据，不重复包装本轮抓手。
