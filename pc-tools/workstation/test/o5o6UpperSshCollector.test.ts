import { EventEmitter } from "node:events";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
// @ts-expect-error JS CLI script intentionally stays runnable by plain node.
import {
  buildCollectorPlan,
  buildDryRunResult,
  buildRemoteCommand,
  buildSshArgs,
  collectUpperSshArtifact,
} from "../scripts/o5-o6-upper-ssh-collector.mjs";

type FakeSpawnResult = {
  code: number;
  stdout?: string;
  stderr?: string;
};

function fakeSpawn(result: FakeSpawnResult) {
  return () => {
    // fake spawn 只模拟 stdout/stderr/close 事件，避免单测真实连接上位机。
    const child = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter };
    child.stdout = new EventEmitter();
    child.stderr = new EventEmitter();
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
}

function remoteProbeFixture() {
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
    ],
    summary: {
      endpoint_count: 1,
      reachable_count: 1,
      schema_matched_count: 1,
      fail_closed_count: 0,
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
    expect(JSON.stringify(dryRun)).not.toContain("Bearer");
  });

  it("decorates a successful remote Python probe and writes the queue-consumable artifact", async () => {
    // 成功路径保留 external probe schema，因此现有 artifact loader 无需新增 parser。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--output", output],
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
    expect(result.ssh_collection).toMatchObject({
      status: "collected",
      target_host_role: "upper_computer",
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

  it("writes a structured blocked artifact when the remote root exists but probe script is missing", async () => {
    // exit 42 代表已经进入远端 repo root；要把“路径存在但 probe 未同步”讲清楚，方便 operator 直接补文件或改 override。
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "rober-o5o6-upper-missing-"));
    const output = path.join(tempDir, "probe.json");
    const plan = buildCollectorPlan({
      argv: ["--cloud-base-url", "https://example.invalid", "--output", output],
      env: {} as NodeJS.ProcessEnv,
    });
    const result = await collectUpperSshArtifact({
      plan,
      spawnImpl: fakeSpawn({ code: 42, stderr: "missing script at /root/rober" }),
    });
    const written = JSON.parse(await readFile(output, "utf8"));

    expect(result.probe_status).toBe("fail_closed");
    expect(result.blocked_reasons).toEqual(["remote_repo_present_but_probe_script_missing"]);
    expect(result.endpoints.every((endpoint: { contract_status: string }) => endpoint.contract_status === "fail_closed")).toBe(true);
    expect(written.ssh_collection.failure_category).toBe("remote_repo_present_but_probe_script_missing");
    expect(written.ssh_collection.remote_path_override_supported).toBe(true);
    expect(written.ssh_collection.next_action).toContain("--remote-script/--remote-root");
    expect(written.safe_to_control).toBe(false);
    expect(written.sends_commands).toBe(false);
    expect(written.reads_hardware).toBe(false);
  });
});
