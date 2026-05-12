# scripts/（仓库根）

上车构建与硬件 smoke 已迁至 **`onboard/scripts/`**，请从仓库根使用：

- `bash onboard/scripts/docker_humble_build.sh`
- `bash onboard/scripts/docker_humble_dev.sh`
- `bash onboard/scripts/run_smoke_tests.sh`
- `python3 onboard/scripts/hardware_smoke_wave_rover.py --help`

证据交叉检查与手机浏览器验收脚本在 **`pc-tools/evidence/`**：

- `python3 pc-tools/evidence/evidence_crosscheck.py --help`
- `python3 pc-tools/evidence/phone_browser_acceptance_gate.py --help`

4G 云中转 Docker smoke：

- `bash cloud-relay/scripts/docker_smoke.sh`（在任意目录执行均可，脚本会 `cd` 到 `cloud-relay/`）

本目录仅保留本说明；避免在根目录再新增与上车强耦合的脚本，以免与 `onboard/`、`pc-tools/`、`cloud-relay/` 分层冲突。
