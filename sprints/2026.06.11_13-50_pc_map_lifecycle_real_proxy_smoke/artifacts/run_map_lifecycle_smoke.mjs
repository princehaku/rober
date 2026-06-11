import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const artifactDir = new URL(".", import.meta.url).pathname;
const workstationBaseUrl = process.env.WORKSTATION_BASE_URL ?? "http://127.0.0.1:18790";
const robotBaseUrl = process.env.ROBOT_BASE_URL ?? "http://192.168.1.11:8787";
const mapName = process.env.MAP_NAME ?? "pc_map_lifecycle_20260611_1350";
const startedAt = new Date().toISOString();

async function callStep(id, method, path, body) {
  const url = `${workstationBaseUrl}${path}?baseUrl=${encodeURIComponent(robotBaseUrl)}`;
  const response = await fetch(url, {
    method,
    headers: method === "POST" ? { "Content-Type": "application/json" } : undefined,
    body: method === "POST" ? JSON.stringify(body ?? {}) : undefined,
  });
  const text = await response.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    json = null;
  }
  const step = {
    id,
    requested_at: new Date().toISOString(),
    workstation_url: url,
    method,
    request_body: method === "POST" ? body ?? {} : null,
    http_status: response.status,
    ok: response.ok,
    json_parse_ok: json !== null,
    response: json,
    raw_text: json === null ? text.slice(0, 2000) : "",
  };
  writeFileSync(resolve(artifactDir, `${id}.json`), `${JSON.stringify(step, null, 2)}\n`);
  return step;
}

function fieldValue(step, key) {
  return step.response && Object.prototype.hasOwnProperty.call(step.response, key) ? step.response[key] : null;
}

function forbiddenTrueFields(step) {
  const fields = [
    "safe_to_control",
    "delivery_success",
    "primary_actions_enabled",
    "robot_control_executed",
    "sends_motion_commands",
    "publishes_cmd_vel",
    "calls_base_manual",
    "uses_base_uart",
  ];
  return fields.filter((field) => fieldValue(step, field) === true);
}

const steps = [];
steps.push(await callStep("01_map_list_before", "GET", "/api/robot-control/map/list"));
steps.push(await callStep("02_map_start", "POST", "/api/robot-control/map/start", { map_name: mapName }));
steps.push(await callStep("03_map_save", "POST", "/api/robot-control/map/save", { map_name: mapName }));
steps.push(await callStep("04_map_list_after", "GET", "/api/robot-control/map/list"));
steps.push(
  await callStep("05_map_save_unknown_field_reject", "POST", "/api/robot-control/map/save", {
    map_name: mapName,
    arbitrary_endpoint: "/api/base/manual",
  }),
);

const reset = {
  id: "06_map_reset",
  status: "not_attempted_by_safety_boundary",
  reason: "destructive reset can remove or disturb existing map/runtime state; task instructed default not to test reset unless confirmed safe.",
};
writeFileSync(resolve(artifactDir, "06_map_reset_not_attempted.json"), `${JSON.stringify(reset, null, 2)}\n`);

const summary = {
  schema: "trashbot.pc_workstation.map_lifecycle_real_proxy_smoke.v1",
  started_at: startedAt,
  finished_at: new Date().toISOString(),
  workstation_base_url: workstationBaseUrl,
  robot_base_url: robotBaseUrl,
  map_name: mapName,
  reset,
  safety_boundary: {
    safe_to_control: false,
    delivery_success: false,
    primary_actions_enabled: false,
    robot_control_executed: false,
    sends_motion_commands: false,
    publishes_cmd_vel: false,
    calls_base_manual: false,
    uses_base_uart: false,
    calls_base_manual_endpoint_attempted: false,
    cmd_vel_publish_attempted: false,
  },
  fixed_proxy_checks: steps.map((step) => ({
    id: step.id,
    http_status: step.http_status,
    proxy_status: fieldValue(step, "proxy_status"),
    remote_endpoint: fieldValue(step, "remote_endpoint"),
    remote_method: fieldValue(step, "remote_method"),
    remote_http_status: fieldValue(step, "remote_http_status"),
    command_mode: fieldValue(step, "command_result")?.mode ?? null,
    command_executed: fieldValue(step, "command_result")?.executed ?? null,
    command_ok: fieldValue(step, "command_result")?.ok ?? null,
    failure_reason: fieldValue(step, "failure_reason"),
    blocked_reasons: fieldValue(step, "blocked_reasons"),
    hard_dangerous_true_fields: fieldValue(step, "hard_dangerous_true_fields"),
    forbidden_true_fields_observed: forbiddenTrueFields(step),
  })),
  result: {
    lifecycle_sequence_attempted: ["list_before", "start", "save", "list_after"],
    lifecycle_all_proxy_forwarded: steps.slice(0, 4).every((step) => fieldValue(step, "proxy_status") === "lifecycle_forwarded"),
    reject_smoke_passed:
      fieldValue(steps[4], "proxy_status") === "lifecycle_rejected" &&
      String(fieldValue(steps[4], "failure_reason") ?? "").includes("request_body_unknown_fields"),
    no_forbidden_true_fields_observed: steps.every((step) => forbiddenTrueFields(step).length === 0),
  },
};
writeFileSync(resolve(artifactDir, "map_lifecycle_smoke_summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
