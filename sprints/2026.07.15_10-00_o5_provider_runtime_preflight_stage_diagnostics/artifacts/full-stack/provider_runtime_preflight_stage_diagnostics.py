#!/usr/bin/env python3
"""O5 provider runtime preflight 的纯离线阶段诊断。"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# 安全设计 01：模块导入不得发起网络、SSH 或子进程。
# 安全设计 02：CLI 只保留 offline dry gate 这一条执行路径。
# 安全设计 03：official release reference 只在内存中验证形状。
# 安全设计 04：primary artifact 永远不保存 reference 或摘要原文。
# 安全设计 05：每次阶段推进都重新验证整个历史前缀。
# 安全设计 06：完成阶段是事实记录，不能由失败原因倒推出补写。
# 安全设计 07：失败只能停在最后一个已经安全到达的阶段。
# 安全设计 08：SHA 计算成功与摘要匹配必须拆成两个事实。
# 安全设计 09：version 执行成功与版本匹配也必须拆成两个事实。
# 安全设计 10：metadata 不合法时不得记录 download_started。
# 安全设计 11：runner 不合法时同样不得记录任何执行阶段。
# 安全设计 12：runner 只能在系统临时根下创建 fixture。
# 安全设计 13：文件操作点必须重复检查路径没有逃逸 root。
# 安全设计 14：fixture 内容固定，保证 dry gate 可确定复验。
# 安全设计 15：本地摘要使用标准库，不调用 sha256sum 命令。
# 安全设计 16：权限调整只作用于自动回收的临时文件。
# 安全设计 17：version 使用受控 stub，不执行伪二进制内容。
# 安全设计 18：底层异常文本永远不能进入 failure_reason。
# 安全设计 19：artifact 只能从固定白名单字段全量构造。
# 安全设计 20：调用方不能传入 production 或 mission 真值。
# 安全设计 21：所有网络、SSH、tunnel 计数固定为零或假。
# 安全设计 22：所有 route、delivery、HIL、安全声明固定为假。
# 安全设计 23：dry gate 成功不代表当前 official binary 已验证。
# 安全设计 24：proof boundary 必须与稳定接口文档完全一致。
# 安全设计 25：schema 变更必须显式升级，不能静默扩展字段。
# 安全设计 26：临时目录退出后不保留 provider runtime fixture。
# 安全设计 27：CLI 输出只序列化 build_artifact 的返回对象。
# 安全设计 28：输出不记录时间，避免形成不必要的运行 trace。
# 安全设计 29：输出不记录本机路径，避免泄漏用户目录结构。
# 安全设计 30：任何不确定组合一律回落为 fail-closed 状态。
# 安全设计 31：失败 artifact 仍保留 metadata 合同是否完成的布尔事实。
# 安全设计 32：状态机内部错误与输入非法统一使用安全转换枚举。
# 安全设计 33：runner 失败注入只用于本地逐阶段测试矩阵。
# 安全设计 34：成功 artifact 不保存 fixture provider 的原始输出。
# 安全设计 35：所有输出值都能由稳定接口文档独立解释。

# 阶段顺序是稳定接口，新增、删除或重排都必须升级 schema。
STAGES = (
    "download_started",
    "download_completed",
    "sha_command_completed",
    "sha_matched",
    "chmod_completed",
    "version_executed",
    "version_matched",
)

# 失败原因只允许安全枚举，绝不拼接底层异常或命令输出。
FAILURE_REASONS = (
    "download_failed",
    "sha_command_failed",
    "sha_mismatch",
    "chmod_failed",
    "version_execution_failed",
    "version_mismatch",
    "invalid_stage_transition",
)

# schema 和 proof boundary 同时用于实现、测试、文档和 dry artifact。
SCHEMA = "trashbot.o5.provider_runtime_preflight_stage_diagnostics.v1"
PROOF_BOUNDARY = "software_proof_o5_provider_runtime_preflight_stage_diagnostics_offline_only"

# fixture 只模拟官方 release 的字段形状，不访问该地址。
OFFICIAL_PROVIDER = "cloudflare"
OFFICIAL_ARCHITECTURE = "aarch64"
OFFICIAL_ASSET_NAME = "cloudflared-linux-arm64"
OFFICIAL_RELEASE_PREFIX = "https://github.com/cloudflare/cloudflared/releases/download/"
VERSION_RE = re.compile(r"^[0-9]{4}\.[0-9]{1,2}\.[0-9]+$")
DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


class SafeStageError(ValueError):
    """阶段机或输入合同不安全时使用的无敏感信息异常。"""


class OfflineRunnerFailure(RuntimeError):
    """本地 runner 注入失败时使用的内部异常。"""


# 本地 runner 是唯一可执行实现，避免任意 command runner 偷渡网络能力。
class LocalFixtureRunner:
    """只在系统临时目录内读写 deterministic fixture。"""

    offline_only = True

    def __init__(
        self,
        root: Path,
        fixture_bytes: bytes,
        fixture_version: str,
        failures: Iterable[str] = (),
    ) -> None:
        # root 不被写入 artifact，只作为进程内的隔离边界。
        self.root = Path(root).resolve()
        self.fixture_bytes = bytes(fixture_bytes)
        self.fixture_version = str(fixture_version)
        self.failures = frozenset(failures)
        # 这些计数仅用于测试证明 runner 没有网络或 SSH 分支。
        self.network_access_attempted = False
        self.ssh_attempted = False

    def _guard_path(self, path: Path) -> Path:
        # 每次文件操作都重复校验，阻止符号链接或调用方路径逃逸。
        candidate = Path(path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise OfflineRunnerFailure("path_outside_temp_root") from exc
        return candidate

    def download(self, asset_reference: str, destination: Path) -> None:
        # asset_reference 只验证为字符串；离线 runner 从不解析或访问它。
        if not isinstance(asset_reference, str) or not asset_reference:
            raise OfflineRunnerFailure("invalid_asset_reference")
        if "download_failed" in self.failures:
            raise OfflineRunnerFailure("download_failed")
        target = self._guard_path(destination)
        target.write_bytes(self.fixture_bytes)

    def sha256(self, binary_path: Path) -> str:
        # 摘要由标准库对本地 fixture 计算，不启动 shell 或外部命令。
        if "sha_command_failed" in self.failures:
            raise OfflineRunnerFailure("sha_command_failed")
        source = self._guard_path(binary_path)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        # mismatch 注入仍返回合法形状，从而精确测试 compare 边界。
        if "sha_mismatch" in self.failures:
            return "0" * 64 if digest != "0" * 64 else "1" * 64
        return digest

    def chmod(self, binary_path: Path) -> None:
        # chmod 仅作用于临时 fixture，不接触 PATH 或系统安装目录。
        if "chmod_failed" in self.failures:
            raise OfflineRunnerFailure("chmod_failed")
        self._guard_path(binary_path).chmod(0o700)

    def version(self, binary_path: Path) -> str:
        # dry gate 不执行 fixture 二进制，只返回受控版本 stub。
        if "version_execution_failed" in self.failures:
            raise OfflineRunnerFailure("version_execution_failed")
        self._guard_path(binary_path)
        if "version_mismatch" in self.failures:
            return "cloudflared version 1900.1.1"
        return f"cloudflared version {self.fixture_version}"


def _is_ordered_prefix(completed_stages: Sequence[str]) -> bool:
    # tuple 比较同时拒绝重复、跳级、回退和未知阶段。
    prefix = tuple(completed_stages)
    return prefix == STAGES[: len(prefix)]


def advance_stage(completed_stages: Sequence[str], stage: str) -> tuple[str, ...]:
    """只允许把状态推进到紧邻的下一个阶段。"""

    # 先验证旧状态，避免在已经污染的列表上继续前进。
    if not _is_ordered_prefix(completed_stages):
        raise SafeStageError("invalid_stage_transition")
    next_index = len(completed_stages)
    # 完成后再推进、重复或跳级都统一映射为安全枚举。
    if next_index >= len(STAGES) or stage != STAGES[next_index]:
        raise SafeStageError("invalid_stage_transition")
    return (*tuple(completed_stages), stage)


def _validate_release_metadata(release_metadata: Mapping[str, Any]) -> tuple[str, str]:
    # 只接受精确 provider/architecture/asset，避免宽松匹配误接其他包。
    if release_metadata.get("provider") != OFFICIAL_PROVIDER:
        raise SafeStageError("invalid_stage_transition")
    if release_metadata.get("architecture") != OFFICIAL_ARCHITECTURE:
        raise SafeStageError("invalid_stage_transition")
    if release_metadata.get("asset_name") != OFFICIAL_ASSET_NAME:
        raise SafeStageError("invalid_stage_transition")
    version = release_metadata.get("version")
    # version 必须是字符串且符合官方现有年月版本形状。
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise SafeStageError("invalid_stage_transition")
    asset_reference = release_metadata.get("asset_reference")
    expected_reference = f"{OFFICIAL_RELEASE_PREFIX}{version}/{OFFICIAL_ASSET_NAME}"
    # 精确比较同时拒绝 userinfo、query、fragment 和非官方 owner。
    if not isinstance(asset_reference, str) or asset_reference != expected_reference:
        raise SafeStageError("invalid_stage_transition")
    digest_value = release_metadata.get("digest")
    # 摘要原文只在内存中使用，build_artifact 没有对应输出字段。
    if not isinstance(digest_value, str):
        raise SafeStageError("invalid_stage_transition")
    digest_match = DIGEST_RE.fullmatch(digest_value)
    if digest_match is None:
        raise SafeStageError("invalid_stage_transition")
    return asset_reference, digest_match.group(1)


def _validate_local_runner(runner: object) -> LocalFixtureRunner:
    # 限制为受控实现，不能靠一个可伪造的 offline 布尔值放行任意 runner。
    if type(runner) is not LocalFixtureRunner or runner.offline_only is not True:
        raise SafeStageError("invalid_stage_transition")
    temporary_root = Path(tempfile.gettempdir()).resolve()
    # runner root 必须位于系统临时根且已经存在，避免写入仓库或用户目录。
    try:
        runner.root.relative_to(temporary_root)
    except ValueError as exc:
        raise SafeStageError("invalid_stage_transition") from exc
    if not runner.root.is_dir():
        raise SafeStageError("invalid_stage_transition")
    return runner


def build_artifact(
    completed_stages: Sequence[str],
    failure_reason: str | None,
    official_provenance_contract_checked: bool,
) -> dict[str, Any]:
    """仅用固定白名单字段构造成功或 fail-closed artifact。"""

    safe_stages = tuple(completed_stages)
    safe_reason = failure_reason
    # 非法前缀不能被反射到输出，统一退回空前缀和安全枚举。
    if not _is_ordered_prefix(safe_stages):
        safe_stages = ()
        safe_reason = "invalid_stage_transition"
    if safe_reason is not None and safe_reason not in FAILURE_REASONS:
        safe_reason = "invalid_stage_transition"
    # 只有完整七阶段、无失败且 metadata 合同已检查才能通过。
    passed = (
        safe_stages == STAGES
        and safe_reason is None
        and official_provenance_contract_checked is True
    )
    if not passed and safe_reason is None:
        safe_reason = "invalid_stage_transition"
    next_stage = None if len(safe_stages) == len(STAGES) else STAGES[len(safe_stages)]
    # 以下字典是完整输出白名单，不合并调用方字典或异常上下文。
    return {
        "schema": SCHEMA,
        "provider_runtime_preflight_status": (
            "passed_offline_dry_gate" if passed else "blocked_offline_dry_gate"
        ),
        "completed_stages": list(safe_stages),
        "last_reached_stage": safe_stages[-1] if safe_stages else None,
        "next_expected_stage": next_stage,
        "failure_reason": safe_reason,
        "proof_boundary": PROOF_BOUNDARY,
        "official_provenance_contract_checked": official_provenance_contract_checked is True,
        "network_access_attempted": False,
        "ssh_attempted": False,
        "tunnel_start_attempt_count": 0,
        "public_capture_count": 0,
        "public_probe_attempt_count": 0,
        "current_run_artifact_delta": False,
        "external_artifact_delta": False,
        "live_control_delta": False,
        "user_action_delta": False,
        "production_ready": False,
        "mission_objective_0_satisfied": False,
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
    }


def _blocked(completed_stages: Sequence[str], reason: str, checked: bool) -> dict[str, Any]:
    # 单一出口保证每种异常都经过同一白名单构造器。
    return build_artifact(completed_stages, reason, checked)


def run_provider_runtime_preflight(
    release_metadata: Mapping[str, Any], runner: object
) -> dict[str, Any]:
    """执行纯本地 preflight，并返回脱敏阶段诊断。"""

    completed: tuple[str, ...] = ()
    # metadata 与 runner 隔离先于 download_started，非法输入不能伪造执行事实。
    try:
        asset_reference, expected_digest = _validate_release_metadata(release_metadata)
        local_runner = _validate_local_runner(runner)
    except (SafeStageError, AttributeError, TypeError, ValueError):
        return _blocked(completed, "invalid_stage_transition", False)
    contract_checked = True
    binary_path = local_runner.root / "provider-runtime-fixture"
    # 每个 try 块只覆盖一个阶段，失败位置因此保持确定且可解释。
    try:
        completed = advance_stage(completed, "download_started")
        local_runner.download(asset_reference, binary_path)
        completed = advance_stage(completed, "download_completed")
    except Exception:
        return _blocked(completed, "download_failed", contract_checked)
    # SHA 命令成功和 SHA 比对成功是两个独立安全边界。
    try:
        actual_digest = local_runner.sha256(binary_path)
        if re.fullmatch(r"[0-9a-f]{64}", actual_digest) is None:
            raise OfflineRunnerFailure("sha_output_invalid")
        completed = advance_stage(completed, "sha_command_completed")
    except Exception:
        return _blocked(completed, "sha_command_failed", contract_checked)
    # 常量时间比较避免未来接入真实摘要时引入可观察的早退差异。
    if not hmac.compare_digest(actual_digest, expected_digest):
        return _blocked(completed, "sha_mismatch", contract_checked)
    try:
        completed = advance_stage(completed, "sha_matched")
        local_runner.chmod(binary_path)
        completed = advance_stage(completed, "chmod_completed")
    except SafeStageError:
        return _blocked(completed, "invalid_stage_transition", contract_checked)
    except Exception:
        return _blocked(completed, "chmod_failed", contract_checked)
    # version 执行成功与 version 内容匹配同样保持两个阶段。
    try:
        version_output = local_runner.version(binary_path)
        completed = advance_stage(completed, "version_executed")
    except SafeStageError:
        return _blocked(completed, "invalid_stage_transition", contract_checked)
    except Exception:
        return _blocked(completed, "version_execution_failed", contract_checked)
    # 输出原文不进入 artifact，只用 metadata version 做内存内判断。
    version = str(release_metadata["version"])
    if version not in version_output:
        return _blocked(completed, "version_mismatch", contract_checked)
    try:
        completed = advance_stage(completed, "version_matched")
    except SafeStageError:
        return _blocked(completed, "invalid_stage_transition", contract_checked)
    return build_artifact(completed, None, contract_checked)


def _offline_fixture() -> tuple[bytes, dict[str, str]]:
    # 内容不是可执行 binary，只用于 deterministic 摘要和版本合同验证。
    fixture_bytes = b"rober-o5-offline-provider-runtime-fixture-v1\n"
    version = "2026.7.1"
    digest = hashlib.sha256(fixture_bytes).hexdigest()
    # raw reference 和 digest 只存在于进程内 metadata，不写入最终 JSON。
    metadata = {
        "provider": OFFICIAL_PROVIDER,
        "architecture": OFFICIAL_ARCHITECTURE,
        "asset_name": OFFICIAL_ASSET_NAME,
        "version": version,
        "asset_reference": f"{OFFICIAL_RELEASE_PREFIX}{version}/{OFFICIAL_ASSET_NAME}",
        "digest": f"sha256:{digest}",
    }
    return fixture_bytes, metadata


def run_offline_dry_gate() -> dict[str, Any]:
    """在自动回收的临时目录中运行 happy-path dry gate。"""

    fixture_bytes, metadata = _offline_fixture()
    # TemporaryDirectory 保证 fixture 不成为仓库或系统残留。
    with tempfile.TemporaryDirectory(prefix="rober-o5-preflight-") as directory:
        runner = LocalFixtureRunner(Path(directory), fixture_bytes, metadata["version"])
        return run_provider_runtime_preflight(metadata, runner)


def _parse_args() -> argparse.Namespace:
    # CLI 刻意不提供 SSH、URL、tunnel、relay 或 control 参数。
    parser = argparse.ArgumentParser(description="O5 provider runtime offline stage diagnostics")
    parser.add_argument("--offline-dry-gate", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    # CLI 唯一执行路径是本地 fixture dry gate。
    args = _parse_args()
    artifact = run_offline_dry_gate()
    # 输出 JSON 只包含 build_artifact 的固定白名单字段。
    args.output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if artifact["provider_runtime_preflight_status"] == "passed_offline_dry_gate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
