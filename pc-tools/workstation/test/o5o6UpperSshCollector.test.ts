import { EventEmitter } from "node:events";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
// @ts-expect-error JS CLI script intentionally stays runnable by plain node.
import * as upperSshCollector from "../scripts/o5-o6-upper-ssh-collector.mjs";

const {
  buildCollectorPlan,
  buildDryRunResult,
  buildProbeInstallSshArgs,
  buildRemoteCommand,
  buildSshArgs,
  collectUpperSshArtifact,
} = upperSshCollector;

type FakeSpawnResult = {
  code: number;
  stdout?: string;
  stderr?: string;
};

type FakeSpawnCall = {
  args: string[];
  stdin: string;
};

type RemoteProbeFixture = {
  probe_status: string;
  blocked_reasons: string[];
  [key: string]: unknown;
};

function requireValue<T>(value: T | undefined, message: string): T {
  // 测试 helper 明确失败原因，避免 TypeScript 和运行时都把缺失调用吞成 undefined。
  if (value === undefined) {
    throw new Error(message);
  }
  return value;
}

function fakeSpawn(result: FakeSpawnResult) {
  return fakeSpawnSequence([result]).spawnImpl;
}

function fakeSpawnSequence(results: FakeSpawnResult[]) {
  const fallbackResult = requireValue(results[results.length - 1], "fake_spawn_sequence_requires_at_least_one_result");
  const calls: FakeSpawnCall[] = [];
  const spawnImpl = (_binary: string, args: string[]) => {
    // fake spawn 只模拟 stdout/stderr/close 事件，避免单测真实连接上位机。
    const result = results[calls.length] ?? fallbackResult;
    const call: FakeSpawnCall = { args, stdin: "" };
    calls.push(call);
    const child = new EventEmitter() as EventEmitter & {
      stdout: EventEmitter;
      stderr: EventEmitter;
      stdin: { end: (value?: string) => void };
    };
    child.stdout = new EventEmitter();
    child.stderr = new EventEmitter();
    child.stdin = {
      end: (value?: string) => {
        // fallback 的 stdin 只应承载本地 probe 源码，不应包含 token 或 operator secret。
        call.stdin += value ?? "";
      },
    };
    queueMicrotask(() => {
      if (result.stdout) {
        child.stdout.emit("data", result.stdout);
      }
      if (result.stderr) {
        child.stderr.emit("data", result.stderr);
      }
      child.emit("close", result.code);
    });
    return child;
  };
  return { spawnImpl, calls };
}

function remoteProbeFixture(): RemoteProbeFixture {
  // 远端 fixture 模拟 Python stdlib probe 的脱敏 JSON，不包含真实 URL、token 或硬件路径。
  return {
    schema: "trashbot.o5_o6.external_live_probe.v1",
    runner: "python_stdlib",
    executed_at: "2026-06-04T02:30:00Z",
    probe_status: "observed_fail_closed_contract",
    viewpoint: "external_or_upper_computer_readonly",
    pc_base_url: "http://loopback",
    cloud_base_url: "https://redacted",
    token_status: "present",
    credentials_redacted: true,
    tls_evidence: {
      tls_status: "observed",
      scheme: "https",
      hostname_redacted: "sha256:abcdef123456",
      host_status: "redacted_public_or_custom_host",
      port: 443,
      tls_observed: true,
      tls_version: "TLSv1.3",
      cipher_status: "present",
      cipher_bits: 256,
      certificate: {
        not_before: "Jan 01 00:00:00 2026 GMT",
        not_after: "Jan 01 00:00:00 2027 GMT",
        certificate_expiry_days: 200,
        issuer_summary: { field_count: 1, common_name_status: "present", organization_status: "absent", country_status: "absent" },
        subject_summary: { field_count: 1, common_name_status: "present", organization_status: "absent", country_status: "absent" },
        subject_alt_name_summary: { dns_name_count: 1, ip_address_count: 0 },
      },
      verification_error: "none",
    },
    endpoints: [
      {
        name: "o5_readiness",
        endpoint: "/api/o5/readiness/health",
        reachable: true,
        http_status: 200,
        schema: "trashbot.o5.readiness_health.v1",
        schema_status: "matched",
        contract_status: "observed_fail_closed_contract",
        failure_category: "none",
        blocked_reasons: [],
        dangerous_true_fields: [],
        sensitive_markers: [],
      },
      {
        name: "pc_aggregate",
        endpoint: "/api/o5-o6/cloud-relay-health?baseUrl=https%3A%2F%2Fredacted",
        reachable: false,
        http_status: null,
        schema: "not_loaded",
        schema_status: "not_loaded",
        contract_status: "fail_closed",
        failure_category: "base_url_not_configured",
        blocked_reasons: ["base_url_not_configured"],
        dangerous_true_fields: [],
        sensitive_markers: [],
      },
    ],
    summary: {
      endpoint_count: 2,
      reachable_count: 1,
      schema_matched_count: 1,
      fail_closed_count: 1,
      safe_to_control: false,
      sends_commands: false,
      robot_control_executed: false,
      delivery_success: false,
      primary_actions_enabled: false,
      reads_hardware: false,
    },
    safety_policy: {
      method_allowlist: ["GET"],
      endpoint_allowlist: ["/api/o5/readiness/health", "/api/o6/archive/health", "/api/o5-o6/cloud-relay-health"],
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "environment_only",
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
    },
    key_false_fields: ["safe_to_control=false", "sends_commands=false", "robot_control_executed=false", "reads_hardware=false"],
    blocked_reasons: [],
    not_proven: ["real_4g_sim_not_proven"],
    safe_to_control: false,
    sends_commands: false,
    reads_hardware: false,
    robot_control_executed: false,
    delivery_success: false,
    primary_actions_enabled: false,
  };
}

describe("O5/O6 upper SSH collector", () => {
  it("builds a read-only ssh command without bearer tokens or robot control paths", () => {
    // 命令构造是安全边界核心：只运行 Python probe，不 POST、不碰机器人控制路径。
    const plan = buildCollectorPlan({
      argv: [
        "--dry-run",
        "--ssh-target",
        "root@192.168.1.11",
        "--ssh-port",
        "37878",
        "--pc-base-url",
        "http://127.0.0.1:8787",
        "--cloud-base-url",
        "https://example.invalid",
      ],
      env: { TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN: "secret-fixture" } as NodeJS.ProcessEnv,
    });
    const command = buildRemoteCommand(plan);
    const args = buildSshArgs(plan);
    const serialized = JSON.stringify({ command, args });

    expect(args).toContain("root@192.168.1.11");
    expect(args).toContain("37878");
    expect(command).toContain("python3 'cloud-relay/scripts/o5_o6_external_live_probe.py' --once-json");
    expect(command).toContain("--cloud-base-url 'https://example.invalid'");
    expect(serialized).not.toContain("secret-fixture");
    expect(serialized).not.toContain("/robots/");
    expect(serialized).not.toContain("/cmd_vel");
    expect(serialized.toLowerCase()).not.toContain("post ");
  });

  it("dry-run prints machine-readable safety metadata and writes no artifact", () => {
    // dry-run 只能证明命令规划，不得污染 acceptance queue 默认 artifact。
    const plan = buildCollectorPlan({
      argv: ["--dry-run", "--cloud-base-url", "https://example.invalid"],
      env: {} as NodeJS.ProcessEnv,
    });
    const dryRun = buildDryRunResult(plan);

    expect(dryRun.schema).toBe("trashbot.o5_o6.upper_ssh_collector.v1");
    expect(dryRun.artifact_written).toBe(false);
    expect(dryRun.safety_policy).toMatchObject({
      no_post: true,
      no_robot_control: true,
      no_hardware_read: true,
      forbidden_paths: ["/robots/*", "/cmd_vel"],
      bearer_source: "remote_environment_only",
    });
    expect(dryRun.stdin_fallback).toMatchObject({
      supported: true,
      execution_mode: "stdin_fallback",
      streams_local_probe_over_ssh_stdin: true,
      remote_file_write_executed: false,
      contains_bearer_token: false,
    });
    expect(dryRun.pc_base_url_contract).toMatchObject({
      configured_for_upper_ssh: false,
      source: "absent",
      blocked_reason: "pc_base_url_not_configured_for_upper_ssh",
    });
    expect(dryRun.pc_base_url_contract.next_action).toContain("--pc-base-url http://<pc-workstation-host>:8787");
    expect(dryRun.blocked_reasons).toContain("pc_base_url_not_configured_for_upper_ssh");
    expect(JSON.stringify(dryRun.stdin_fallback.ssh_args)).toContain("python3 - --once-json");
    expect(JSON.stringify(dryRun.stdin_fallback.ssh_args)).toContain("--pc-base-url ''");
    expect(JSON.stringify(dryRun.stdin_fallback.ssh_args)).not.toContain("http://127.0.0.1:8787");
    expect(JSON.stringify(dryRun)).not.toContain("Bearer");
  });

  it("dry-run classifies remote probe sync without executing ssh or writing remote files", () => {
    // 新同步模式必须显式请求；dry-run 只展示写入边界，不能偷偷 SSH 或落 artifact。
    const plan = buildCollectorPlan({
      argv: [
        "--dry-run",
        "--sync-remote-probe",
        "--ssh-command",
        "ssh root@192.168.1.11 -p 37878",
        "--cloud-base-url",
        "https://example.invalid",
      ],
      env: { TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN: "local-secret-not-forwarded" } as NodeJS.ProcessEnv,
    });
    const dryRun = buildDryRunResult(plan);
    const syncArgs = JSON.stringify(buildProbeInstallSshArgs(plan));

    expect(dryRun.sync_remote_probe).toMatchObject({
      requested: true,
      status: "dry_run_not_executed",
      mode: "ssh_stdin_write",
      allowed_write_scope: "single_probe_script_only",
      exact_final_path_only: true,
      target_allowed: true,
      dry_run_no_ssh: true,
      dry_run_no_write: true,
      ssh_executed: false,
      remote_file_write_attempted: false,
      remote_file_write_executed: false,
      contains_bearer_token: false,
      post_executed: false,
      robots_path_accessed: false,
      cmd_vel_accessed: false,
      hardware_read_executed: false,
      robot_control_executed: false,
    });
    expect(dryRun.preflight.checks.map((check: { id: string }) => check.id)).toContain("remote_probe_sync");
    expect(dryRun.preflight.failure_classification).toContain("remote_probe_sync_not_executed_dry_run");
    expect(dryRun.blocked_reasons).toContain("remote_probe_sync_not_executed_dry_run");
    expect(syncArgs).toContain("test -d 'cloud-relay/scripts'");
    expect(syncArgs).toContain("cat > 'cloud-relay/scripts/o5_o6_external_live_probe.py'");
    expect(syncArgs).toContain("test -s 'cloud-relay/scripts/o5_o6_external_live_probe.py'");
    expect(syncArgs).not.toContain(".o5_o6_external_live_probe.py.tmp");
    expect(syncArgs).not.toContain("py_compile");
    expect(syncArgs).not.toContain("mkdir -p");
    expect(JSON.stringify(dryRun)).not.toContain("local-secret-not-forwarded");
    expect(syncArgs).not.toContain("/robots/");
    expect(syncArgs).not.toContain("/cmd_vel");
  });

  it("parses operator ssh command input and classifies preflight gaps without executing ssh", () => {
    // operator 可直接粘贴 SSH 入口；dry-run 只解析 target/port 并输出缺口分类，不触发真实连接。
    const plan = buildCollectorPlan({
      argv: [
        "--dry-run",
        "--ssh-command",
        "ssh root@192.168.1.11 -p 37878",
        "--cloud-base-url",
        "https://example.invalid",
      ],
      env: { TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN: "local-secret-not-forwarded" } as NodeJS.ProcessEnv,
    });
    const dryRun = buildDryRunResult(plan);

    expect(plan.sshTarget).toBe("root@192.168.1.11");
    expect(plan.sshPort).toBe("37878");
    expect(plan.sshTargetSource).toBe("ssh_command");
    expect(plan.sshPortSource).toBe("ssh_command");
    expect(dryRun.preflight).toMatchObject({
      schema: "trashbot.o5_o6.upper_ssh_collector_preflight.v1",
      status: "blocked",
      accepts_ssh_command_input: true,
      remote_bearer_token_local_hint: "local_env_present_not_forwarded",
      execution_policy: {
        dry_run_no_ssh: true,
        network_probe_executed: false,
        post_executed: false,
        robots_path_accessed: false,
        cmd_vel_accessed: false,
        hardware_read_executed: false,
        robot_control_executed: false,
      },
    });
    expect(dryRun.preflight.checks.map((check: { id: string }) => check.id)).toEqual([
      "ssh_target",
      "ssh_port",
      "pc_base_url",
      "cloud_base_url",
      "remote_bearer_token",
      "remote_root",
      "remote_probe_script",
    ]);
    expect(dryRun.preflight.failure_classification).toContain("pc_base_url_not_configured_for_upper_ssh");
    expect(dryRun.preflight.failure_classification).toContain("remote_bearer_token_not_verified_by_pc_preflight");
    expect(dryRun.preflight.failure_classification).toContain("remote_root_not_verified_by_pc_preflight");
    expect(dryRun.preflight.failure_classification).toContain("remote_probe_script_not_verified_by_pc_preflight");
    expect(dryRun.failure_classification).toEqual(dryRun.preflight.failure_classification);
    expect(JSON.stringify(dryRun)).not.toContain("local-secret-not-forwarded");
    expect(JSON.stringify(dryRun.ssh_command.args)).not.toContain("/robots/");
    expect(JSON.stringify(dryRun.ssh_command.args)).not.toContain("/cmd_vel");
    expect(JSON.stringify(dryRun.stdin_fallback.ssh_args)).not.toContain("/robots/");
    expect(JSON.stringify(dryRun.stdin_fallback.ssh_args)).not.toContain("/cmd_vel");
  });

  it("keeps PC aggregate blocked when upper SSH has no explicit PC workstation base URL", async () => {
    // 未显式配置 PC workstation URL 时，远端 probe 不应默认访问上位机自己的 127.0.0.1。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-pc-base-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--output", output],
      env: {} as NodeJS.ProcessEnv,
    });
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fakeSpawn({ code: 2, stdout: `${JSON.stringify(remoteProbeFixture())}\n` }),
    });
    const written = JSON.parse(await readFile(output, "utf8"));
    const pcAggregate = written.endpoints.find((endpoint: { name: string }) => endpoint.name === "pc_aggregate");

    expect(JSON.stringify(buildSshArgs(plan))).toContain("--pc-base-url ''");
    expect(JSON.stringify(buildSshArgs(plan))).not.toContain("http://127.0.0.1:8787");
    expect(result.pc_base_url).toBe("not_configured_for_upper_ssh");
    expect(result.blocked_reasons).toContain("pc_base_url_not_configured_for_upper_ssh");
    expect(pcAggregate.failure_category).toBe("pc_base_url_not_configured_for_upper_ssh");
    expect(pcAggregate.blocked_reasons).toContain("pc_base_url_not_configured_for_upper_ssh");
    expect(written.ssh_collection).toMatchObject({
      pc_base_url_configured_for_upper_ssh: false,
      pc_base_url_source: "absent",
    });
    expect(written.ssh_collection.pc_base_url_next_action).toContain("ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL");
    expect(written.safe_to_control).toBe(false);
    expect(written.sends_commands).toBe(false);
    expect(written.reads_hardware).toBe(false);
  });

  it("decorates a successful remote Python probe and writes the queue-consumable artifact", async () => {
    // 成功路径保留 external probe schema，因此现有 artifact loader 无需新增 parser。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--pc-base-url", "http://192.168.1.50:8787", "--output", output],
      env: {} as NodeJS.ProcessEnv,
    });
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fakeSpawn({ code: 0, stdout: `${JSON.stringify(remoteProbeFixture())}\n` }),
    });
    const written = JSON.parse(await readFile(output, "utf8"));

    expect(result.schema).toBe("trashbot.o5_o6.external_live_probe.v1");
    expect(result.runner).toBe("pc_upper_ssh_collector+python_stdlib");
    expect(result.source_host_role).toBe("upper_computer");
    expect(result.viewpoint).toBe("upper_computer_via_pc_ssh_readonly");
    expect(result.ssh_collection).toMatchObject({
      status: "collected",
      execution_mode: "installed_script",
      fallback_used: false,
      target_host_role: "upper_computer",
      pc_base_url_configured_for_upper_ssh: true,
      pc_base_url_source: "cli",
      command_boundary: {
        post_executed: false,
        robots_path_accessed: false,
        cmd_vel_accessed: false,
        hardware_read_executed: false,
        robot_control_executed: false,
      },
    });
    expect(written.runner).toBe("pc_upper_ssh_collector+python_stdlib");
    expect(written.safety_policy.forbidden_paths).toEqual(["/robots/*", "/cmd_vel"]);
    expect(written.ssh_collection.command_boundary.robots_path_accessed).toBe(false);
    expect(written.ssh_collection.command_boundary.cmd_vel_accessed).toBe(false);
  });

  it("uses ssh stdin fallback when the remote root exists but probe script is missing", async () => {
    // exit 42 代表已经进入远端 repo root；此时应优先用 stdin fallback，而不是要求 operator 先写远端文件。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-stdin-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--pc-base-url", "http://192.168.1.50:8787", "--output", output],
      env: { TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN: "secret-fixture" } as NodeJS.ProcessEnv,
    });
    const remoteProbe = remoteProbeFixture();
    remoteProbe.probe_status = "fail_closed";
    remoteProbe.blocked_reasons = ["network_or_service_unreachable"];
    const fake = fakeSpawnSequence([
      { code: 42, stderr: "missing script at /root/rober" },
      { code: 2, stdout: `${JSON.stringify(remoteProbe)}\n` },
    ]);
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fake.spawnImpl,
    });
    const written = JSON.parse(await readFile(output, "utf8"));

    expect(fake.calls).toHaveLength(2);
    const fallbackCall = requireValue(fake.calls[1], "stdin_fallback_spawn_call_missing");
    expect(JSON.stringify(fallbackCall.args)).toContain("python3 - --once-json");
    expect(fallbackCall.stdin).toContain("SCHEMA = \"trashbot.o5_o6.external_live_probe.v1\"");
    expect(fallbackCall.stdin).not.toContain("secret-fixture");
    expect(result.probe_status).toBe("fail_closed");
    expect(result.ssh_collection).toMatchObject({
      status: "collected",
      execution_mode: "stdin_fallback",
      attempted_execution_modes: ["installed_script", "stdin_fallback"],
      fallback_used: true,
      fallback_reason: "remote_repo_present_but_probe_script_missing",
      remote_exit_code: 2,
    });
    expect(written.collector_execution_mode).toBe("stdin_fallback");
    expect(written.blocked_reasons).toContain("network_or_service_unreachable");
    expect(written.safe_to_control).toBe(false);
    expect(written.sends_commands).toBe(false);
    expect(written.reads_hardware).toBe(false);
    expect(written.robot_control_executed).toBe(false);
  });

  it("can sync the local probe over ssh stdin before running the installed remote script", async () => {
    // sync 模式只写固定 probe 脚本，然后复用 installed_script 采集路径，消除缺脚本 blocker。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-sync-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: [
        "--sync-remote-probe",
        "--cloud-base-url",
        "https://example.invalid",
        "--pc-base-url",
        "http://192.168.1.50:8787",
        "--output",
        output,
      ],
      env: { TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN: "secret-fixture" } as NodeJS.ProcessEnv,
    });
    const remoteProbe = remoteProbeFixture();
    remoteProbe.probe_status = "fail_closed";
    remoteProbe.blocked_reasons = ["network_or_service_unreachable"];
    const fake = fakeSpawnSequence([
      { code: 0 },
      { code: 2, stdout: `${JSON.stringify(remoteProbe)}\n` },
    ]);
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fake.spawnImpl,
    });
    const written = JSON.parse(await readFile(output, "utf8"));
    const syncCall = requireValue(fake.calls[0], "sync_remote_probe_spawn_call_missing");
    const installedCall = requireValue(fake.calls[1], "installed_script_spawn_call_missing");

    expect(fake.calls).toHaveLength(2);
    expect(JSON.stringify(syncCall.args)).toContain("test -d 'cloud-relay/scripts'");
    expect(JSON.stringify(syncCall.args)).toContain("cat > 'cloud-relay/scripts/o5_o6_external_live_probe.py'");
    expect(JSON.stringify(syncCall.args)).toContain("test -s 'cloud-relay/scripts/o5_o6_external_live_probe.py'");
    expect(JSON.stringify(syncCall.args)).not.toContain(".o5_o6_external_live_probe.py.tmp");
    expect(JSON.stringify(syncCall.args)).not.toContain("py_compile");
    expect(JSON.stringify(syncCall.args)).not.toContain("mkdir -p");
    expect(syncCall.stdin).toContain("SCHEMA = \"trashbot.o5_o6.external_live_probe.v1\"");
    expect(syncCall.stdin).not.toContain("secret-fixture");
    expect(JSON.stringify(installedCall.args)).toContain("python3 'cloud-relay/scripts/o5_o6_external_live_probe.py' --once-json");
    expect(result.ssh_collection).toMatchObject({
      status: "collected",
      execution_mode: "installed_script",
      attempted_execution_modes: ["sync_remote_probe", "installed_script"],
      fallback_used: false,
      remote_probe_sync: {
        requested: true,
        status: "synced",
        exact_final_path_only: true,
        ssh_executed: true,
        remote_file_write_attempted: true,
        remote_file_write_executed: true,
        contains_bearer_token: false,
      },
      command_boundary: {
        remote_file_write_attempted: true,
        remote_file_write_executed: true,
        remote_write_scope: "single_probe_script_only",
        passes_bearer_token_via_cli_or_ssh_args: false,
        post_executed: false,
        robots_path_accessed: false,
        cmd_vel_accessed: false,
        hardware_read_executed: false,
        robot_control_executed: false,
      },
    });
    expect(result.viewpoint).toBe("upper_computer_via_pc_ssh_probe_sync_then_readonly_probe");
    expect(written.collector_execution_mode).toBe("installed_script");
    expect(written.viewpoint).toBe("upper_computer_via_pc_ssh_probe_sync_then_readonly_probe");
    expect(written.blocked_reasons).not.toContain("remote_repo_present_but_probe_script_missing");
    expect(written.ssh_collection.remote_probe_sync.remote_target_ref).toBe("/root/rober/cloud-relay/scripts/o5_o6_external_live_probe.py");
    expect(written.safe_to_control).toBe(false);
    expect(written.sends_commands).toBe(false);
    expect(written.reads_hardware).toBe(false);
    expect(written.robot_control_executed).toBe(false);
  });

  it("writes a structured blocked artifact when ssh stdin fallback cannot execute", async () => {
    // fallback 失败时仍要落 external probe shape，避免 acceptance queue 失去机器可读 next_action。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-missing-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--pc-base-url", "http://192.168.1.50:8787", "--output", output],
      env: {} as NodeJS.ProcessEnv,
    });
    const fake = fakeSpawnSequence([
      { code: 42, stderr: "missing script at /root/rober" },
      { code: 127, stderr: "python3: not found" },
    ]);
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fake.spawnImpl,
    });
    const written = JSON.parse(await readFile(output, "utf8"));

    expect(result.probe_status).toBe("fail_closed");
    expect(result.blocked_reasons).toEqual(["ssh_stdin_fallback_probe_failed"]);
    expect(result.endpoints.every((endpoint: { contract_status: string }) => endpoint.contract_status === "fail_closed")).toBe(true);
    expect(written.ssh_collection.failure_category).toBe("ssh_stdin_fallback_probe_failed");
    expect(written.ssh_collection.execution_mode).toBe("stdin_fallback");
    expect(written.ssh_collection.fallback_reason).toBe("remote_repo_present_but_probe_script_missing");
    expect(written.ssh_collection.remote_path_override_supported).toBe(true);
    expect(written.ssh_collection.stdin_fallback_remote_write).toBe(false);
    expect(written.ssh_collection.next_action).toContain("remote python3");
    expect(written.safe_to_control).toBe(false);
    expect(written.sends_commands).toBe(false);
    expect(written.reads_hardware).toBe(false);
    expect(written.robot_control_executed).toBe(false);
  });
});
