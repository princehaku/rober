import json
import os
import pathlib
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ros2_trashbot_behavior"))


def _unwritable_sqlite_path() -> str:
    """跨平台不可写路径：POSIX 用 /dev/null/…；Windows 用不存在父目录下的文件。"""
    import platform

    if platform.system() == "Windows":
        return str(
            pathlib.Path(tempfile.gettempdir())
            / "__rober_unwritable_parent__"
            / "__missing__"
            / "relay_state.sqlite"
        )
    return "/dev/null/relay_state.sqlite"


def _unwritable_json_state_path() -> str:
    import platform

    if platform.system() == "Windows":
        return str(
            pathlib.Path(tempfile.gettempdir())
            / "__rober_unwritable_parent__"
            / "__missing__"
            / "relay_state.json"
        )
    return "/dev/null/relay_state.json"

from ros2_trashbot_behavior.remote_cloud_relay import (  # noqa: E402
    BACKUP_RESTORE_EVIDENCE_BOUNDARY,
    CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
    CLOUD_DEPLOYMENT_READINESS_SCHEMA,
    CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
    CLOUD_DB_QUEUE_CONFIG_SCHEMA,
    CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
    CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
    CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
    CLOUD_EXTERNAL_PROBE_SCHEMA,
    CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY,
    CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA,
    CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
    CLOUD_WORKER_CUTOVER_DRAIN_EVIDENCE_BOUNDARY,
    CLOUD_WORKER_CUTOVER_DRAIN_SCHEMA,
    CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA,
    CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
    CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
    CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY,
    CREDENTIAL_ROTATION_PHONE_EVIDENCE_BOUNDARY,
    CREDENTIAL_ROTATION_SCHEMA,
    EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
    EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
    FileBackedRelayStore,
    NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
    NETWORK_RECOVERY_PHONE_EVIDENCE_BOUNDARY,
    NETWORK_RECOVERY_SCHEMA,
    OSS_CDN_BASE_URL,
    OSS_CDN_BUCKET,
    OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY,
    OSS_CDN_LIVE_PROBE_SCHEMA,
    OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
    OSS_CDN_MANIFEST_SCHEMA,
    OSS_CDN_PHONE_MANIFEST_EVIDENCE_BOUNDARY,
    OSS_CDN_REGION,
    PREFLIGHT_EVIDENCE_BOUNDARY,
    PROTOCOL_VERSION,
    PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY,
    PRODUCTION_STORE_QUEUE_PHONE_EVIDENCE_BOUNDARY,
    PRODUCTION_STORE_QUEUE_SCHEMA,
    PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY,
    PRODUCTION_RECOVERY_PHONE_EVIDENCE_BOUNDARY,
    PRODUCTION_RECOVERY_SCHEMA,
    PROVISIONING_AUDIT_EVIDENCE_BOUNDARY,
    PROVISIONING_AUDIT_PHONE_EVIDENCE_BOUNDARY,
    PROVISIONING_AUDIT_SCHEMA,
    QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY,
    QUEUE_ORDERING_DRILL_PHONE_EVIDENCE_BOUNDARY,
    QUEUE_ORDERING_DRILL_SCHEMA,
    SQLITE_EVIDENCE_BOUNDARY,
    SQLiteRelayStore,
    TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY,
    TRANSACTION_ISOLATION_PHONE_EVIDENCE_BOUNDARY,
    TRANSACTION_ISOLATION_SCHEMA,
    _sha256_checksum,
    backup_artifact_summary,
    backup_restore_drill_payload,
    build_credential_rotation_artifact_payload,
    build_phone_credential_rotation_summary,
    build_phone_production_store_queue_summary,
    build_phone_production_recovery_summary,
    build_oss_cdn_live_probe_payload,
    build_oss_cdn_manifest_payload,
    build_phone_network_recovery_summary,
    build_phone_oss_cdn_manifest_summary,
    build_phone_provisioning_audit_summary,
    build_phone_queue_ordering_drill_summary,
    build_phone_transaction_isolation_summary,
    build_cloud_deployment_readiness_artifact_payload,
    build_cloud_db_queue_config_artifact_payload,
    build_cloud_db_queue_external_probe_bundle_payload,
    build_cloud_external_probe_bundle_payload,
    build_cloud_public_ingress_tls_artifact_payload,
    build_external_evidence_intake_artifact_payload,
    build_cloud_worker_migration_rehearsal_artifact_payload,
    build_cloud_worker_cutover_drain_artifact_payload,
    cloud_deployment_readiness_artifact_summary,
    cloud_db_queue_config_artifact_summary,
    cloud_db_queue_external_probe_bundle_summary,
    cloud_external_probe_bundle_summary,
    cloud_public_ingress_tls_artifact_summary,
    build_production_store_queue_artifact_payload,
    build_production_recovery_artifact_payload,
    build_provisioning_audit_artifact_payload,
    build_queue_ordering_drill_artifact_payload,
    build_transaction_isolation_artifact_payload,
    build_server,
    credential_rotation_artifact_summary,
    create_credential_rotation_artifact,
    create_network_recovery_artifact,
    create_oss_cdn_live_probe_artifact,
    create_oss_cdn_manifest_artifact,
    create_production_store_queue_artifact,
    create_production_recovery_artifact,
    create_provisioning_audit_artifact,
    create_queue_ordering_drill_artifact,
    create_sqlite_backup_artifact,
    create_transaction_isolation_artifact,
    create_cloud_deployment_readiness_artifact,
    create_cloud_db_queue_config_artifact,
    create_cloud_db_queue_external_probe_bundle_artifact,
    create_cloud_external_probe_bundle_artifact,
    create_cloud_public_ingress_tls_artifact,
    create_external_evidence_intake_artifact,
    create_cloud_worker_migration_rehearsal_artifact,
    create_cloud_worker_cutover_drain_artifact,
    external_evidence_intake_artifact_summary,
    cloud_worker_migration_rehearsal_artifact_summary,
    cloud_worker_cutover_drain_artifact_summary,
    network_recovery_artifact_summary,
    network_recovery_drill_payload,
    oss_cdn_live_probe_summary,
    oss_cdn_manifest_summary,
    production_preflight_payload,
    production_recovery_artifact_summary,
    production_store_queue_artifact_summary,
    provisioning_audit_artifact_summary,
    queue_ordering_drill_artifact_summary,
    restore_sqlite_backup_artifact,
    transaction_isolation_artifact_summary,
)
from ros2_trashbot_behavior import remote_cloud_relay as relay_module  # noqa: E402


class RelayHttpClient:
    def __init__(self, base_url, token="phone-token"):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(self, method, path, payload=None, token=None, raw_body=None):
        data = None
        headers = {"Accept": "application/json"}
        active_token = self.token if token is None else token
        if active_token:
            headers["Authorization"] = f"Bearer {active_token}"
        if raw_body is not None:
            data = raw_body
            headers["Content-Type"] = "application/json"
        elif payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=2.0) as response:
                body = response.read().decode("utf-8") or "{}"
                return response.status, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") or "{}"
            return exc.code, json.loads(body)

    def raw_request(self, method, path, token=None):
        headers = {}
        active_token = self.token if token is None else token
        if active_token:
            headers["Authorization"] = f"Bearer {active_token}"
        request = urllib.request.Request(self.base_url + path, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=2.0) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()


class RemoteCloudRelayHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = pathlib.Path(self.tmp.name) / "relay_state.json"
        self.o6_state_path = pathlib.Path(self.tmp.name) / "o6_archive_state.json"
        self.env_patcher = mock.patch.dict(
            os.environ,
            {"TRASHBOT_O6_CLOUD_ARCHIVE_STATE": str(self.o6_state_path)},
        )
        self.env_patcher.start()
        self.server = build_server("127.0.0.1", 0, self.state_path, "phone-token")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = RelayHttpClient(f"http://127.0.0.1:{self.server.server_address[1]}")

    def tearDown(self):
        self.env_patcher.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)
        self.tmp.cleanup()

    def test_o7_operator_console_endpoint_is_public_readonly_and_fail_closed(self):
        status, body = self.client.request("GET", "/api/o7/operator-console", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o7.operator_console.v1")
        self.assertEqual(body["cloud_api_status"], "draft_blocked_not_proven")
        self.assertEqual(body["operator_mode"], "observe_only")
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertFalse(body["manual_control_policy"]["command_dispatch_enabled"])
        self.assertFalse(body["safe_command_snapshot"]["manual_control_enabled"])
        self.assertFalse(body["safe_command_snapshot"]["navigate_goal_enabled"])
        self.assertFalse(body["voice_asr_tts_snapshot"]["tts_send_enabled"])
        self.assertFalse(body["labeling_queue_snapshot"]["submit_enabled"])
        self.assertFalse(body["route_replay_snapshot"]["playback_available"])
        self.assertEqual([view["id"] for view in body["kr_views"]], [f"O7-KR{index}" for index in range(1, 7)])
        self.assertIn("real_o7_realtime_cloud_stream", body["not_proven"])

    def test_o7_rtc_signaling_contract_endpoint_is_static_readonly_and_fail_closed(self):
        with mock.patch.dict(
            os.environ,
            {
                "O7_RTC_REALTIME_TOKEN": "Bearer should-never-leak",
                "TRASHBOT_O7_RTC_SIGNALING_URL": "https://rtc.example.test/signaling",
            },
        ):
            status, body = self.client.request("GET", "/api/o7/rtc-signaling/contract", token="")

        encoded = json.dumps(body, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o7.rtc_signaling_contract.v1")
        self.assertEqual(body["source"], "software_proof")
        self.assertEqual(body["proof_status"], "not_proven")
        self.assertEqual(body["contract_status"], "static_fail_closed_contract")
        self.assertFalse(body["network_probe_executed"])
        self.assertFalse(body["webrtc_session_created"])
        self.assertFalse(body["media_transport_connected"])
        self.assertFalse(body["video_track_received"])
        self.assertFalse(body["realtime_pose_stream_connected"])
        self.assertFalse(body["real_ros2_tf_connected"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["sends_commands"])
        self.assertFalse(body["reads_hardware"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["delivery_success"])
        surfaces = body["protocol_surfaces"]
        self.assertEqual(surfaces["signaling_endpoint"]["path_template"], "/api/o7/rtc/signaling/sessions")
        self.assertEqual(surfaces["signaling_endpoint"]["status"], "receipt_only_implemented")
        self.assertTrue(surfaces["session_identity"]["idempotency_key_required"])
        self.assertEqual(surfaces["session_identity"]["status"], "receipt_only_validated")
        self.assertEqual(surfaces["offer_answer"]["status"], "offer_receipt_only_answer_disabled")
        self.assertTrue(surfaces["ice_candidates"]["trickle_ice_required"])
        self.assertEqual(surfaces["ice_candidates"]["status"], "future_not_implemented")
        self.assertFalse(surfaces["media_tracks"]["video"]["received"])
        self.assertFalse(surfaces["media_tracks"]["audio"]["received"])
        self.assertEqual(surfaces["media_tracks"]["status"], "future_not_implemented")
        self.assertTrue(surfaces["pose_realtime_events"]["requires_ros2_tf_bridge"])
        self.assertEqual(surfaces["pose_realtime_events"]["status"], "future_not_implemented")
        self.assertEqual(surfaces["elevator_realtime_events"]["status"], "future_not_implemented")
        self.assertFalse(surfaces["credential_handling"]["credential_values_exposed"])
        self.assertEqual(surfaces["credential_handling"]["credential_transport_policy"], "bearer_header_redacted")
        self.assertIn("first_video_frame_ref", surfaces["observability_evidence_refs"]["required_refs"])
        self.assertIn("media_timeout", surfaces["failure_timeout_semantics"]["required_states"])
        self.assertFalse(surfaces["forbidden_actions"]["command_dispatch"])
        self.assertFalse(surfaces["forbidden_actions"]["hardware_probe"])
        self.assertNotIn("rtc_signaling_endpoint_not_implemented", body["blocked_reasons"])
        self.assertIn("rtc_signaling_receipt_only", body["blocked_reasons"])
        self.assertIn("real_rtc_session_not_created", body["blocked_reasons"])
        self.assertIn("webrtc_answer_disabled", body["blocked_reasons"])
        self.assertIn("real_webrtc_media_transport", body["not_proven"])
        self.assertIn("ros2_tf_bridge_trace", body["next_required_evidence"])
        for forbidden in ("should-never-leak", "Authorization: Bearer should-never-leak", "/cmd_vel", "ttyUSB"):
            self.assertNotIn(forbidden, encoded)

    def test_o7_rtc_contract_sensitive_false_keys_do_not_allow_true_values(self):
        payload = relay_module.safe_value(
            {
                "reads_hardware": True,
                "hardware_probe": True,
                "safe_false": {
                    "reads_hardware": False,
                    "hardware_probe": False,
                },
                "auth_token_handling": {"token_values_exposed": False},
                "token_transport": "bearer_header_redacted",
                "token_values_exposed": False,
            }
        )

        self.assertNotIn("reads_hardware", payload)
        self.assertNotIn("hardware_probe", payload)
        self.assertFalse(payload["safe_false"]["reads_hardware"])
        self.assertFalse(payload["safe_false"]["hardware_probe"])
        self.assertNotIn("auth_token_handling", payload)
        self.assertNotIn("token_transport", payload)
        self.assertNotIn("token_values_exposed", payload)

    def test_o7_rtc_signaling_session_receipt_is_bearer_gated_and_fail_closed(self):
        status, unauthorized = self.client.request(
            "POST",
            "/api/o7/rtc/signaling/sessions",
            {
                "robot_id": "trashbot-001",
                "client_id": "pc-console",
                "session_id": "rtc-session-001",
                "idempotency_key": "rtc-session-001-create",
                "offer": {"type": "offer", "sdp": "v=0\r\na=sendrecv\r\n"},
            },
            token="",
        )
        self.assertEqual(status, 401)
        self.assertEqual(unauthorized["error"]["code"], "auth_failed")

        offer_sdp = (
            "v=0\r\n"
            "a=ice-ufrag:Authorization Bearer leaked-token\r\n"
            "a=candidate:1 1 UDP 1 192.0.2.10 3478 typ host https://turn.example.test\r\n"
        )
        status, body = self.client.request(
            "POST",
            "/api/o7/rtc/signaling/sessions",
            {
                "robot_id": "trashbot-001",
                "client_id": "pc-console",
                "session_id": "rtc-session-001",
                "idempotency_key": "rtc-session-001-create",
                "offer": {"type": "offer", "sdp": offer_sdp},
                "auth": "Bearer body-credential",
                "turn_url": "https://turn.example.test/secret",
            },
        )
        encoded = json.dumps(body, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o7.rtc_signaling_session_receipt.v1")
        self.assertEqual(body["source"], "software_proof")
        self.assertEqual(body["proof_status"], "not_proven")
        self.assertEqual(body["session_status"], "blocked_not_created")
        self.assertTrue(body["validated_contract_fields"])
        self.assertFalse(body["webrtc_session_created"])
        self.assertFalse(body["answer_created"])
        self.assertFalse(body["ice_candidates_processed"])
        self.assertFalse(body["media_transport_connected"])
        self.assertFalse(body["video_track_received"])
        self.assertFalse(body["realtime_pose_stream_connected"])
        self.assertFalse(body["real_ros2_tf_connected"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["sends_commands"])
        self.assertFalse(body["reads_hardware"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["delivery_success"])
        self.assertEqual(body["field_summaries"]["offer"]["sdp_length"], len(offer_sdp))
        self.assertTrue(body["field_summaries"]["offer"]["sdp_sha256_prefix"])
        for forbidden in (
            offer_sdp,
            "Authorization",
            "Bearer",
            "leaked-token",
            "https://turn.example.test",
            "body-credential",
            "turn_url",
            "/cmd_vel",
        ):
            self.assertNotIn(forbidden, encoded)

        status, next_payload = self.client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertIsNone(next_payload["command"])

    def test_o7_rtc_signaling_session_receipt_missing_fields_returns_structured_400(self):
        status, body = self.client.request(
            "POST",
            "/api/o7/rtc/signaling/sessions",
            {
                "robot_id": "trashbot-001",
                "client_id": "pc-console",
                "session_id": "rtc-session-001",
                "offer": {},
            },
        )

        self.assertEqual(status, 400)
        self.assertEqual(body["schema"], "trashbot.o7.rtc_signaling_session_receipt.v1")
        self.assertFalse(body["validated_contract_fields"])
        self.assertEqual(body["session_status"], "blocked_not_created")
        self.assertIn("idempotency_key", body["missing_fields"])
        self.assertIn("offer.sdp", body["missing_fields"])
        self.assertFalse(body["webrtc_session_created"])
        self.assertFalse(body["answer_created"])
        self.assertFalse(body["sends_commands"])
        self.assertFalse(body["reads_hardware"])

    def test_o7_rtc_signaling_session_bad_json_uses_existing_malformed_json(self):
        status, body = self.client.request(
            "POST",
            "/api/o7/rtc/signaling/sessions",
            raw_body=b"{bad-json",
        )

        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "malformed_json")
        self.assertNotIn("Traceback", json.dumps(body, ensure_ascii=False))

    def test_o7_rtc_signaling_session_local_empty_token_allows_probe(self):
        server = build_server("127.0.0.1", 0, pathlib.Path(self.tmp.name) / "open_relay_state.json", "")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}", token="")
        try:
            status, body = client.request(
                "POST",
                "/api/o7/rtc/signaling/sessions",
                {
                    "robot_id": "trashbot-001",
                    "client_id": "pc-console",
                    "session_id": "rtc-session-open",
                    "idempotency_key": "rtc-session-open-create",
                    "offer": {"sdp": "v=0\r\n"},
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        self.assertEqual(status, 200)
        self.assertTrue(body["validated_contract_fields"])
        self.assertFalse(body["webrtc_session_created"])

    def test_o7_cloud_archive_tasks_endpoint_is_public_readonly_and_fail_closed(self):
        status, body = self.client.request("GET", "/api/o7/cloud-archive/tasks", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o7.cloud_archive_tasks.v1")
        self.assertEqual(body["archive_status"], "blocked_not_proven")
        self.assertFalse(body["real_cloud_archive_connected"])
        self.assertFalse(body["real_realtime_api_connected"])
        self.assertFalse(body["real_annotation_api_connected"])
        self.assertFalse(body["real_voice_api_connected"])
        self.assertFalse(body["real_command_api_connected"])
        self.assertFalse(body["real_robot_ack_connected"])
        self.assertFalse(body["playback_available"])
        self.assertFalse(body["submit_enabled"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertFalse(body["robot_control_executed"])
        self.assertEqual(body["task_list"]["total_tasks"], 0)
        self.assertEqual(body["task_list"]["tasks"], [])
        self.assertIsNone(body["selected_task"])
        self.assertEqual(body["route_replay_inspector"]["status"], "blocked_not_proven")
        self.assertFalse(body["route_replay_inspector"]["cursor_initial_state"]["safe_to_play"])
        self.assertFalse(body["labeling_queue_inspector"]["submit_enabled"])
        self.assertFalse(body["voice_asr_tts_inspector"]["tts_send_enabled"])
        self.assertFalse(body["safe_command_inspector"]["command_dispatch_enabled"])
        self.assertIn("real_cloud_archive_store_not_connected", body["blocked_reasons"])
        self.assertIn("real_o7_cloud_archive_task_api", body["not_proven"])

    def test_o7_cloud_archive_tasks_endpoint_reads_safe_env_fixture_summary_only(self):
        fixture_path = pathlib.Path(self.tmp.name) / "o7_archive_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.cloud_archive_fixture.v1",
                    "tasks": [
                        {
                            "task_id": "task-o7-001",
                            "robot_id": "trashbot-001",
                            "status": "fixture_recorded",
                            "started_at": "2026-05-27T09:00:00+08:00",
                            "selected": True,
                            "map_frame": "map",
                            "trajectory": [
                                {
                                    "frame_index": 0,
                                    "timestamp_ms": 1000,
                                    "pose": {"x_m": 1.2, "y_m": 2.3, "yaw_rad": 0.4},
                                    "velocity": {"speed_mps": 0.2},
                                    "state": "patrol",
                                    "evidence_ref": "frames/frame-0001.jpg",
                                }
                            ],
                            "events": [
                                {
                                    "event_type": "elevator_wait",
                                    "state": "waiting",
                                    "timestamp_ms": 1100,
                                    "evidence_ref": "events/event-0001.json",
                                }
                            ],
                            "keyframe_refs": ["keyframes/keyframe-0001.jpg"],
                            "labels": [
                                {
                                    "label_type": "elevator_door",
                                    "value": "open",
                                    "status": "fixture_review",
                                    "evidence_ref": "labels/label-0001.json",
                                }
                            ],
                            "label_schema": {
                                "schema_ref": "label-schema.json",
                                "version": "v1",
                                "allowed_fields": ["label_type", "value"],
                            },
                            "allowed_label_types": ["elevator_door", "obstacle"],
                            "asr_events": [
                                {
                                    "event_type": "final",
                                    "timestamp_ms": 1200,
                                    "transcript": "到达电梯口",
                                    "confidence": 0.91,
                                    "evidence_ref": "voice/asr-0001.json",
                                }
                            ],
                            "tts_draft": {"text": "请帮我按电梯", "voice_profile": "default", "language": "zh-CN"},
                            "commands": [
                                {
                                    "command_id": "cmd-fixture-001",
                                    "command_type": "navigate_goal",
                                    "status": "fixture_review",
                                    "evidence_ref": "commands/cmd-0001.json",
                                }
                            ],
                            "manual_turn_envelope": {
                                "requested_direction": "left",
                                "evidence_ref": "commands/manual-0001.json",
                            },
                            "navigate_goal_envelope": {
                                "goal_source": "operator_map_click",
                                "map_frame": "map",
                                "x_m": 3.0,
                                "y_m": 4.0,
                                "yaw_rad": 1.57,
                                "evidence_ref": "commands/nav-0001.json",
                            },
                        },
                        {
                            "task_id": "task-o7-002",
                            "robot_id": "trashbot-001",
                            "status": "fixture_recorded",
                            "started_at": "2026-05-27T09:10:00+08:00",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/cloud-archive/tasks", token="")

        encoded = json.dumps(body, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(body["archive_status"], "fixture_summary_ready")
        self.assertTrue(body["cloud_runtime_fixture_connected"])
        self.assertFalse(body["real_cloud_archive_connected"])
        self.assertFalse(body["playback_available"])
        self.assertFalse(body["submit_enabled"])
        self.assertFalse(body["tts_send_enabled"])
        self.assertFalse(body["command_dispatch_enabled"])
        self.assertFalse(body["manual_control_enabled"])
        self.assertFalse(body["navigate_goal_enabled"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertEqual(body["task_list"]["total_tasks"], 2)
        self.assertEqual(body["selected_task"]["task_id"], "task-o7-001")
        self.assertEqual(body["latest_task"]["task_id"], "task-o7-002")
        self.assertEqual(body["safe_summaries"]["trajectory"]["frame_count"], 1)
        self.assertEqual(body["safe_summaries"]["labels"]["label_count"], 1)
        self.assertEqual(body["safe_summaries"]["voice"]["asr_event_count"], 1)
        self.assertEqual(body["safe_summaries"]["commands"]["command_count"], 1)
        self.assertEqual(body["route_replay_inspector"]["status"], "fixture_inspector_ready")
        self.assertEqual(body["route_replay_inspector"]["sample_frames"][0]["x_m"], 1.2)
        self.assertEqual(body["route_replay_inspector"]["event_timeline"][0]["event_type"], "elevator_wait")
        self.assertEqual(body["route_replay_inspector"]["keyframe_refs"], ["keyframe-0001.jpg"])
        self.assertEqual(body["labeling_queue_inspector"]["status"], "fixture_labeling_ready")
        self.assertEqual(body["voice_asr_tts_inspector"]["status"], "fixture_voice_ready")
        self.assertEqual(body["safe_command_inspector"]["status"], "fixture_command_ready")
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "baudrate", "traceback"):
            self.assertNotIn(forbidden, encoded)

    def test_o7_cloud_archive_tasks_endpoint_sanitizes_malformed_numeric_fixture(self):
        fixture_path = pathlib.Path(self.tmp.name) / "malformed_numeric_o7_archive_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.cloud_archive_fixture.v1",
                    "tasks": [
                        {
                            "task_id": "task-o7-numeric",
                            "selected": True,
                            "trajectory": [
                                {
                                    "frame_index": "bad",
                                    "timestamp_ms": "not-a-number",
                                    "x_m": "nan",
                                    "y_m": "2.5",
                                    "yaw_rad": "inf",
                                    "speed_mps": {"bad": "shape"},
                                    "state": "patrol",
                                    "evidence_ref": "frames/frame-numeric.jpg",
                                }
                            ],
                            "navigate_goal_envelope": {
                                "goal_source": "operator_map_click",
                                "map_frame": "map",
                                "x_m": "bad",
                                "y_m": "4.25",
                                "yaw_rad": "inf",
                                "evidence_ref": "commands/nav-numeric.json",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/cloud-archive/tasks", token="")

        frame = body["route_replay_inspector"]["sample_frames"][0]
        navigate = body["safe_command_inspector"]["navigate_goal_envelope"]
        map_goal = body["safe_command_inspector"]["map_goal_slot"]
        self.assertEqual(status, 200)
        self.assertEqual(body["archive_status"], "fixture_summary_ready")
        self.assertEqual(frame["frame_index"], 0)
        self.assertIsNone(frame["timestamp_ms"])
        self.assertIsNone(frame["x_m"])
        self.assertEqual(frame["y_m"], 2.5)
        self.assertIsNone(frame["yaw_rad"])
        self.assertIsNone(frame["speed_mps"])
        self.assertIsNone(navigate["x_m"])
        self.assertEqual(navigate["y_m"], 4.25)
        self.assertIsNone(navigate["yaw_rad"])
        self.assertIsNone(map_goal["x_m"])
        self.assertEqual(map_goal["y_m"], 4.25)
        self.assertIsNone(map_goal["yaw_rad"])
        self.assertFalse(body["real_cloud_archive_connected"])
        self.assertFalse(body["playback_available"])
        self.assertFalse(body["submit_enabled"])
        self.assertFalse(body["tts_send_enabled"])
        self.assertFalse(body["command_dispatch_enabled"])
        self.assertFalse(body["manual_control_enabled"])
        self.assertFalse(body["navigate_goal_enabled"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])

    def test_o7_cloud_archive_tasks_endpoint_blocks_unsafe_env_fixture(self):
        fixture_path = pathlib.Path(self.tmp.name) / "unsafe_o7_archive_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.cloud_archive_fixture.v1",
                    "tasks": [
                        {
                            "task_id": "task-o7-unsafe",
                            "trajectory": [{"evidence_ref": "Authorization: Bearer leaked-token"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/cloud-archive/tasks", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["archive_status"], "blocked_not_proven")
        self.assertEqual(body["input_status"]["failure_reason"], "unsafe_fixture_claim")
        self.assertFalse(body.get("cloud_runtime_fixture_connected", False))
        self.assertFalse(body["real_cloud_archive_connected"])
        self.assertEqual(body["task_list"]["total_tasks"], 0)
        self.assertEqual(body["task_list"]["tasks"], [])

    def test_o6_cloud_archive_tasks_endpoint_is_public_readonly_and_fail_closed(self):
        status, body = self.client.request("GET", "/api/o6/archive/tasks", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o6.cloud_archive.v1")
        self.assertEqual(body["source"], "local_mock_archive")
        self.assertEqual(body["archive_status"], "blocked_not_proven")
        self.assertFalse(body["real_cloud_db_connected"])
        self.assertFalse(body["real_oss_connected"])
        self.assertFalse(body["connects_cloud_production"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertEqual(body["task_list"]["total_tasks"], 0)
        self.assertEqual(body["task_list"]["tasks"], [])
        self.assertIsNone(body["selected_task"])
        self.assertIsNone(body["latest_task"])
        self.assertEqual(body["summary"]["task_count"], 0)
        self.assertIn("real_cloud_db_not_connected", body["not_proven"])

    def test_o6_cloud_archive_tasks_endpoint_upserts_lists_and_gets_item(self):
        payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-001",
            "started_at_ms": 1000,
            "finished_at_ms": 2000,
            "trajectory_frames": [
                {
                    "frame_index": 0,
                    "timestamp_ms": 1000,
                    "x_m": 1.25,
                    "y_m": 2.5,
                    "yaw_rad": 0.5,
                    "speed_mps": 0.15,
                    "state": "patrol",
                    "evidence_ref": "frames/frame-001.jpg",
                }
            ],
            "events": [
                {
                    "event_type": "archive_created",
                    "timestamp_ms": 1200,
                    "state": "recorded",
                    "details": "local mock archive ready",
                    "evidence_ref": "events/event-001.json",
                }
            ],
            "evidence_refs": ["evidence/archive-001.json"],
        }

        status, created = self.client.request("POST", "/api/o6/archive/tasks", payload)
        self.assertEqual(status, 201)
        self.assertEqual(created["write_status"], "created")
        self.assertFalse(created["duplicate"])
        self.assertEqual(created["task"]["task_id"], "task-o6-001")
        self.assertEqual(created["task"]["trajectory_frames"][0]["x_m"], 1.25)
        self.assertEqual(created["task"]["events"][0]["event_type"], "archive_created")
        self.assertEqual(created["task"]["evidence_refs"], ["archive-001.json"])
        self.assertTrue(self.o6_state_path.exists())

        status, listing = self.client.request("GET", "/api/o6/archive/tasks", token="")
        self.assertEqual(status, 200)
        self.assertEqual(listing["task_list"]["total_tasks"], 1)
        self.assertEqual(listing["selected_task"]["task_id"], "task-o6-001")
        self.assertEqual(listing["latest_task"]["task_id"], "task-o6-001")

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-001", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["task"]["task_id"], "task-o6-001")
        self.assertEqual(detail["task"]["trajectory_frames"][0]["state"], "patrol")
        self.assertEqual(detail["task_lookup"]["status"], "local_mock_archive_ready")

        updated_payload = dict(payload)
        updated_payload["finished_at_ms"] = 2500
        updated_payload["events"] = payload["events"] + [
            {
                "event_type": "archive_updated",
                "timestamp_ms": 2200,
                "state": "updated",
                "details": "still local mock",
                "evidence_ref": "events/event-002.json",
            }
        ]
        status, updated = self.client.request("POST", "/api/o6/archive/tasks", updated_payload)
        self.assertEqual(status, 200)
        self.assertTrue(updated["duplicate"])
        self.assertEqual(updated["write_status"], "updated")
        self.assertEqual(updated["task"]["finished_at_ms"], 2500)
        self.assertEqual(updated["task_list"]["total_tasks"], 1)
        self.assertEqual(updated["summary"]["task_count"], 1)

    def test_o6_cloud_archive_tasks_endpoint_rejects_unsafe_or_oversized_payloads(self):
        unsafe_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-unsafe",
            "started_at_ms": 1000,
            "finished_at_ms": 2000,
            "trajectory_frames": [],
            "events": [],
            "evidence_refs": ["Authorization: Bearer leaked-token"],
        }
        status, body = self.client.request("POST", "/api/o6/archive/tasks", unsafe_payload)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        too_large_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-large",
            "started_at_ms": 1000,
            "finished_at_ms": 2000,
            "trajectory_frames": [
                {
                    "frame_index": index,
                    "timestamp_ms": 1000 + index,
                    "x_m": float(index),
                    "y_m": float(index),
                    "yaw_rad": 0.0,
                    "speed_mps": 0.1,
                    "state": "patrol",
                    "evidence_ref": f"frames/frame-{index:03d}.jpg",
                }
                for index in range(65)
            ],
            "events": [],
            "evidence_refs": [],
        }
        status, body = self.client.request("POST", "/api/o6/archive/tasks", too_large_payload)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("too large", body["error"]["message"].lower())

        raw_body = b"{" + b" " * (relay_module.O6_CLOUD_ARCHIVE_MAX_BODY_BYTES + 1) + b"}"
        status, body = self.client.request("POST", "/api/o6/archive/tasks", raw_body=raw_body)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("too large", body["error"]["message"].lower())

    def test_o6_cloud_archive_tasks_endpoint_rejects_bad_json_missing_fields_and_time_order(self):
        # O6 是后续 O7 的数据源，坏输入必须早拒绝，不能生成看似可回放的空任务。
        status, body = self.client.request("POST", "/api/o6/archive/tasks", raw_body=b'{"robot_id":')
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "malformed_json")

        missing_events_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-missing-events",
            "started_at_ms": 1000,
            "finished_at_ms": 2000,
            "trajectory_frames": [],
        }
        status, body = self.client.request("POST", "/api/o6/archive/tasks", missing_events_payload)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("events", body["error"]["message"])

        bad_time_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-bad-time",
            "started_at_ms": 2000,
            "finished_at_ms": 1000,
            "trajectory_frames": [],
            "events": [],
        }
        status, body = self.client.request("POST", "/api/o6/archive/tasks", bad_time_payload)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("finished_at_ms", body["error"]["message"])

    def test_o6_cloud_archive_tasks_endpoint_missing_detail_fails_closed(self):
        status, body = self.client.request("GET", "/api/o6/archive/tasks/missing-task", token="")

        encoded = json.dumps(body, ensure_ascii=False)
        self.assertEqual(status, 404)
        self.assertEqual(body["error"]["code"], "not_found")
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "traceback"):
            self.assertNotIn(forbidden, encoded)

    def _o6_archive_task_payload(self, task_id="task-o6-001", robot_id="trashbot-001", finished_at=2000):
        # 标注接口依赖已有 task，先用 local mock task API 固定创建/更新同一份可复用输入。
        return {
            "robot_id": robot_id,
            "task_id": task_id,
            "started_at_ms": 1000,
            "finished_at_ms": finished_at,
            "trajectory_frames": [
                {
                    "frame_index": 0,
                    "timestamp_ms": 1000,
                    "x_m": 1.25,
                    "y_m": 2.5,
                    "yaw_rad": 0.5,
                    "speed_mps": 0.15,
                    "state": "patrol",
                    "evidence_ref": "frames/frame-001.jpg",
                }
            ],
            "events": [
                {
                    "event_type": "archive_created",
                    "timestamp_ms": 1200,
                    "state": "recorded",
                    "details": "local mock archive ready",
                    "evidence_ref": "events/event-001.json",
                }
            ],
            "evidence_refs": ["evidence/archive-001.json"],
        }

    def _o6_event_archive_payload(self, task_id="task-o6-events", event_id="evt-route-0001", event_type="route.pose"):
        # 事件 payload 固定落在 helper task 时间窗内，便于复用同一批 fail-closed 用例。
        return {
            "robot_id": "trashbot-001",
            "task_id": task_id,
            "events": [
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "occurred_at_ms": 1500,
                    "pose": {"x_m": 1.2, "y_m": 0.4, "yaw_rad": 0.1, "floor_id": "F1"},
                    "summary": "route pose frame",
                    "severity": "info",
                    "evidence_refs": ["oss://mock/rober/trashbot-001/task-o6-events/frame-0001.jpg"],
                    "metadata": {"frame_index": 1, "camera": "front"},
                }
            ],
        }

    def _o6_evidence_archive_payload(self, task_id="task-o6-evidence", evidence_id="evd-frame-0001"):
        # evidence 接口只写 ref 摘要；测试里用 oss:// 输入验证回包不泄露完整 URL。
        return {
            "robot_id": "trashbot-001",
            "task_id": task_id,
            "evidence_refs": [
                {
                    "evidence_id": evidence_id,
                    "evidence_type": "camera_frame",
                    "evidence_ref": "oss://mock/rober/trashbot-001/task-o6-evidence/frame-0001.jpg",
                    "captured_at_ms": 1500,
                    "event_id": "evt-route-0001",
                    "content_type": "image/jpeg",
                    "size_bytes": 123456,
                    "checksum": "sha256:mock",
                    "metadata": {"camera": "front"},
                }
            ],
        }

    def test_o6_archive_events_endpoint_writes_lists_filters_and_detail_reads_back(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-events"),
        )
        self.assertEqual(status, 201)

        payload = self._o6_event_archive_payload(task_id="task-o6-events")
        payload["events"].append(
            {
                "event_id": "evt-elevator-0001",
                "event_type": "elevator.door_state",
                "occurred_at_ms": 1700,
                "summary": "door state sample",
                "severity": "warning",
                "metadata": {"door_state": "unknown"},
            }
        )
        status, created = self.client.request("POST", "/api/o6/archive/events", payload)

        encoded = json.dumps(created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], "trashbot.o6.archive_events.v1")
        self.assertEqual(created["source"], "local_mock_event_archive")
        self.assertEqual(created["proof_status"], "not_proven")
        self.assertTrue(created["archive_event_written"])
        self.assertFalse(created["real_cloud_db_connected"])
        self.assertFalse(created["real_oss_connected"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["primary_actions_enabled"])
        self.assertEqual(created["event_summary"]["created_count"], 2)
        self.assertEqual(created["event_summary"]["updated_count"], 0)
        self.assertEqual(created["events_written"][0]["evidence_refs"], ["frame-0001.jpg"])
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "oss://mock"):
            self.assertNotIn(forbidden, encoded)

        status, listing = self.client.request(
            "GET",
            "/api/o6/archive/events?task_id=task-o6-events&event_type=route.pose&from_ms=1400&to_ms=1600&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(listing["schema"], "trashbot.o6.archive_events.v1")
        self.assertFalse(listing["archive_event_written"])
        self.assertEqual(listing["query"]["event_type"], "route.pose")
        self.assertEqual(len(listing["events"]), 1)
        self.assertEqual(listing["events"][0]["event_id"], "evt-route-0001")
        self.assertEqual(listing["event_summary"]["event_count"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-events", token="")
        self.assertEqual(status, 200)
        event_by_id = {event.get("event_id"): event for event in detail["task"]["events"] if event.get("event_id")}
        self.assertEqual(event_by_id["evt-route-0001"]["source"], "local_mock_event_archive")
        self.assertEqual(event_by_id["evt-route-0001"]["metadata"]["frame_index"], 1)

    def test_o6_archive_events_endpoint_is_idempotent_and_supports_mixed_batches(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-events-mixed"),
        )
        self.assertEqual(status, 201)

        status, first = self.client.request(
            "POST",
            "/api/o6/archive/events",
            self._o6_event_archive_payload(task_id="task-o6-events-mixed", event_id="evt-a"),
        )
        self.assertEqual(status, 201)
        self.assertEqual(first["event_summary"]["created_count"], 1)

        mixed = self._o6_event_archive_payload(task_id="task-o6-events-mixed", event_id="evt-a")
        mixed["events"][0]["summary"] = "route pose frame updated"
        mixed["events"].append(
            {
                "event_id": "evt-b",
                "event_type": "task.recovery",
                "occurred_at_ms": 1600,
                "summary": "recovery note",
                "severity": "info",
                "metadata": {"reason": "operator_note"},
            }
        )
        status, updated = self.client.request("POST", "/api/o6/archive/events", mixed)
        self.assertEqual(status, 200)
        self.assertTrue(updated["duplicate"])
        self.assertEqual(updated["write_status"], "updated")
        self.assertEqual(updated["event_summary"]["created_count"], 1)
        self.assertEqual(updated["event_summary"]["updated_count"], 1)

        status, listing = self.client.request("GET", "/api/o6/archive/events?task_id=task-o6-events-mixed&limit=10")
        self.assertEqual(status, 200)
        events = {event["event_id"]: event for event in listing["events"]}
        self.assertEqual(events["evt-a"]["summary"], "route pose frame updated")
        self.assertIn("evt-b", events)

    def test_o6_archive_events_endpoint_rejects_bad_json_scope_query_and_unsafe_payloads(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-events-reject"),
        )
        self.assertEqual(status, 201)

        status, bad_json = self.client.request("POST", "/api/o6/archive/events", raw_body=b"{bad-json")
        self.assertEqual(status, 400)
        self.assertEqual(bad_json["error"]["code"], "malformed_json")

        status, non_object = self.client.request("POST", "/api/o6/archive/events", raw_body=b"[]")
        self.assertEqual(status, 400)
        self.assertEqual(non_object["error"]["code"], "bad_request")

        missing = {"robot_id": "trashbot-001", "task_id": "task-o6-events-reject"}
        status, missing_body = self.client.request("POST", "/api/o6/archive/events", missing)
        self.assertEqual(status, 400)
        self.assertEqual(missing_body["error"]["code"], "bad_request")

        too_large = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        too_large["events"] = [
            {
                "event_id": f"evt-{index:03d}",
                "event_type": "route.pose",
                "occurred_at_ms": 1500,
            }
            for index in range(relay_module.O6_ARCHIVE_MAX_BATCH_ITEMS + 1)
        ]
        status, oversized = self.client.request("POST", "/api/o6/archive/events", too_large)
        self.assertEqual(status, 400)
        self.assertEqual(oversized["error"]["code"], "bad_request")

        unknown = self._o6_event_archive_payload(task_id="missing-task")
        status, unknown_body = self.client.request("POST", "/api/o6/archive/events", unknown)
        self.assertEqual(status, 404)
        self.assertEqual(unknown_body["error"]["code"], "unknown_task")

        unauthorized = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        unauthorized["robot_id"] = "trashbot-other"
        status, unauthorized_body = self.client.request("POST", "/api/o6/archive/events", unauthorized)
        self.assertEqual(status, 403)
        self.assertEqual(unauthorized_body["error"]["code"], "unauthorized_task")

        bad_type = self._o6_event_archive_payload(task_id="task-o6-events-reject", event_type="model_inference.floor_recognition")
        status, bad_type_body = self.client.request("POST", "/api/o6/archive/events", bad_type)
        self.assertEqual(status, 400)
        self.assertEqual(bad_type_body["error"]["code"], "bad_request")

        out_of_window = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        out_of_window["events"][0]["occurred_at_ms"] = 2500
        status, window_body = self.client.request("POST", "/api/o6/archive/events", out_of_window)
        self.assertEqual(status, 400)
        self.assertIn("occurred_at_ms", window_body["error"]["message"])

        unsafe = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        unsafe["events"][0]["metadata"] = {"note": "Authorization Bearer leaked-token"}
        status, unsafe_body = self.client.request("POST", "/api/o6/archive/events", unsafe)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", unsafe_body["error"]["message"].lower())

        real_claim = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        real_claim["cloud_db_connected"] = True
        status, real_claim_body = self.client.request("POST", "/api/o6/archive/events", real_claim)
        self.assertEqual(status, 400)
        self.assertEqual(real_claim_body["error"]["code"], "bad_request")

        raw_content = self._o6_event_archive_payload(task_id="task-o6-events-reject")
        raw_content["events"][0]["image_base64"] = "base64,raw"
        status, raw_body = self.client.request("POST", "/api/o6/archive/events", raw_content)
        self.assertEqual(status, 400)
        self.assertEqual(raw_body["error"]["code"], "bad_request")

        status, invalid_type = self.client.request("GET", "/api/o6/archive/events?event_type=bad.type")
        self.assertEqual(status, 400)
        status, invalid_limit = self.client.request("GET", "/api/o6/archive/events?limit=99999")
        self.assertEqual(status, 400)
        status, invalid_window = self.client.request("GET", "/api/o6/archive/events?from_ms=2000&to_ms=1000")
        self.assertEqual(status, 400)
        status, unknown_query = self.client.request("GET", "/api/o6/archive/events?task_id=missing-task")
        self.assertEqual(status, 404)
        self.assertEqual(unknown_query["error"]["code"], "unknown_task")

    def test_o6_archive_evidence_endpoint_writes_lists_filters_and_detail_reads_back(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-evidence"),
        )
        self.assertEqual(status, 201)

        payload = self._o6_evidence_archive_payload(task_id="task-o6-evidence")
        payload["evidence_refs"].append(
            {
                "evidence_id": "evd-failure-0001",
                "evidence_type": "failure_snapshot",
                "evidence_ref": "oss://mock/rober/trashbot-001/task-o6-evidence/failure-0001.jpg",
                "captured_at_ms": 1700,
                "event_id": "evt-failure-0001",
                "content_type": "image/jpeg",
                "size_bytes": 42,
                "checksum": "sha256:mock-failure",
                "metadata": {"reason": "blocked"},
            }
        )
        status, created = self.client.request("POST", "/api/o6/archive/evidence", payload)

        encoded = json.dumps(created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], "trashbot.o6.archive_evidence.v1")
        self.assertEqual(created["source"], "local_mock_evidence_archive")
        self.assertEqual(created["proof_status"], "not_proven")
        self.assertTrue(created["archive_evidence_written"])
        self.assertFalse(created["real_oss_upload_success"])
        self.assertFalse(created["real_cloud_db_connected"])
        self.assertFalse(created["real_oss_connected"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertEqual(created["evidence_summary"]["created_count"], 2)
        self.assertEqual(created["evidence_refs_written"][0]["evidence_ref"], "frame-0001.jpg")
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "oss://mock"):
            self.assertNotIn(forbidden, encoded)

        status, listing = self.client.request(
            "GET",
            "/api/o6/archive/evidence?task_id=task-o6-evidence&evidence_type=camera_frame&event_id=evt-route-0001&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(listing["schema"], "trashbot.o6.archive_evidence.v1")
        self.assertFalse(listing["archive_evidence_written"])
        self.assertEqual(len(listing["evidence_refs"]), 1)
        self.assertEqual(listing["evidence_refs"][0]["evidence_id"], "evd-frame-0001")
        self.assertEqual(listing["evidence_summary"]["evidence_ref_count"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-evidence", token="")
        self.assertEqual(status, 200)
        evidence_by_id = {
            ref.get("evidence_id"): ref
            for ref in detail["task"]["evidence_refs"]
            if isinstance(ref, dict) and ref.get("evidence_id")
        }
        self.assertEqual(evidence_by_id["evd-frame-0001"]["source"] if "source" in evidence_by_id["evd-frame-0001"] else "local_mock_evidence_archive", "local_mock_evidence_archive")
        self.assertEqual(evidence_by_id["evd-frame-0001"]["metadata"]["camera"], "front")

    def test_o6_archive_evidence_endpoint_is_idempotent_and_supports_mixed_batches(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-evidence-mixed"),
        )
        self.assertEqual(status, 201)

        status, first = self.client.request(
            "POST",
            "/api/o6/archive/evidence",
            self._o6_evidence_archive_payload(task_id="task-o6-evidence-mixed", evidence_id="evd-a"),
        )
        self.assertEqual(status, 201)
        self.assertEqual(first["evidence_summary"]["created_count"], 1)

        mixed = self._o6_evidence_archive_payload(task_id="task-o6-evidence-mixed", evidence_id="evd-a")
        mixed["evidence_refs"][0]["checksum"] = "sha256:updated"
        mixed["evidence_refs"].append(
            {
                "evidence_id": "evd-b",
                "evidence_type": "snapshot",
                "evidence_ref": "oss://mock/rober/trashbot-001/task-o6-evidence-mixed/snapshot-0001.jpg",
                "captured_at_ms": 1600,
                "content_type": "image/jpeg",
                "metadata": {"camera": "rear"},
            }
        )
        status, updated = self.client.request("POST", "/api/o6/archive/evidence", mixed)
        self.assertEqual(status, 200)
        self.assertTrue(updated["duplicate"])
        self.assertEqual(updated["write_status"], "updated")
        self.assertEqual(updated["evidence_summary"]["created_count"], 1)
        self.assertEqual(updated["evidence_summary"]["updated_count"], 1)

        status, listing = self.client.request("GET", "/api/o6/archive/evidence?task_id=task-o6-evidence-mixed&limit=10")
        self.assertEqual(status, 200)
        evidence = {item["evidence_id"]: item for item in listing["evidence_refs"]}
        self.assertEqual(evidence["evd-a"]["checksum"], "sha256:updated")
        self.assertIn("evd-b", evidence)

    def test_o6_archive_evidence_endpoint_rejects_bad_json_scope_query_and_unsafe_payloads(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-evidence-reject"),
        )
        self.assertEqual(status, 201)

        status, bad_json = self.client.request("POST", "/api/o6/archive/evidence", raw_body=b"{bad-json")
        self.assertEqual(status, 400)
        self.assertEqual(bad_json["error"]["code"], "malformed_json")

        status, non_object = self.client.request("POST", "/api/o6/archive/evidence", raw_body=b"[]")
        self.assertEqual(status, 400)
        self.assertEqual(non_object["error"]["code"], "bad_request")

        missing = {"robot_id": "trashbot-001", "task_id": "task-o6-evidence-reject"}
        status, missing_body = self.client.request("POST", "/api/o6/archive/evidence", missing)
        self.assertEqual(status, 400)
        self.assertEqual(missing_body["error"]["code"], "bad_request")

        too_large = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        too_large["evidence_refs"] = [
            {
                "evidence_id": f"evd-{index:03d}",
                "evidence_type": "camera_frame",
                "evidence_ref": f"oss://mock/rober/task-o6-evidence-reject/frame-{index:03d}.jpg",
                "captured_at_ms": 1500,
            }
            for index in range(relay_module.O6_ARCHIVE_MAX_BATCH_ITEMS + 1)
        ]
        status, oversized = self.client.request("POST", "/api/o6/archive/evidence", too_large)
        self.assertEqual(status, 400)
        self.assertEqual(oversized["error"]["code"], "bad_request")

        unknown = self._o6_evidence_archive_payload(task_id="missing-task")
        status, unknown_body = self.client.request("POST", "/api/o6/archive/evidence", unknown)
        self.assertEqual(status, 404)
        self.assertEqual(unknown_body["error"]["code"], "unknown_task")

        unauthorized = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        unauthorized["robot_id"] = "trashbot-other"
        status, unauthorized_body = self.client.request("POST", "/api/o6/archive/evidence", unauthorized)
        self.assertEqual(status, 403)
        self.assertEqual(unauthorized_body["error"]["code"], "unauthorized_task")

        bad_type = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        bad_type["evidence_refs"][0]["evidence_type"] = "raw_video"
        status, bad_type_body = self.client.request("POST", "/api/o6/archive/evidence", bad_type)
        self.assertEqual(status, 400)
        self.assertEqual(bad_type_body["error"]["code"], "bad_request")

        out_of_window = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        out_of_window["evidence_refs"][0]["captured_at_ms"] = 2500
        status, window_body = self.client.request("POST", "/api/o6/archive/evidence", out_of_window)
        self.assertEqual(status, 400)
        self.assertIn("captured_at_ms", window_body["error"]["message"])

        unsafe = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        unsafe["evidence_refs"][0]["metadata"] = {"note": "Authorization Bearer leaked-token"}
        status, unsafe_body = self.client.request("POST", "/api/o6/archive/evidence", unsafe)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", unsafe_body["error"]["message"].lower())

        real_claim = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        real_claim["oss_uploaded"] = True
        status, real_claim_body = self.client.request("POST", "/api/o6/archive/evidence", real_claim)
        self.assertEqual(status, 400)
        self.assertEqual(real_claim_body["error"]["code"], "bad_request")

        raw_content = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        raw_content["evidence_refs"][0]["image_base64"] = "base64,raw"
        status, raw_body = self.client.request("POST", "/api/o6/archive/evidence", raw_content)
        self.assertEqual(status, 400)
        self.assertEqual(raw_body["error"]["code"], "bad_request")

        credential_url = self._o6_evidence_archive_payload(task_id="task-o6-evidence-reject")
        credential_url["evidence_refs"][0]["evidence_ref"] = "https://example.test/frame.jpg?token=secret"
        status, credential_body = self.client.request("POST", "/api/o6/archive/evidence", credential_url)
        self.assertEqual(status, 400)
        self.assertEqual(credential_body["error"]["code"], "bad_request")

        status, invalid_type = self.client.request("GET", "/api/o6/archive/evidence?evidence_type=bad.type")
        self.assertEqual(status, 400)
        status, invalid_limit = self.client.request("GET", "/api/o6/archive/evidence?limit=99999")
        self.assertEqual(status, 400)
        status, unknown_query = self.client.request("GET", "/api/o6/archive/evidence?task_id=missing-task")
        self.assertEqual(status, 404)
        self.assertEqual(unknown_query["error"]["code"], "unknown_task")

    def test_o6_cloud_archive_labels_endpoints_create_list_and_detail(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload())
        self.assertEqual(status, 201)

        payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-001",
            "labels": [
                {
                    "item_id": "traj-0001",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "open",
                    "confidence": 0.93,
                    "annotator_id": "labeler-01",
                    "evidence_ref": "labels/evidence-0001.json",
                    "notes": "first sample",
                },
                {
                    "item_id": "traj-0002",
                    "item_type": "trajectory_frame",
                    "label_type": "trajectory_gate",
                    "value": "valid",
                    "annotator_id": "labeler-01",
                    "evidence_ref": "labels/evidence-0002.json",
                },
            ],
        }

        status, created = self.client.request("POST", "/api/o6/archive/labels", payload)
        self.assertEqual(status, 201)
        self.assertEqual(created["write_status"], "created")
        self.assertEqual(created["task_id"], "task-o6-001")
        self.assertFalse(created["duplicate"])
        self.assertEqual(created["label_summary"]["itemized_label_count"], 2)
        self.assertEqual(created["label_summary"]["pending_item_count"], 1)
        self.assertEqual(created["label_summary"]["labeled_item_count"], 1)
        self.assertEqual(created["task_status"], "partial")
        self.assertEqual(created["schema"], relay_module.O6_CLOUD_LABELING_SCHEMA)
        self.assertEqual(created["source"], "local_mock_labeling")
        self.assertEqual(created["proof_status"], "not_proven")
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["primary_actions_enabled"])
        self.assertTrue(created["pc_only"])
        self.assertFalse(created["submit_enabled"])
        self.assertFalse(created["rollback_enabled"])
        self.assertFalse(created["dataset_export_available"])
        self.assertFalse(created["real_annotation_api_connected"])
        self.assertFalse(created["real_dataset_export_connected"])
        self.assertFalse(created["connects_cloud_production"])
        self.assertFalse(created["robot_control_executed"])

        status, listing = self.client.request("GET", "/api/o6/archive/labels?status=pending")
        self.assertEqual(status, 200)
        self.assertEqual(listing["schema"], relay_module.O6_CLOUD_LABELING_SCHEMA)
        self.assertEqual(listing["status_filter"], "pending")
        self.assertEqual(listing["label_summary"]["task_count"], 1)
        self.assertEqual(listing["label_summary"]["pending_task_count"], 0)
        self.assertEqual(listing["label_summary"]["partial_task_count"], 1)
        self.assertEqual(listing["label_summary"]["labeled_task_count"], 0)
        self.assertEqual(len(listing["task_summary"]), 1)
        self.assertEqual(listing["task_summary"][0]["task_id"], "task-o6-001")
        self.assertEqual(listing["task_summary"][0]["task_status"], "partial")

        status, labeled_listing = self.client.request("GET", "/api/o6/archive/labels?status=labeled")
        self.assertEqual(labeled_listing["label_summary"]["labeled_task_count"], 0)

        status, detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-001", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["task_id"], "task-o6-001")
        self.assertEqual(detail["robot_id"], "trashbot-001")
        self.assertEqual(detail["task_status"], "partial")
        self.assertEqual(len(detail["itemized_labels"]), 2)
        self.assertEqual(detail["itemized_labels"][0]["item_type"], "trajectory_frame")
        self.assertEqual(detail["itemized_labels"][0]["label_type"], "elevator_door_state")
        self.assertIn("real_annotation_submit_success", detail["not_proven"])

    def test_o6_cloud_archive_labels_endpoint_idempotent_upsert_and_task_scope(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-002"))
        self.assertEqual(status, 201)

        first_labels = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-002",
            "labels": [
                {
                    "item_id": "traj-0101",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "closed",
                    "confidence": 0.7,
                    "evidence_ref": "labels/evidence-0101.json",
                }
            ],
        }

        status, created = self.client.request("POST", "/api/o6/archive/labels", first_labels)
        self.assertEqual(status, 201)
        self.assertFalse(created["duplicate"])
        self.assertEqual(created["write_status"], "created")

        new_key = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-002",
            "labels": [
                {
                    "item_id": "traj-0102",
                    "item_type": "trajectory_frame",
                    "label_type": "trajectory_gate",
                    "value": "ok",
                    "confidence": 0.82,
                    "evidence_ref": "labels/evidence-0102.json",
                }
            ],
        }
        status, created_new_key = self.client.request("POST", "/api/o6/archive/labels", new_key)
        self.assertEqual(status, 201)
        self.assertFalse(created_new_key["duplicate"])
        self.assertEqual(created_new_key["write_status"], "created")
        self.assertEqual(created_new_key["label_summary"]["itemized_label_count"], 2)

        duplicated = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-002",
            "labels": [
                {
                    "item_id": "traj-0101",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "open",
                    "confidence": 0.97,
                    "evidence_ref": "labels/evidence-0101-updated.json",
                }
            ],
        }
        status, updated = self.client.request("POST", "/api/o6/archive/labels", duplicated)
        self.assertEqual(status, 200)
        self.assertTrue(updated["duplicate"])
        self.assertEqual(updated["write_status"], "updated")
        self.assertEqual(updated["label_summary"]["labeled_item_count"], 2)

        status, list_detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-002", token="")
        self.assertEqual(status, 200)
        self.assertEqual(list_detail["task_status"], "labeled")

    def test_o6_cloud_archive_labels_endpoint_batch_with_mix_existing_and_new_keys(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-004"))
        self.assertEqual(status, 201)

        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-004",
                "labels": [
                    {
                        "item_id": "traj-0401",
                        "item_type": "trajectory_frame",
                        "label_type": "elevator_door_state",
                        "value": "open",
                        "confidence": 0.9,
                        "evidence_ref": "labels/evidence-0401.json",
                    },
                    {
                        "item_id": "traj-0402",
                        "item_type": "trajectory_frame",
                        "label_type": "trajectory_gate",
                        "value": "valid",
                        "confidence": 0.8,
                        "evidence_ref": "labels/evidence-0402.json",
                    },
                ],
            },
        )
        self.assertEqual(status, 201)

        mixed_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-004",
            "labels": [
                {
                    "item_id": "traj-0401",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "closed",
                    "confidence": 0.95,
                    "evidence_ref": "labels/evidence-0401-updated.json",
                },
                {
                    "item_id": "traj-0403",
                    "item_type": "trajectory_frame",
                    "label_type": "trajectory_gate",
                    "value": "unknown",
                    "confidence": 0.88,
                    "evidence_ref": "labels/evidence-0403.json",
                },
            ],
        }

        status, mixed = self.client.request("POST", "/api/o6/archive/labels", mixed_payload)
        self.assertEqual(status, 200)
        self.assertTrue(mixed["duplicate"])
        self.assertEqual(mixed["write_status"], "updated")
        self.assertEqual(mixed["label_summary"]["itemized_label_count"], 3)
        self.assertEqual(mixed["task_status"], "labeled")

        status, detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-004", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["label_summary"]["itemized_label_count"], 3)
        itemized_labels = {(item["item_id"], item["label_type"]): item for item in detail["itemized_labels"]}
        self.assertEqual(itemized_labels[("traj-0401", "elevator_door_state")]["value"], "closed")
        self.assertIn(("traj-0402", "trajectory_gate"), itemized_labels)
        self.assertIn(("traj-0403", "trajectory_gate"), itemized_labels)

        status, cross = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-002",
                "task_id": "task-o6-004",
                "labels": [
                    {
                        "item_id": "traj-0102",
                        "item_type": "trajectory_frame",
                        "label_type": "elevator_door_state",
                        "value": "open",
                    }
                ],
            },
        )
        self.assertEqual(status, 403)
        self.assertEqual(cross["error"]["code"], "unauthorized_task")

        status, missing_task = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-004-missing",
                "labels": [
                    {
                        "item_id": "traj-0201",
                        "item_type": "trajectory_frame",
                        "label_type": "elevator_door_state",
                        "value": "open",
                    }
                ],
            },
        )
        self.assertEqual(status, 404)
        self.assertEqual(missing_task["error"]["code"], "unknown_task")

        status, list_detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-004", token="")
        self.assertEqual(status, 200)
        self.assertEqual(list_detail["task_status"], "labeled")

    def test_o6_cloud_archive_labels_endpoint_rejects_bad_json_labels_and_invalid_query(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-003"))
        self.assertEqual(status, 201)

        status, bad_type = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-003",
                "labels": {},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(bad_type["error"]["code"], "bad_request")

        status, missing = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-003",
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(missing["error"]["code"], "bad_request")

        status, raw_body = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            raw_body=b"[]",
        )
        self.assertEqual(status, 400)
        self.assertEqual(raw_body["error"]["code"], "bad_request")

        unsafe_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-003",
            "labels": [
                {
                    "item_id": "traj-0301",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "Authorization: Bearer leaked-token",
                }
            ],
        }
        status, unsafe = self.client.request("POST", "/api/o6/archive/labels", unsafe_payload)
        self.assertEqual(status, 400)
        self.assertEqual(unsafe["error"]["code"], "bad_request")
        self.assertIn("unsafe", unsafe["error"]["message"].lower())

        too_large = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-003",
            "labels": [
                {
                    "item_id": f"traj-{index:04d}",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "open",
                }
                for index in range(relay_module.O6_CLOUD_LABELING_MAX_LABELS + 1)
            ],
        }
        status, oversized = self.client.request("POST", "/api/o6/archive/labels", too_large)
        self.assertEqual(status, 400)
        self.assertEqual(oversized["error"]["code"], "bad_request")
        self.assertIn("too large", oversized["error"]["message"].lower())

        status, invalid_status = self.client.request("GET", "/api/o6/archive/labels?status=invalid", token="")
        self.assertEqual(status, 400)
        self.assertEqual(invalid_status["error"]["code"], "bad_request")

        status, invalid_limit = self.client.request("GET", "/api/o6/archive/labels?limit=-1", token="")
        self.assertEqual(status, 400)
        self.assertEqual(invalid_limit["error"]["code"], "bad_request")

        status, capped_listing = self.client.request("GET", "/api/o6/archive/labels?limit=99999", token="")
        self.assertEqual(status, 200)
        self.assertLessEqual(capped_listing["limit"], relay_module.O6_CLOUD_LABELING_MAX_LIST_LIMIT)
        self.assertEqual(capped_listing["status_filter"], "all")

    def _o6_inference_payload(self, task_id="task-o6-001", inference_id="infer-001", input_id="frame-001"):
        # 推理接口只消费已有 archive task，因此测试 payload 固定落在 helper task 的时间窗口内。
        return {
            "robot_id": "trashbot-001",
            "task_id": task_id,
            "inference_id": inference_id,
            "model_family": "elevator_scene_stub",
            "requested_outputs": ["elevator_door_state", "floor_recognition"],
            "inputs": [
                {
                    "input_id": input_id,
                    "input_type": "image_ref",
                    "evidence_ref": f"frames/{input_id}.jpg",
                    "captured_at_ms": 1500,
                    "metadata": {"camera": "front", "scene": "elevator"},
                }
            ],
        }

    def _o6_consumer_seed_task(self, task_id, *, started_at_ms, finished_at_ms, failure=False):
        # consumer 读面必须复用 archive/timeline 真数据，因此种子任务仍走既有写接口。
        payload = self._o6_archive_task_payload(task_id=task_id, finished_at=finished_at_ms)
        payload["started_at_ms"] = started_at_ms
        payload["trajectory_frames"] = [
            {
                "frame_index": 0,
                "timestamp_ms": started_at_ms,
                "x_m": 1.25,
                "y_m": 2.5,
                "yaw_rad": 0.5,
                "speed_mps": 0.15,
                "state": "patrol",
                "evidence_ref": "frames/frame-001.jpg",
            },
            {
                "frame_index": 1,
                "timestamp_ms": started_at_ms + 200,
                "x_m": 1.35,
                "y_m": 2.7,
                "yaw_rad": 0.55,
                "speed_mps": 0.12,
                "state": "collect" if failure else "patrol",
                "evidence_ref": "frames/frame-002.jpg",
            },
        ]
        payload["events"] = [
            {
                "event_type": "archive_created",
                "timestamp_ms": started_at_ms + 100,
                "state": "recorded",
                "details": "local mock archive ready",
                "evidence_ref": "events/event-001.json",
            }
        ]
        status, body = self.client.request("POST", "/api/o6/archive/tasks", payload)
        self.assertEqual(status, 201)
        if failure:
            status, _ = self.client.request(
                "POST",
                "/api/o6/archive/events",
                {
                    "robot_id": "trashbot-001",
                    "task_id": task_id,
                    "events": [
                        {
                            "event_id": "evt-failure-001",
                            "event_type": "task.failure",
                            "occurred_at_ms": started_at_ms + 300,
                            "summary": "blocked by mock failure",
                            "severity": "error",
                            "metadata": {"reason": "mock_failure"},
                        }
                    ],
                },
            )
            self.assertEqual(status, 201)
        return body

    def _o6_consumer_seed_rich_task(self, task_id="task-o6-consumer-rich"):
        # rich task 用来验证 consumer detail 的聚合完整性和 include/view 瘦身。
        self._o6_consumer_seed_task(task_id, started_at_ms=1000, finished_at_ms=2200)
        status, _ = self.client.request("POST", "/api/o6/archive/events", self._o6_event_archive_payload(task_id=task_id))
        self.assertEqual(status, 201)
        status, _ = self.client.request("POST", "/api/o6/archive/evidence", self._o6_evidence_archive_payload(task_id=task_id))
        self.assertEqual(status, 201)
        labels_payload = {
            "robot_id": "trashbot-001",
            "task_id": task_id,
            "labels": [
                {
                    "item_id": "frame-001",
                    "item_type": "route_frame",
                    "label_type": "floor_id",
                    "value": "F1",
                    "confidence": 0.9,
                    "annotator_id": "operator-a",
                    "evidence_ref": "frames/frame-001.jpg",
                }
            ],
        }
        status, _ = self.client.request("POST", "/api/o6/archive/labels", labels_payload)
        self.assertEqual(status, 201)
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/inference",
            self._o6_inference_payload(task_id=task_id, inference_id="infer-consumer", input_id="frame-001"),
        )
        self.assertEqual(status, 201)
        status, _ = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "mock",
                "endpoint": "https://relay.example.test/edge",
                "metadata": {"ip_family": "ipv4", "network_type": "cellular"},
            },
        )
        self.assertEqual(status, 201)

    def test_o6_model_inference_endpoint_writes_events_and_detail_reads_them(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload())
        self.assertEqual(status, 201)

        status, created = self.client.request("POST", "/api/o6/archive/inference", self._o6_inference_payload())

        encoded = json.dumps(created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], relay_module.O6_MODEL_INFERENCE_SCHEMA)
        self.assertEqual(created["source"], "local_mock_inference")
        self.assertEqual(created["proof_status"], "not_proven")
        self.assertEqual(created["write_status"], "created")
        self.assertFalse(created["duplicate"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["primary_actions_enabled"])
        self.assertFalse(created["connects_cloud_production"])
        self.assertFalse(created["robot_control_executed"])
        self.assertFalse(created["real_gpu_model_connected"])
        self.assertFalse(created["real_external_model_api_connected"])
        self.assertFalse(created["real_model_inference_success"])
        self.assertTrue(created["archive_event_written"])
        self.assertEqual(created["result_summary"]["result_count"], 2)
        self.assertEqual(created["result_summary"]["created_count"], 2)
        self.assertEqual(created["result_summary"]["updated_count"], 0)
        self.assertIn("model_inference.elevator_door_state", created["result_summary"]["event_types"])
        self.assertIn("model_inference.floor_recognition", created["result_summary"]["event_types"])
        self.assertIn("real_gpu_model", created["not_proven"])
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "ttyUSB", "traceback"):
            self.assertNotIn(forbidden, encoded)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-001", token="")
        self.assertEqual(status, 200)
        event_by_type = {event["event_type"]: event for event in detail["task"]["events"]}
        self.assertIn("model_inference.elevator_door_state", event_by_type)
        self.assertIn("model_inference.floor_recognition", event_by_type)
        door_event = event_by_type["model_inference.elevator_door_state"]
        self.assertEqual(door_event["source"], "local_mock_inference")
        self.assertEqual(door_event["inference_id"], "infer-001")
        self.assertEqual(door_event["input_id"], "frame-001")
        self.assertEqual(door_event["result_type"], "elevator_door_state")
        self.assertEqual(door_event["result_value"], "unknown")
        self.assertEqual(door_event["confidence"], 0.0)
        self.assertEqual(door_event["evidence_ref"], "frame-001.jpg")
        self.assertIn("real_elevator_door_state", door_event["not_proven"])

    def test_o6_model_inference_endpoint_is_idempotent_and_supports_mixed_batches(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-inf-mixed"))
        self.assertEqual(status, 201)

        status, first = self.client.request(
            "POST",
            "/api/o6/archive/inference",
            self._o6_inference_payload(task_id="task-o6-inf-mixed", inference_id="infer-mixed", input_id="frame-a"),
        )
        self.assertEqual(status, 201)
        self.assertEqual(first["result_summary"]["created_count"], 2)

        mixed_payload = self._o6_inference_payload(
            task_id="task-o6-inf-mixed",
            inference_id="infer-mixed",
            input_id="frame-a",
        )
        mixed_payload["requested_outputs"] = ["elevator_door_state"]
        mixed_payload["inputs"].append(
            {
                "input_id": "frame-b",
                "input_type": "snapshot_ref",
                "evidence_ref": "frames/frame-b.jpg",
                "captured_at_ms": 1600,
                "metadata": {"camera": "front"},
            }
        )

        status, mixed = self.client.request("POST", "/api/o6/archive/inference", mixed_payload)
        self.assertEqual(status, 200)
        self.assertTrue(mixed["duplicate"])
        self.assertEqual(mixed["write_status"], "updated")
        self.assertEqual(mixed["result_summary"]["created_count"], 1)
        self.assertEqual(mixed["result_summary"]["updated_count"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-inf-mixed", token="")
        self.assertEqual(status, 200)
        inference_events = [
            event
            for event in detail["task"]["events"]
            if str(event.get("event_type", "")).startswith("model_inference.")
        ]
        keys = {(event["inference_id"], event["input_id"], event["result_type"]) for event in inference_events}
        self.assertEqual(len(keys), 3)
        self.assertIn(("infer-mixed", "frame-a", "elevator_door_state"), keys)
        self.assertIn(("infer-mixed", "frame-a", "floor_recognition"), keys)
        self.assertIn(("infer-mixed", "frame-b", "elevator_door_state"), keys)

    def test_o6_model_inference_endpoint_rejects_unknown_and_unauthorized_tasks(self):
        status, unknown = self.client.request(
            "POST",
            "/api/o6/archive/inference",
            self._o6_inference_payload(task_id="missing-task"),
        )
        self.assertEqual(status, 404)
        self.assertEqual(unknown["error"]["code"], "unknown_task")

        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-auth"))
        self.assertEqual(status, 201)
        payload = self._o6_inference_payload(task_id="task-o6-auth")
        payload["robot_id"] = "trashbot-other"
        status, unauthorized = self.client.request("POST", "/api/o6/archive/inference", payload)
        self.assertEqual(status, 403)
        self.assertEqual(unauthorized["error"]["code"], "unauthorized_task")

    def test_o6_model_inference_endpoint_rejects_bad_unsafe_oversized_and_out_of_window(self):
        status, _ = self.client.request("POST", "/api/o6/archive/tasks", self._o6_archive_task_payload(task_id="task-o6-inf-reject"))
        self.assertEqual(status, 201)

        status, bad_json = self.client.request("POST", "/api/o6/archive/inference", raw_body=b"{bad-json")
        self.assertEqual(status, 400)
        self.assertEqual(bad_json["error"]["code"], "malformed_json")

        status, non_object = self.client.request("POST", "/api/o6/archive/inference", raw_body=b"[]")
        self.assertEqual(status, 400)
        self.assertEqual(non_object["error"]["code"], "bad_request")

        missing = self._o6_inference_payload(task_id="task-o6-inf-reject")
        del missing["requested_outputs"]
        status, missing_body = self.client.request("POST", "/api/o6/archive/inference", missing)
        self.assertEqual(status, 400)
        self.assertEqual(missing_body["error"]["code"], "bad_request")

        unknown_output = self._o6_inference_payload(task_id="task-o6-inf-reject")
        unknown_output["requested_outputs"] = ["trash_detector"]
        status, unsupported = self.client.request("POST", "/api/o6/archive/inference", unknown_output)
        self.assertEqual(status, 400)
        self.assertEqual(unsupported["error"]["code"], "bad_request")

        too_many_inputs = self._o6_inference_payload(task_id="task-o6-inf-reject")
        too_many_inputs["inputs"] = [
            {
                "input_id": f"frame-{index:03d}",
                "input_type": "image_ref",
                "evidence_ref": f"frames/frame-{index:03d}.jpg",
                "captured_at_ms": 1500,
                "metadata": {},
            }
            for index in range(relay_module.O6_MODEL_INFERENCE_MAX_INPUTS + 1)
        ]
        status, oversized = self.client.request("POST", "/api/o6/archive/inference", too_many_inputs)
        self.assertEqual(status, 400)
        self.assertEqual(oversized["error"]["code"], "bad_request")
        self.assertIn("too large", oversized["error"]["message"].lower())

        unsafe = self._o6_inference_payload(task_id="task-o6-inf-reject")
        unsafe["inputs"][0]["metadata"] = {"note": "Authorization Bearer leaked-token"}
        status, unsafe_body = self.client.request("POST", "/api/o6/archive/inference", unsafe)
        self.assertEqual(status, 400)
        self.assertEqual(unsafe_body["error"]["code"], "bad_request")
        self.assertIn("unsafe", unsafe_body["error"]["message"].lower())

        real_claim = self._o6_inference_payload(task_id="task-o6-inf-reject")
        real_claim["gpu_connected"] = True
        status, claim_body = self.client.request("POST", "/api/o6/archive/inference", real_claim)
        self.assertEqual(status, 400)
        self.assertEqual(claim_body["error"]["code"], "bad_request")

        out_of_window = self._o6_inference_payload(task_id="task-o6-inf-reject")
        out_of_window["inputs"][0]["captured_at_ms"] = 2500
        status, window_body = self.client.request("POST", "/api/o6/archive/inference", out_of_window)
        self.assertEqual(status, 400)
        self.assertEqual(window_body["error"]["code"], "bad_request")
        self.assertIn("captured_at_ms", window_body["error"]["message"])

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-inf-reject", token="")
        self.assertEqual(status, 200)
        self.assertEqual(len(detail["task"]["events"]), 1)

    def test_o6_tunnel_heartbeat_endpoint_rejects_unsupported_provider(self):
        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "http",
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsupported", body["error"]["message"].lower())

    def test_o6_tunnel_heartbeat_endpoint_rejects_unsafe_metadata_and_endpoint(self):
        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "frp",
                "endpoint": "https://example.com/tunnel?token=leaked",
                "metadata": {"ip_family": "ipv4", "notes": "safe"},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "frp",
                "endpoint": "tcp://agent.local/",
                "metadata": {"notes": "token=leaked"},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "frp",
                "endpoint": "traceback",
                "metadata": {"ip_family": "ipv4", "notes": "safe"},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "frp",
                "endpoint": "tcp://agent.local/",
                "metadata": {"secret": "should not appear"},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

        status, body = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-001",
                "tunnel_provider": "frp",
                "endpoint": "tcp://agent.local/",
                "metadata": {"notes": "traceback observed"},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

    def test_o6_tunnel_heartbeat_persists_redacted_status_and_list_supports_filters(self):
        now_ms = int(time.time() * 1000)
        with mock.patch.object(relay_module, "_now", return_value=now_ms / 1000.0):
            status, first = self.client.request(
                "POST",
                "/api/o6/tunnel/heartbeat",
                {
                    "robot_id": "trashbot-online",
                    "tunnel_provider": "frp",
                    "endpoint": "https://tunnel.example.com/stream?region=cn",
                    "metadata": {
                        "ip_family": "ipv4",
                        "network_type": "cellular",
                        "region": "cn-hangzhou",
                        "notes": "clean heartbeat",
                    },
                },
            )
        self.assertEqual(status, 201)
        self.assertEqual(first["schema"], relay_module.O6_TUNNEL_STATUS_SCHEMA)
        self.assertEqual(first["source"], "local_mock_tunnel_status")
        self.assertFalse(first["real_tunnel_connected"])
        self.assertFalse(first["real_4g_connected"])
        self.assertFalse(first["connects_cloud_production"])
        self.assertFalse(first["robot_control_executed"])
        self.assertEqual(first["robot_id"], "trashbot-online")
        self.assertEqual(first["tunnel_provider"], "frp")
        self.assertEqual(first["endpoint"], "https://tunnel.example.com/stream")
        self.assertNotIn("region=cn", first["endpoint"])
        self.assertNotIn("token", first["endpoint"])
        self.assertEqual(first["metadata"]["ip_family"], "ipv4")
        self.assertEqual(first["metadata"]["notes"], "clean heartbeat")

        status, second = self.client.request(
            "POST",
            "/api/o6/tunnel/heartbeat",
            {
                "robot_id": "trashbot-offline",
                "tunnel_provider": "mock",
                "observed_at": int(time.time() * 1000) - 120000,
                "ttl_seconds": 60,
                "metadata": {"ip_family": "ipv6"},
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(second["robot_id"], "trashbot-offline")

        status, listing = self.client.request("GET", "/api/o6/tunnel/robots")
        self.assertEqual(status, 200)
        self.assertEqual(listing["schema"], relay_module.O6_TUNNEL_STATUS_SCHEMA)
        self.assertEqual(listing["query"]["status"], "all")
        self.assertEqual(listing["query"]["provider"], "all")
        self.assertLessEqual(len(listing["robots"]), 2)
        self.assertEqual(listing["robots"][0]["robot_id"], "trashbot-online")
        self.assertEqual(listing["robots"][1]["robot_id"], "trashbot-offline")
        self.assertEqual(listing["robots"][0]["status"], "online")
        self.assertEqual(listing["robots"][1]["status"], "offline")

        status, online_only = self.client.request("GET", "/api/o6/tunnel/robots?status=online")
        self.assertEqual(status, 200)
        self.assertEqual(len(online_only["robots"]), 1)
        self.assertEqual(online_only["robots"][0]["robot_id"], "trashbot-online")
        self.assertEqual(online_only["robots"][0]["status"], "online")
        self.assertEqual(online_only["query"]["status"], "online")

        status, offline_only = self.client.request("GET", "/api/o6/tunnel/robots?status=offline")
        self.assertEqual(status, 200)
        self.assertEqual(len(offline_only["robots"]), 1)
        self.assertEqual(offline_only["robots"][0]["robot_id"], "trashbot-offline")
        self.assertEqual(offline_only["robots"][0]["status"], "offline")

        status, provider_only = self.client.request("GET", "/api/o6/tunnel/robots?provider=mock")
        self.assertEqual(status, 200)
        self.assertEqual(len(provider_only["robots"]), 1)
        self.assertEqual(provider_only["robots"][0]["robot_id"], "trashbot-offline")

        status, detail = self.client.request("GET", "/api/o6/tunnel/robots/trashbot-online")
        self.assertEqual(status, 200)
        self.assertEqual(detail["robot_id"], "trashbot-online")
        self.assertEqual(detail["status"], "online")
        self.assertTrue(detail["schema_version"] > 0)

        status, missing = self.client.request("GET", "/api/o6/tunnel/robots/missing")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "not_found")

    def test_o6_tunnel_heartbeat_endpoint_rejects_invalid_query(self):
        status, invalid_limit = self.client.request("GET", "/api/o6/tunnel/robots?limit=-1")
        self.assertEqual(status, 400)
        self.assertEqual(invalid_limit["error"]["code"], "bad_request")

        status, invalid_status = self.client.request("GET", "/api/o6/tunnel/robots?status=bad")
        self.assertEqual(status, 400)
        self.assertEqual(invalid_status["error"]["code"], "bad_request")

        status, too_large = self.client.request(
            "GET",
            f"/api/o6/tunnel/robots?limit={relay_module.O6_TUNNEL_STATUS_MAX_LIST_LIMIT + 1}"
        )
        self.assertEqual(status, 200)
        self.assertLessEqual(too_large["query"]["limit"], relay_module.O6_TUNNEL_STATUS_MAX_LIST_LIMIT)

    def test_o6_consumer_tasks_endpoint_lists_descending_and_aggregates_summary_fields(self):
        self._o6_consumer_seed_rich_task("task-o6-consumer-rich")
        self._o6_consumer_seed_task(
            "task-o6-consumer-failed",
            started_at_ms=3000,
            finished_at_ms=3600,
            failure=True,
        )

        status, body = self.client.request(
            "GET",
            "/api/o6/consumer/tasks?view=summary&status=all&limit=10",
            token="",
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], relay_module.O6_CONSUMER_READ_SCHEMA)
        self.assertEqual(body["source"], "local_mock_consumer_read_model")
        self.assertEqual(body["consumer_status"], "local_mock_consumer_read_ready")
        self.assertEqual(body["view"], "summary")
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["connects_cloud_production"])
        self.assertFalse(body["robot_control_executed"])
        self.assertEqual(body["task_list"]["total_tasks"], 2)
        tasks = body["task_list"]["tasks"]
        self.assertEqual(tasks[0]["task_id"], "task-o6-consumer-failed")
        self.assertEqual(tasks[0]["task_status_summary"], "failed_mock")
        self.assertEqual(tasks[1]["task_id"], "task-o6-consumer-rich")
        self.assertEqual(tasks[1]["task_status_summary"], "completed_mock")
        self.assertEqual(tasks[1]["labeling_status"], "labeled")
        self.assertEqual(tasks[1]["inference_status"], "present")
        self.assertEqual(tasks[1]["tunnel_status_summary"], "online")
        self.assertGreaterEqual(tasks[1]["latest_event_at_ms"], 1500)

        status, filtered = self.client.request(
            "GET",
            "/api/o6/consumer/tasks?status=failed_mock&before_started_at_ms=4000&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(filtered["task_list"]["total_tasks"], 1)
        self.assertEqual(filtered["task_list"]["tasks"][0]["task_id"], "task-o6-consumer-failed")

    def test_o6_consumer_task_detail_supports_include_and_summary_view_without_losing_inference_fields(self):
        self._o6_consumer_seed_rich_task("task-o6-consumer-detail")

        status, body = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-consumer-detail?view=summary&include=trajectory,events,evidence,labeling,inference,tunnel",
            token="",
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["task_lookup"]["task_id"], "task-o6-consumer-detail")
        self.assertEqual(body["task_summary"]["task_id"], "task-o6-consumer-detail")
        self.assertEqual(body["trajectory"]["status"], "local_mock_archive_ready")
        self.assertTrue(body["trajectory"]["has_more"] or len(body["trajectory"]["frames"]) <= 2)
        self.assertEqual(body["events"]["status"], "local_mock_archive_ready")
        occurred = [event.get("occurred_at_ms", event.get("timestamp_ms")) for event in body["events"]["events"]]
        self.assertEqual(occurred, sorted(occurred))
        self.assertEqual(body["evidence"]["status"], "local_mock_archive_ready")
        self.assertEqual(body["labeling"]["labeling_status"], "labeled")
        self.assertEqual(body["inference"]["inference_status"], "present")
        inference_result = body["inference"]["results"][0]
        self.assertIn("inference_id", inference_result)
        self.assertIn("input_id", inference_result)
        self.assertIn("result_type", inference_result)
        self.assertIn("result_value", inference_result)
        self.assertIn("confidence", inference_result)
        self.assertIn("not_proven", inference_result)
        self.assertEqual(body["tunnel_status"]["temporal_alignment"], "latest_known_robot_snapshot_not_task_aligned")
        self.assertEqual(body["tunnel_status"]["latest_known_status"]["status"], "online")
        self.assertFalse(body["proof_boundary"]["safe_to_control"])

        status, slim = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-consumer-detail?view=summary&include=events",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertIn("events", slim)
        self.assertNotIn("trajectory", slim)
        self.assertNotIn("evidence", slim)
        self.assertNotIn("labeling", slim)
        self.assertNotIn("inference", slim)
        self.assertNotIn("tunnel_status", slim)

    def test_o6_consumer_tasks_endpoint_fail_closed_paths_and_missing_subviews(self):
        self._o6_consumer_seed_task("task-o6-consumer-empty", started_at_ms=5000, finished_at_ms=5600)

        status, empty_detail = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-consumer-empty?include=labeling,inference,tunnel",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(empty_detail["labeling"]["labeling_status"], "pending")
        self.assertEqual(empty_detail["labeling"]["label_count"], 0)
        self.assertEqual(empty_detail["inference"]["status"], "absent")
        self.assertEqual(empty_detail["inference"]["inference_status"], "absent")
        self.assertEqual(empty_detail["tunnel_status"]["status"], "blocked_not_proven")
        self.assertEqual(empty_detail["tunnel_status"]["tunnel_status_summary"], "unknown_not_proven")

        status, missing = self.client.request("GET", "/api/o6/consumer/tasks/missing-task", token="")
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "not_found")

        status, mismatch = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-consumer-empty?robot_id=trashbot-other",
            token="",
        )
        self.assertEqual(status, 403)
        self.assertEqual(mismatch["error"]["code"], "unauthorized_task")

        status, bad_include = self.client.request("GET", "/api/o6/consumer/tasks?include=bad_section", token="")
        self.assertEqual(status, 400)
        self.assertEqual(bad_include["error"]["code"], "bad_request")

        status, bad_view = self.client.request("GET", "/api/o6/consumer/tasks/task-o6-consumer-empty?view=wide", token="")
        self.assertEqual(status, 400)
        self.assertEqual(bad_view["error"]["code"], "bad_request")

        status, bad_limit = self.client.request("GET", "/api/o6/consumer/tasks?limit=99999", token="")
        self.assertEqual(status, 400)
        self.assertEqual(bad_limit["error"]["code"], "bad_request")

        status, unsafe_query = self.client.request("GET", "/api/o6/consumer/tasks?robot_id=Authorization%20Bearer%20leaked", token="")
        self.assertEqual(status, 400)
        self.assertEqual(unsafe_query["error"]["code"], "bad_request")

    def test_o7_realtime_elevator_snapshot_endpoint_is_public_readonly_and_fail_closed(self):
        with mock.patch.dict(os.environ, {"TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON": ""}):
            status, body = self.client.request("GET", "/api/o7/realtime-elevator/snapshot", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["schema"], "trashbot.o7.realtime_elevator_snapshot.v1")
        self.assertEqual(body["realtime_status"], "blocked_not_proven")
        self.assertEqual(body["snapshot_status"], "blocked_not_proven")
        self.assertFalse(body["cloud_runtime_fixture_connected"])
        self.assertFalse(body["real_realtime_api_connected"])
        self.assertFalse(body["real_ros2_tf_connected"])
        self.assertFalse(body["latency_lt_2s_proven"])
        self.assertFalse(body["route_membership"]["on_route"])
        self.assertFalse(body["route_membership"]["in_elevator_zone"])
        self.assertFalse(body["real_elevator_state_chain_connected"])
        self.assertFalse(body["floor_recognition_proven"])
        self.assertFalse(body["human_takeover_proven"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertFalse(body["robot_control_executed"])
        self.assertEqual(body["map_frame"]["frame_id"], "map")
        self.assertIsNone(body["robot_pose"])
        self.assertEqual(body["elevator_state_chain"]["samples"], [])
        self.assertIn("real_o7_realtime_cloud_stream", body["not_proven"])

    def test_o7_realtime_elevator_snapshot_endpoint_reads_safe_env_fixture_summary_only(self):
        fixture_path = pathlib.Path(self.tmp.name) / "o7_realtime_elevator_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.realtime_elevator_fixture.v1",
                    "map_ref": {
                        "id": "map-fixture-001",
                        "uri": "maps/office-floor.yaml",
                        "evidence_ref": "evidence/map-summary.json",
                    },
                    "map_frame": "map",
                    "robot_pose": {
                        "x_m": 1.25,
                        "y_m": 2.5,
                        "yaw_rad": 0.75,
                        "timestamp_ms": 1000,
                        "pose_source": "fixture_pose",
                        "evidence_ref": "pose/pose-001.json",
                    },
                    "pose_freshness": {
                        "timestamp_ms": 1000,
                        "age_ms": 350,
                        "evidence_ref": "pose/freshness-001.json",
                    },
                    "route_membership": {
                        "route_id": "route-fixture-001",
                        "status": "fixture_route_summary",
                        "evidence_ref": "route/membership-001.json",
                    },
                    "elevator_state_chain": [
                        {
                            "state": "waiting_for_elevator",
                            "status": "fixture_state",
                            "timestamp_ms": 1100,
                            "evidence_ref": "elevator/state-001.json",
                        },
                        {
                            "state": "inside_elevator",
                            "status": "fixture_state",
                            "timestamp_ms": 1200,
                            "evidence_ref": "elevator/state-002.json",
                        },
                    ],
                    "current_floor_evidence": {
                        "floor_label": "F1",
                        "confidence": 0.82,
                        "status": "fixture_floor",
                        "evidence_ref": "floor/current-001.json",
                    },
                    "human_takeover": {
                        "reason": "fixture_operator_assist_required",
                        "operator_action": "observe_only",
                        "status": "fixture_takeover",
                        "evidence_ref": "takeover/takeover-001.json",
                    },
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/realtime-elevator/snapshot", token="")

        encoded = json.dumps(body, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(body["snapshot_status"], "fixture_summary_ready")
        self.assertTrue(body["cloud_runtime_fixture_connected"])
        self.assertEqual(body["source_fixture_schema"], "trashbot.o7.realtime_elevator_fixture.v1")
        self.assertEqual(body["map_ref"]["id"], "map-fixture-001")
        self.assertEqual(body["map_frame"]["frame_id"], "map")
        self.assertEqual(body["robot_pose"]["x_m"], 1.25)
        self.assertEqual(body["robot_pose"]["y_m"], 2.5)
        self.assertEqual(body["robot_pose"]["yaw_rad"], 0.75)
        self.assertEqual(body["pose_freshness"]["timestamp_ms"], 1000.0)
        self.assertEqual(body["pose_freshness"]["age_ms"], 350.0)
        self.assertEqual(body["route_membership"]["route_id"], "route-fixture-001")
        self.assertEqual(body["elevator_state_chain"]["sample_count"], 2)
        self.assertEqual(body["elevator_state_chain"]["samples"][0]["state"], "waiting_for_elevator")
        self.assertEqual(body["current_floor_evidence"]["floor_label"], "F1")
        self.assertEqual(body["current_floor_evidence"]["confidence"], 0.82)
        self.assertEqual(body["human_takeover"]["reason"], "fixture_operator_assist_required")
        self.assertFalse(body["real_realtime_api_connected"])
        self.assertFalse(body["real_ros2_tf_connected"])
        self.assertFalse(body["latency_lt_2s_proven"])
        self.assertFalse(body["route_membership"]["on_route"])
        self.assertFalse(body["route_membership"]["in_elevator_zone"])
        self.assertFalse(body["real_elevator_state_chain_connected"])
        self.assertFalse(body["floor_recognition_proven"])
        self.assertFalse(body["human_takeover_proven"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertFalse(body["robot_control_executed"])
        for forbidden in ("Authorization", "Bearer", "/cmd_vel", "baudrate", "traceback"):
            self.assertNotIn(forbidden, encoded)

    def test_o7_realtime_elevator_snapshot_endpoint_blocks_unsafe_env_fixture(self):
        fixture_path = pathlib.Path(self.tmp.name) / "unsafe_o7_realtime_elevator_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.realtime_elevator_fixture.v1",
                    "route_membership": {"route_id": "unsafe-route", "on_route": True},
                    "robot_pose": {"evidence_ref": "Authorization: Bearer leaked-token"},
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/realtime-elevator/snapshot", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["snapshot_status"], "blocked_not_proven")
        self.assertEqual(body["input_status"]["failure_reason"], "unsafe_fixture_claim")
        self.assertFalse(body["cloud_runtime_fixture_connected"])
        self.assertIsNone(body["robot_pose"])
        self.assertEqual(body["elevator_state_chain"]["samples"], [])
        self.assertFalse(body["route_membership"]["on_route"])
        self.assertFalse(body["route_membership"]["in_elevator_zone"])

    def test_o7_realtime_elevator_snapshot_endpoint_sanitizes_malformed_numeric_fixture(self):
        fixture_path = pathlib.Path(self.tmp.name) / "malformed_numeric_o7_realtime_elevator_fixture.json"
        fixture_path.write_text(
            json.dumps(
                {
                    "schema": "trashbot.o7.realtime_elevator_fixture.v1",
                    "robot_pose": {
                        "x_m": "nan",
                        "y_m": "2.25",
                        "yaw_rad": "inf",
                        "timestamp_ms": "not-a-number",
                    },
                    "pose_freshness": {"timestamp_ms": "bad", "age_ms": "425"},
                    "elevator_state_chain": [
                        {"state": "waiting", "timestamp_ms": "bad"},
                    ],
                    "current_floor_evidence": {"floor_label": "F2", "confidence": "nan"},
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(os.environ, {"TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON": str(fixture_path)}):
            status, body = self.client.request("GET", "/api/o7/realtime-elevator/snapshot", token="")

        self.assertEqual(status, 200)
        self.assertEqual(body["snapshot_status"], "fixture_summary_ready")
        self.assertIsNone(body["robot_pose"]["x_m"])
        self.assertEqual(body["robot_pose"]["y_m"], 2.25)
        self.assertIsNone(body["robot_pose"]["yaw_rad"])
        self.assertIsNone(body["robot_pose"]["timestamp_ms"])
        self.assertIsNone(body["pose_freshness"]["timestamp_ms"])
        self.assertEqual(body["pose_freshness"]["age_ms"], 425.0)
        self.assertIsNone(body["elevator_state_chain"]["samples"][0]["timestamp_ms"])
        self.assertIsNone(body["current_floor_evidence"]["confidence"])
        self.assertFalse(body["real_realtime_api_connected"])
        self.assertFalse(body["real_ros2_tf_connected"])
        self.assertFalse(body["latency_lt_2s_proven"])
        self.assertFalse(body["route_membership"]["on_route"])
        self.assertFalse(body["route_membership"]["in_elevator_zone"])
        self.assertFalse(body["real_elevator_state_chain_connected"])
        self.assertFalse(body["floor_recognition_proven"])
        self.assertFalse(body["human_takeover_proven"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["delivery_success"])
        self.assertFalse(body["primary_actions_enabled"])
        self.assertFalse(body["robot_control_executed"])

    def command(self, command_id="cmd-0001", **extra):
        payload = {
            "protocol_version": PROTOCOL_VERSION,
            "id": command_id,
            "type": "collect",
            "expires_at": time.time() + 300.0,
            "payload": {"target": "trash_station", "trash_type": 0},
        }
        payload.update(extra)
        return payload

    def terminal_result(self, command_id="phone-terminal-001", **extra):
        payload = {
            "schema": "trashbot.cloud_command_terminal_result.v1",
            "schema_version": 1,
            "robot_id": "trashbot-001",
            "command_id": command_id,
            "terminal_result_type": "delivery_terminal",
            "terminal_result_state": "completed",
            "result_code": "task_terminal_completed",
            "error_code": "",
            "task_record_ref": "safe_task_record_ref",
            "evidence_ref": "safe_evidence_ref",
            "completed_at": "2026-05-26T07:08:00+08:00",
            "source": "robot_remote_bridge",
            "delivery_success": False,
            "real_world_delivery_proven": False,
        }
        payload.update(extra)
        return payload

    def test_command_status_ack_contract_and_idempotency(self):
        status, payload = self.client.request("POST", "/robots/trashbot-001/commands", self.command())
        self.assertEqual(status, 201)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["duplicate"])
        self.assertEqual(payload["command"]["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(payload["command"]["id"], "cmd-0001")
        self.assertEqual(payload["command"]["payload"]["target"], "trash_station")

        status, payload = self.client.request("POST", "/robots/trashbot-001/commands", self.command())
        self.assertEqual(status, 200)
        self.assertTrue(payload["duplicate"])

        status, payload = self.client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertEqual(payload["command"]["id"], "cmd-0001")

        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "remote collect command accepted",
                "updated_at": time.time(),
                "diagnostics": {"network": "relay_proof"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"]["robot_id"], "trashbot-001")

        status, payload = self.client.request("GET", "/robots/trashbot-001/status")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"]["state"], "delivering")

        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/commands/cmd-0001/ack",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "acked",
                "message": "collect command submitted",
                "updated_at": time.time(),
                "result": {"behavior": "submitted"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["ack"]["command_id"], "cmd-0001")
        self.assertEqual(payload["ack"]["state"], "acked")

        status, payload = self.client.request("GET", "/robots/trashbot-001/commands/cmd-0001/ack")
        self.assertEqual(status, 200)
        self.assertEqual(payload["ack"]["result"]["behavior"], "submitted")

        status, payload = self.client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=cmd-0001")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["command"])

    def test_cloud_phone_command_api_collect_receipt_and_robot_polling_contract(self):
        status, payload = self.client.request(
            "POST",
            "/api/commands/collect",
            {
                "robot_id": "trashbot-001",
                "idempotency_key": "phone-collect-001",
                "payload": {"target": "trash_station", "trash_type": 0},
            },
        )
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["capability"], "cloud_phone_command_api")
        self.assertEqual(payload["evidence_boundary"], "software_proof_docker_cloud_phone_command_api_gate")
        self.assertEqual(payload["ack_semantics"], "queued_not_delivery_success")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["duplicate"])
        self.assertEqual(payload["command_id"], "phone-collect-001")
        self.assertEqual(payload["command_type"], "collect")
        self.assertEqual(payload["queue_sequence"], 1)
        for forbidden in ("phone-token", "Authorization", "Bearer", "/cmd_vel", "serial", "UART", "WAVE ROVER"):
            self.assertNotIn(forbidden, encoded)

        status, next_payload = self.client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertEqual(next_payload["command"]["id"], "phone-collect-001")
        self.assertEqual(next_payload["command"]["type"], "collect")
        self.assertEqual(next_payload["command"]["payload"]["target"], "trash_station")

    def test_cloud_phone_command_api_duplicate_confirm_and_cancel_receipts(self):
        for path, command_id, expected_type in (
            ("/api/commands/confirm-dropoff", "phone-confirm-001", "confirm_dropoff"),
            ("/api/commands/cancel", "phone-cancel-001", "cancel"),
        ):
            body = {"robot_id": "trashbot-001", "command_id": command_id, "payload": {"reason": "phone_submit"}}
            status, payload = self.client.request("POST", path, body)
            self.assertEqual(status, 201, path)
            self.assertEqual(payload["command_type"], expected_type)
            self.assertFalse(payload["delivery_success"])

            status, duplicate = self.client.request("POST", path, body)
            self.assertEqual(status, 200, path)
            self.assertTrue(duplicate["duplicate"])
            self.assertEqual(duplicate["duplicate_info"]["state"], "command_duplicate_deduped")
            self.assertEqual(duplicate["command_id"], command_id)

    def test_cloud_phone_command_api_fails_closed_without_sensitive_leaks(self):
        cases = (
            (
                "/api/commands/collect",
                {"robot_id": "trashbot-001", "payload": {"target": "trash_station"}},
                "",
                401,
                "auth_failed",
            ),
            (
                "/api/commands/cmd_vel",
                {"robot_id": "trashbot-001", "payload": {"target": "trash_station", "topic": "/cmd_vel"}},
                None,
                400,
                "bad_request",
            ),
            (
                "/api/commands/collect",
                {"payload": {"target": "trash_station"}, "Authorization": "Bearer hidden"},
                None,
                400,
                "bad_request",
            ),
            (
                "/api/commands/collect",
                {"robot_id": "trashbot-001", "payload": {}},
                None,
                400,
                "bad_request",
            ),
        )
        for path, body, token, expected_status, expected_code in cases:
            status, payload = self.client.request("POST", path, body, token=token)
            encoded = json.dumps(payload, ensure_ascii=False)
            self.assertEqual(status, expected_status, path)
            self.assertEqual(payload["error"]["code"], expected_code)
            for forbidden in (
                "phone-token",
                "Authorization",
                "Bearer",
                "hidden",
                "/cmd_vel",
                "raw state path",
                "ROS topic",
                "serial",
                "UART",
                "WAVE ROVER",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_phone_command_api_store_failure_returns_safe_503(self):
        class FailingStore:
            def submit_command(self, robot_id, payload):
                raise OSError("raw state path /cmd_vel Authorization Bearer hidden")

        server = relay_module.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            relay_module.make_handler(
                FailingStore(),
                relay_module.FileBackedO6CloudArchiveStore(pathlib.Path(self.tmp.name) / "unused_o6_archive_state.json"),
                "phone-token",
            ),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}")
        try:
            status, payload = client.request(
                "POST",
                "/api/commands/collect",
                {
                    "robot_id": "trashbot-001",
                    "idempotency_key": "phone-store-failure-001",
                    "payload": {"target": "trash_station"},
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 503)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "command_store_unavailable")
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "hidden",
            "/cmd_vel",
            "raw state path",
            "serial",
            "UART",
            "WAVE ROVER",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_result_reconciliation_lifecycle_states_are_phone_safe(self):
        status, receipt = self.client.request(
            "POST",
            "/api/commands/collect",
            {
                "robot_id": "trashbot-001",
                "idempotency_key": "phone-result-queued-001",
                "payload": {"target": "trash_station", "trash_type": 0},
            },
        )
        self.assertEqual(status, 201)
        command_id = receipt["command_id"]

        status, payload = self.client.request(
            "GET",
            f"/api/commands/{command_id}/result?robot_id=trashbot-001",
        )
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(payload["schema"], "trashbot.cloud_command_result_reconciliation.v2")
        self.assertEqual(payload["capability"], "cloud_command_result_reconciliation")
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_result_reconciliation_gate",
        )
        self.assertEqual(payload["command_state"], "queued")
        self.assertEqual(payload["ack_state"], "none")
        self.assertEqual(payload["result_state"], "queued")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["primary_actions_enabled"])

        self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "command envelope is being handled",
                "updated_at": time.time(),
            },
        )
        status, payload = self.client.request(
            "GET",
            f"/api/commands/{command_id}/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_state"], "processing")
        self.assertEqual(payload["result_state"], "processing")
        self.assertFalse(payload["delivery_success"])

        self.client.request(
            "POST",
            f"/robots/trashbot-001/commands/{command_id}/ack",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "acked",
                "message": "behavior accepted envelope",
                "updated_at": time.time(),
                "result": {"behavior": "submitted", "internal": "not a delivery proof"},
            },
        )
        status, payload = self.client.request(
            "GET",
            f"/api/commands/{command_id}/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_state"], "terminal_result_pending")
        self.assertEqual(payload["ack_state"], "acked")
        self.assertEqual(payload["result_state"], "terminal_result_pending")
        self.assertIn("not_delivery", payload["ack_semantics"])
        self.assertFalse(payload["delivery_success"])

        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "/cmd_vel",
            "raw state path",
            "DB",
            "queue URL",
            "ROS topic",
            "serial",
            "UART",
            "WAVE ROVER",
            "traceback",
            "checksum",
        ):
            self.assertNotIn(forbidden, encoded)
            self.assertNotIn(forbidden, json.dumps(payload, ensure_ascii=False))

    def test_cloud_command_result_reconciliation_missing_and_expired_are_not_success(self):
        status, payload = self.client.request(
            "GET",
            "/api/commands/not-present/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_state"], "missing_or_expired")
        self.assertEqual(payload["result_state"], "missing_or_expired")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["safe_to_control"])

        status, receipt = self.client.request(
            "POST",
            "/api/commands/cancel",
            {
                "robot_id": "trashbot-001",
                "command_id": "phone-result-expired-001",
                "expires_at": time.time() - 1.0,
                "payload": {"reason": "stale_user_intent"},
            },
        )
        self.assertEqual(status, 201)
        status, payload = self.client.request(
            "GET",
            f"/api/commands/{receipt['command_id']}/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["command_state"], "missing_or_expired")
        self.assertEqual(payload["ack_state"], "none")
        self.assertFalse(payload["primary_actions_enabled"])

    def test_cloud_command_result_reconciliation_store_unavailable_is_same_schema(self):
        class FailingStore:
            def get_command_result_reconciliation(self, robot_id, command_id):
                raise OSError("raw state path /cmd_vel Authorization Bearer hidden DB queue URL traceback checksum")

            def state_store_writable(self):
                return False

        server = relay_module.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            relay_module.make_handler(
                FailingStore(),
                relay_module.FileBackedO6CloudArchiveStore(pathlib.Path(self.tmp.name) / "unused_o6_archive_state.json"),
                "phone-token",
            ),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}")
        try:
            status, payload = client.request(
                "GET",
                "/api/commands/phone-store-down/result?robot_id=trashbot-001",
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 503)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["schema"], "trashbot.cloud_command_result_reconciliation.v2")
        self.assertEqual(payload["command_state"], "store_unavailable")
        self.assertEqual(payload["ack_state"], "unavailable")
        self.assertEqual(payload["result_state"], "store_unavailable")
        self.assertFalse(payload["delivery_success"])
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "hidden",
            "/cmd_vel",
            "raw state path",
            "DB",
            "queue URL",
            "ROS topic",
            "serial",
            "UART",
            "WAVE ROVER",
            "traceback",
            "checksum",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_terminal_result_file_store_recorded_pending_idempotent_conflict_and_missing(self):
        status, receipt = self.client.request(
            "POST",
            "/api/commands/collect",
            {
                "robot_id": "trashbot-001",
                "idempotency_key": "phone-terminal-001",
                "payload": {"target": "trash_station", "trash_type": 0},
            },
        )
        self.assertEqual(status, 201)
        command_id = receipt["command_id"]

        self.client.request(
            "POST",
            f"/robots/trashbot-001/commands/{command_id}/ack",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "acked",
                "message": "envelope terminal ack only",
                "updated_at": time.time(),
                "result": {"delivery_success": False},
            },
        )
        status, pending = self.client.request(
            "GET",
            f"/api/commands/{command_id}/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(pending["result_state"], "terminal_result_pending")
        self.assertFalse(pending["delivery_success"])

        status, recorded = self.client.request(
            "POST",
            f"/robots/trashbot-001/commands/{command_id}/terminal-result",
            self.terminal_result(command_id),
        )
        encoded = json.dumps(recorded, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertEqual(recorded["schema"], "trashbot.cloud_command_terminal_result.v1")
        self.assertEqual(recorded["capability"], "cloud_command_terminal_result")
        self.assertEqual(recorded["terminal_result_state"], "terminal_result_recorded")
        self.assertEqual(recorded["terminal_result_type"], "delivery_terminal")
        self.assertEqual(recorded["result_code"], "task_terminal_completed")
        self.assertFalse(recorded["delivery_success"])
        self.assertFalse(recorded["safe_to_control"])
        self.assertFalse(recorded["primary_actions_enabled"])
        self.assertFalse(recorded["real_world_delivery_proven"])

        status, reconciliation = self.client.request(
            "GET",
            f"/api/commands/{command_id}/result?robot_id=trashbot-001",
        )
        self.assertEqual(status, 200)
        self.assertEqual(reconciliation["schema"], "trashbot.cloud_command_result_reconciliation.v2")
        self.assertEqual(reconciliation["command_state"], "terminal_result_recorded")
        self.assertEqual(reconciliation["result_state"], "terminal_result_recorded")
        self.assertEqual(reconciliation["terminal_result_type"], "delivery_terminal")
        self.assertEqual(reconciliation["result_code"], "task_terminal_completed")
        self.assertFalse(reconciliation["delivery_success"])
        self.assertFalse(reconciliation["safe_to_control"])
        self.assertFalse(reconciliation["primary_actions_enabled"])
        self.assertFalse(reconciliation["real_world_delivery_proven"])

        reloaded = FileBackedRelayStore(self.state_path)
        persisted = reloaded.get_command_result_reconciliation("trashbot-001", command_id)
        self.assertEqual(persisted["result_state"], "terminal_result_recorded")
        self.assertEqual(persisted["result_code"], "task_terminal_completed")

        status, duplicate = self.client.request(
            "POST",
            f"/robots/trashbot-001/commands/{command_id}/terminal-result",
            self.terminal_result(command_id),
        )
        self.assertEqual(status, 200)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["terminal_result_state"], "terminal_result_recorded")

        status, conflict = self.client.request(
            "POST",
            f"/robots/trashbot-001/commands/{command_id}/terminal-result",
            self.terminal_result(command_id, result_code="task_terminal_failed", error_code="safe_error_code"),
        )
        self.assertEqual(status, 409)
        self.assertEqual(conflict["terminal_result_state"], "terminal_result_conflict")
        self.assertEqual(conflict["result_code"], "task_terminal_completed")

        status, missing = self.client.request(
            "POST",
            "/robots/trashbot-001/commands/not-present/terminal-result",
            self.terminal_result("not-present"),
        )
        self.assertEqual(status, 404)
        self.assertEqual(missing["terminal_result_state"], "terminal_result_missing")
        self.assertFalse(missing["delivery_success"])

        for payload in (recorded, reconciliation, duplicate, conflict, missing):
            encoded = json.dumps(payload, ensure_ascii=False)
            self.assertFalse(payload["delivery_success"])
            self.assertFalse(payload["safe_to_control"])
            self.assertFalse(payload["primary_actions_enabled"])
            for forbidden in (
                "phone-token",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "raw state path",
                "DB",
                "queue URL",
                "ROS topic",
                "serial",
                "UART",
                "WAVE ROVER",
                "traceback",
                "checksum",
            ):
                self.assertNotIn(forbidden, encoded)
        self.assertNotIn("checksum", encoded)

    def test_cloud_command_terminal_result_sqlite_store_persists_recorded(self):
        sqlite_path = pathlib.Path(self.tmp.name) / "terminal_result.sqlite"
        server = build_server("127.0.0.1", 0, sqlite_path, "phone-token", state_backend="sqlite")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}")
        try:
            status, receipt = client.request(
                "POST",
                "/api/commands/confirm-dropoff",
                {
                    "robot_id": "trashbot-001",
                    "command_id": "sqlite-terminal-001",
                    "payload": {"reason": "dropoff_confirmed_by_robot"},
                },
            )
            self.assertEqual(status, 201)
            status, recorded = client.request(
                "POST",
                "/robots/trashbot-001/commands/sqlite-terminal-001/terminal-result",
                self.terminal_result(
                    receipt["command_id"],
                    terminal_result_type="dropoff_terminal",
                    result_code="dropoff_terminal_completed",
                ),
            )
            self.assertEqual(status, 201)
            self.assertEqual(recorded["terminal_result_state"], "terminal_result_recorded")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        reloaded = SQLiteRelayStore(sqlite_path)
        reconciliation = reloaded.get_command_result_reconciliation("trashbot-001", "sqlite-terminal-001")
        self.assertEqual(reconciliation["result_state"], "terminal_result_recorded")
        self.assertEqual(reconciliation["terminal_result_type"], "dropoff_terminal")
        self.assertEqual(reconciliation["result_code"], "dropoff_terminal_completed")
        self.assertFalse(reconciliation["delivery_success"])

    def test_cloud_command_terminal_result_store_unavailable_is_phone_safe(self):
        class FailingStore:
            def post_terminal_result(self, robot_id, command_id, payload):
                raise OSError("raw state path /cmd_vel Authorization Bearer hidden DB queue URL traceback checksum")

        server = relay_module.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            relay_module.make_handler(
                FailingStore(),
                relay_module.FileBackedO6CloudArchiveStore(pathlib.Path(self.tmp.name) / "unused_o6_archive_state.json"),
                "phone-token",
            ),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}")
        try:
            status, payload = client.request(
                "POST",
                "/robots/trashbot-001/commands/store-down/terminal-result",
                self.terminal_result("store-down"),
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 503)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["schema"], "trashbot.cloud_command_terminal_result.v1")
        self.assertEqual(payload["terminal_result_state"], "store_unavailable")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["primary_actions_enabled"])
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "hidden",
            "/cmd_vel",
            "raw state path",
            "DB",
            "queue URL",
            "ROS topic",
            "serial",
            "UART",
            "WAVE ROVER",
            "traceback",
            "checksum",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_health_and_readiness_are_phone_safe(self):
        status, payload = self.client.request("GET", "/healthz", token="")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(payload["evidence_boundary"], "software_proof_docker_deploy")

        status, payload = self.client.request("GET", "/readyz", token="")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["checks"]["protocol"])
        self.assertTrue(payload["checks"]["credential_gate"])
        self.assertTrue(payload["checks"]["state_store"])
        self.assertTrue(payload["checks"]["phone_safe_failure"])

        encoded = json.dumps(payload, ensure_ascii=False)
        for forbidden in ("phone-token", "Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate"):
            self.assertNotIn(forbidden, encoded)

    def test_preflight_endpoint_blocks_local_placeholders_without_leaks(self):
        status, payload = self.client.request("GET", "/preflightz", token="")
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(status, 503)
        self.assertFalse(payload["production_ready"])
        self.assertEqual(payload["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
        self.assertGreaterEqual(payload["blocked_count"], 1)
        self.assertIn("Docker/local 软件 proof", payload["safe_summary"])
        self.assertIn("real_cloud", payload["not_proven"])
        for forbidden in ("phone-token", "Authorization", "Bearer", "/cmd_vel", "ttyUSB", "baudrate"):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_relay_serves_mobile_web_shell_without_auth(self):
        for path, marker, content_type in (
            ("/", b"rober", "text/html"),
            ("/index.html", b"rober", "text/html"),
            ("/app.js", b"mobile_web", "application/javascript"),
            ("/styles.css", b":root", "text/css"),
            ("/manifest.webmanifest", b"short_name", "application/manifest+json"),
            ("/service-worker.js", b"isControlOrDynamicRequest", "application/javascript"),
            ("/offline.html", b"software_proof_docker_mobile_web_entrypoint_gate", "text/html"),
            ("/icon-192.svg", b"<svg", "image/svg+xml"),
            ("/icon-512.svg", b"<svg", "image/svg+xml"),
        ):
            status, headers, body = self.client.raw_request("GET", path, token="")
            self.assertEqual(status, 200, path)
            self.assertIn(content_type, headers.get("Content-Type", ""))
            self.assertIn(marker, body)
            self.assertEqual(
                headers.get("X-Trashbot-Evidence-Boundary"),
                "software_proof_docker_cloud_hosted_mobile_web_gate",
            )
            self.assertNotIn(str(REPO_ROOT).encode("utf-8"), body)

    def test_mobile_web_static_does_not_cover_api_or_probe_routes(self):
        status, payload = self.client.request("GET", "/api/status", token="")
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "status_missing")
        self.assertEqual(payload["robot_id"], "trashbot-001")
        self.assertFalse(payload["can_collect"])
        self.assertFalse(payload["phone_readiness"]["can_continue"])
        self.assertFalse(payload["phone_readiness"]["command_safety"]["actions"]["start"]["enabled"])
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate",
        )

        status, payload = self.client.request("GET", "/api/diagnostics", token="")
        self.assertEqual(status, 200)
        self.assertEqual(payload["overall_status"], "blocked")
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate",
        )
        self.assertIn("real_phone_device_browser", payload["not_proven"])

        status, payload = self.client.request("GET", "/api/collect", token="")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "not_found")

        status, payload = self.client.request("GET", "/healthz", token="")
        self.assertEqual(status, 200)
        self.assertEqual(payload["service"], "remote_cloud_relay")

        status, payload = self.client.request("GET", "/robots/trashbot-001/status")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "status_missing")

    def test_cloud_command_lifecycle_replay_acceptance_packet_http_export_is_support_safe(self):
        status, payload = self.client.request(
            "GET",
            "/api/support/cloud-command-lifecycle-replay-acceptance-packet-export",
            token="",
        )
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_http_export",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate",
        )
        self.assertEqual(
            payload["source_cli_export_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_cli_export",
        )
        self.assertEqual(
            payload["source_cli_export_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate",
        )
        self.assertEqual(
            payload["source_packet_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate",
        )
        self.assertEqual(payload["ack_semantics"], "accepted_processing_only_not_delivery_success")
        self.assertEqual(payload["terminal_result_status"], "terminal_result_pending")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["safe_id_status"], "pending_owner_material_not_proven")
        self.assertEqual(payload["source_cli_export"]["safe_command_id"], payload["safe_command_id"])
        self.assertEqual(payload["source_cli_export"]["source_packet"]["safe_evidence_ref"], payload["safe_evidence_ref"])
        self.assertIn("owner_handoff", payload)
        self.assertIn("next_required_evidence", payload)
        self.assertEqual(payload["redaction_status"], "passed")
        self.assertTrue(payload["read_only"])
        self.assertTrue(payload["phone_safe"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["persistence_updates_allowed"])
        self.assertFalse(payload["command_replay_allowed"])
        self.assertFalse(payload["command_resubmit_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertIn("not_proven", payload)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("not delivery success", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_http_export_has_no_state_side_effects(self):
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "state exists before support export",
                "updated_at": time.time(),
            },
        )
        self.assertEqual(status, 200)
        before = self.state_path.read_text(encoding="utf-8")

        status, payload = self.client.request(
            "GET",
            "/api/support/cloud-command-lifecycle-replay-acceptance-packet-export",
            token="",
        )
        after = self.state_path.read_text(encoding="utf-8")

        self.assertEqual(status, 200)
        self.assertEqual(payload["capability"], "cloud_command_lifecycle_replay_acceptance_packet_http_export")
        self.assertEqual(before, after)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_alias_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate",
        )
        self.assertEqual(
            payload["source_http_export_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate",
        )
        self.assertEqual(payload["ack_semantics"], "accepted_processing_only_not_delivery_success")
        self.assertEqual(payload["terminal_result_status"], "terminal_result_pending")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["redaction_status"], "passed")
        self.assertIn("owner_handoff", payload)
        self.assertIn("next_required_evidence", payload)
        self.assertIn("safe_copy", payload)
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["command_replay_allowed"])
        self.assertFalse(payload["command_resubmit_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(
            diagnostics_payload[
                "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_summary"
            ]["safe_evidence_ref"],
            payload["safe_evidence_ref"],
        )
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not HIL", encoded)
        self.assertIn("not PR #5 resolved", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_owner_response_review_decision_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate",
        )
        self.assertEqual(
            payload["source_intake_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate",
        )
        self.assertEqual(payload["review_decision"], "blocked_not_proven")
        self.assertEqual(
            payload["owner_response_status"],
            "pending_safe_owner_response_material_not_proven",
        )
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertIn("owner_response_material_pending", payload["review_reasons"])
        self.assertIn("verified_terminal_delivery_dropoff_or_cancel_result", payload["next_required_evidence"])
        self.assertEqual(payload["source_boundary"], "safe_owner_response_intake_only")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["command_replay_allowed"])
        self.assertFalse(payload["command_resubmit_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(
            diagnostics_payload[
                "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_summary"
            ]["safe_evidence_ref"],
            payload["safe_evidence_ref"],
        )
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate",
        )
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision",
        )
        self.assertEqual(
            payload["source_review_decision_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate",
        )
        self.assertEqual(payload["review_handoff_status"], "blocked_pending_owner")
        self.assertEqual(payload["review_decision"], "blocked_not_proven")
        self.assertEqual(payload["handoff_owner"], "field_owner")
        self.assertEqual(payload["handoff_reason"], "owner_response_material_pending")
        self.assertEqual(payload["owner_response_status"], "pending_safe_owner_response_material_not_proven")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertIn("verified_terminal_delivery_dropoff_or_cancel_result", payload["next_required_evidence"])
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", payload["blocker_summary"])
        self.assertEqual(payload["source_boundary"], "safe_owner_response_review_decision_only")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["command_replay_allowed"])
        self.assertFalse(payload["command_resubmit_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(diagnostics_summary["safe_evidence_ref"], payload["safe_evidence_ref"])
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate",
        )
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff",
        )
        self.assertEqual(
            payload["source_handoff_evidence_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate",
        )
        self.assertEqual(payload["source_boundary"], "safe_owner_response_review_handoff_only")
        self.assertEqual(payload["ack_intake_status"], "acknowledged_not_proven")
        self.assertEqual(payload["reviewer_ack_status"]["status"], "acknowledged_not_proven")
        self.assertEqual(payload["source_handoff_status"], "blocked_pending_owner")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["routing"]["owner"], "field_owner")
        self.assertEqual(payload["routing"]["support"], "support_triage")
        self.assertEqual(payload["routing"]["reviewer"], "pr5_reviewer")
        self.assertIn("reviewer_ack_metadata_only", payload["ack_reasons"])
        self.assertIn("verified_terminal_delivery_dropoff_or_cancel_result", payload["next_required_evidence"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["persistence_updates_allowed"])
        self.assertFalse(payload["command_replay_allowed"])
        self.assertFalse(payload["command_resubmit_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(diagnostics_summary["safe_evidence_ref"], payload["safe_evidence_ref"])
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate",
        )
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake",
        )
        self.assertEqual(payload["source_ack_intake_status"], "acknowledged_not_proven")
        self.assertEqual(
            payload["reviewer_ack_review_decision"],
            "reviewer_ack_accepted_for_support_review_not_proven",
        )
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["routing"]["owner"], "field_owner")
        self.assertEqual(payload["routing"]["support"], "support_triage")
        self.assertEqual(payload["routing"]["reviewer"], "pr5_reviewer")
        self.assertIn("source_reviewer_ack_intake_safe", payload["decision_reasons"])
        self.assertIn("verified_terminal_delivery_dropoff_or_cancel_result", payload["next_required_evidence"])
        self.assertEqual(payload["pr5_review_thread"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["pr5_material_status"], "hardware_material_pending")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(diagnostics_summary["evidence_ref"], payload["evidence_ref"])
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_states_are_not_proven(self):
        base_ack_intake = (
            relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_payload()
        )
        cases = [
            (
                {
                    "ack_intake_status": "needs_reassignment_not_proven",
                    "status": "needs_reassignment_not_proven",
                    "reassignment_required": True,
                },
                "reviewer_ack_needs_reassignment_not_proven",
            ),
            (
                {"pr5_material_status": "missing_material_not_proven"},
                "reviewer_ack_missing_material_not_proven",
            ),
            (
                {"expected_evidence_ref": "different-safe-ref"},
                "reviewer_ack_evidence_ref_mismatch_not_proven",
            ),
            (
                {
                    "ack_intake_status": "rejected_unsafe_not_proven",
                    "status": "rejected_unsafe_not_proven",
                    "rejected_reviewer_ack": True,
                },
                "reviewer_ack_rejected_unsafe_not_proven",
            ),
            (
                {"ack_intake_status": "", "status": "", "safe_command_id": "", "safe_evidence_ref": ""},
                "blocked_missing_reviewer_ack_intake_not_proven",
            ),
        ]
        for extra_fields, expected_decision in cases:
            with self.subTest(expected_decision=expected_decision):
                source_ack_intake = dict(base_ack_intake, **extra_fields)
                payload = (
                    relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_payload(
                        source_ack_intake=source_ack_intake
                    )
                )
                encoded = json.dumps(payload, ensure_ascii=False)

                self.assertEqual(payload["reviewer_ack_review_decision"], expected_decision)
                self.assertIn(expected_decision, payload["supported_review_decisions"])
                self.assertEqual(payload["pr5_review_thread"], "PRRT_kwDOSWB9286CJ3tX")
                self.assertEqual(payload["pr5_material_status"], "hardware_material_pending")
                self.assertFalse(payload["delivery_success"])
                self.assertFalse(payload["primary_actions_enabled"])
                self.assertFalse(payload["safe_to_control"])
                self.assertFalse(payload["ack_post_allowed"])
                self.assertFalse(payload["cursor_updates_allowed"])
                self.assertFalse(payload["review_action_allowed"])
                self.assertFalse(payload["github_action_allowed"])
                self.assertFalse(payload["robot_command_side_effects_allowed"])
                self.assertFalse(payload["verified_terminal_result"])
                self.assertNotIn("delivery_success\": true", encoded)
                self.assertNotIn("primary_actions_enabled\": true", encoded)
                self.assertNotIn("safe_to_control\": true", encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["schema"],
            "trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary.v1",
        )
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate",
        )
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision",
        )
        self.assertEqual(
            payload["source_proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate",
        )
        self.assertEqual(
            payload["source_review_decision"],
            "reviewer_ack_accepted_for_support_review_not_proven",
        )
        self.assertEqual(
            payload["review_handoff_status"],
            "accepted_for_reviewer_ack_review_handoff_not_proven",
        )
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["handoff_owner"], "field_owner")
        self.assertEqual(payload["support_route"], "support_triage")
        self.assertEqual(payload["reviewer_route"], "pr5_reviewer")
        self.assertEqual(payload["handoff_reason"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", payload["blocker_status"])
        self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["phone_browser_proof"], "not true phone/browser proof")
        self.assertEqual(payload["okr_progress_effect"], "no OKR percentage lift")
        self.assertIn("not verified terminal result", payload["non_claims"])
        self.assertIn("not delivery success", payload["non_claims"])
        self.assertIn("verified_terminal_delivery_dropoff_or_cancel_result", payload["next_required_evidence"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["terminal_result_verified"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertFalse(payload["pr5_resolved"])
        self.assertEqual(diagnostics_summary["evidence_ref"], payload["evidence_ref"])
        self.assertIn(
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary",
            encoded,
        )
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_states_are_not_proven(self):
        base_review_decision = (
            relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_payload()
        )
        cases = [
            (
                {"reviewer_ack_review_decision": "reviewer_ack_needs_reassignment_not_proven"},
                "reviewer_ack_review_handoff_needs_reassignment_not_proven",
            ),
            (
                {"reviewer_ack_review_decision": "reviewer_ack_missing_material_not_proven"},
                "reviewer_ack_review_handoff_missing_material_not_proven",
            ),
            (
                {"reviewer_ack_review_decision": "reviewer_ack_rejected_unsafe_not_proven"},
                "reviewer_ack_review_handoff_rejected_unsafe_not_proven",
            ),
            (
                {"reviewer_ack_review_decision": ""},
                "blocked_missing_source_reviewer_ack_review_decision_not_proven",
            ),
            (
                {"expected_evidence_ref": "different-safe-ref"},
                "reviewer_ack_review_handoff_evidence_ref_mismatch_not_proven",
            ),
        ]
        for extra_fields, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                source_review_decision = dict(base_review_decision, **extra_fields)
                payload = (
                    relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_payload(
                        source_review_decision=source_review_decision
                    )
                )
                encoded = json.dumps(payload, ensure_ascii=False)

                self.assertEqual(payload["review_handoff_status"], expected_status)
                self.assertIn(expected_status, payload["supported_review_handoff_statuses"])
                self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
                self.assertIn("hardware_material_pending", payload["blocker_status"])
                self.assertFalse(payload["delivery_success"])
                self.assertFalse(payload["primary_actions_enabled"])
                self.assertFalse(payload["safe_to_control"])
                self.assertFalse(payload["terminal_result_verified"])
                self.assertFalse(payload["review_action_allowed"])
                self.assertFalse(payload["github_action_allowed"])
                self.assertFalse(payload["robot_command_side_effects_allowed"])
                self.assertFalse(payload["verified_terminal_result"])
                self.assertNotIn("delivery_success\": true", encoded)
                self.assertNotIn("primary_actions_enabled\": true", encoded)
                self.assertNotIn("safe_to_control\": true", encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["schema"],
            "trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary.v1",
        )
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate",
        )
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff",
        )
        self.assertEqual(
            payload["source_proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate",
        )
        self.assertEqual(
            payload["source_review_handoff_status"],
            "accepted_for_reviewer_ack_review_handoff_not_proven",
        )
        self.assertEqual(payload["followup_status"], "reviewer_ack_followup_pending_not_proven")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["followup_owner"], "field_owner")
        self.assertEqual(payload["support_route"], "support_triage")
        self.assertEqual(payload["reviewer_route"], "pr5_reviewer")
        self.assertEqual(payload["escalation_route"], "product_owner_or_ceo_decision_queue")
        self.assertEqual(payload["escalation_reason"], "PRRT_kwDOSWB9286CJ3tX hardware_material_pending")
        self.assertIn("hardware_material_pending", payload["blocker_status"])
        self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["phone_browser_proof"], "not true phone/browser proof")
        self.assertEqual(payload["okr_progress_effect"], "no OKR percentage lift")
        self.assertIn("not verified terminal result", payload["non_claims"])
        self.assertIn("not true phone/browser proof", payload["non_claims"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["terminal_result_verified"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["material_upload_allowed"])
        self.assertFalse(payload["review_action_allowed"])
        self.assertFalse(payload["handoff_action_allowed"])
        self.assertFalse(payload["owner_response_submission_allowed"])
        self.assertFalse(payload["reviewer_ack_submission_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["diagnostics_mutation_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertEqual(diagnostics_summary["evidence_ref"], payload["evidence_ref"])
        self.assertIn(
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary",
            encoded,
        )
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("hardware_material_pending", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_states_are_not_proven(self):
        base_handoff = (
            relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_payload()
        )
        cases = [
            (
                {"review_handoff_status": "reviewer_ack_review_handoff_missing_material_not_proven"},
                "reviewer_ack_followup_blocked_missing_material_not_proven",
            ),
            (
                {"due_status": "reviewer_ack_followup_overdue_not_proven"},
                "reviewer_ack_followup_overdue_not_proven",
            ),
            (
                {"due_status": "reviewer_ack_followup_escalated_not_proven"},
                "reviewer_ack_followup_escalated_not_proven",
            ),
            (
                {"review_handoff_status": "reviewer_ack_review_handoff_rejected_unsafe_not_proven"},
                "reviewer_ack_followup_rejected_unsafe_not_proven",
            ),
            (
                {"review_handoff_status": ""},
                "blocked_missing_source_reviewer_ack_review_handoff_not_proven",
            ),
            (
                {"expected_evidence_ref": "different-safe-ref"},
                "reviewer_ack_followup_evidence_ref_mismatch_not_proven",
            ),
        ]
        for extra_fields, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                source_review_handoff = dict(base_handoff, **extra_fields)
                payload = (
                    relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_payload(
                        source_review_handoff=source_review_handoff
                    )
                )
                encoded = json.dumps(payload, ensure_ascii=False)

                self.assertEqual(payload["followup_status"], expected_status)
                self.assertIn(expected_status, payload["supported_followup_statuses"])
                self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
                self.assertIn("hardware_material_pending", payload["blocker_status"])
                self.assertFalse(payload["delivery_success"])
                self.assertFalse(payload["primary_actions_enabled"])
                self.assertFalse(payload["safe_to_control"])
                self.assertFalse(payload["terminal_result_verified"])
                self.assertFalse(payload["review_action_allowed"])
                self.assertFalse(payload["github_action_allowed"])
                self.assertFalse(payload["robot_command_side_effects_allowed"])
                self.assertFalse(payload["verified_terminal_result"])
                self.assertNotIn("delivery_success\": true", encoded)
                self.assertNotIn("primary_actions_enabled\": true", encoded)
                self.assertNotIn("safe_to_control\": true", encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_is_safe(self):
        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary"
        ]
        diagnostics_summary = diagnostics_payload[
            "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["schema"],
            "trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary.v1",
        )
        self.assertEqual(
            payload["capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge",
        )
        self.assertEqual(
            payload["proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate",
        )
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(
            payload["source_capability"],
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status",
        )
        self.assertEqual(
            payload["source_proof_boundary"],
            "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate",
        )
        self.assertEqual(payload["source_followup_status"], "reviewer_ack_followup_pending_not_proven")
        self.assertEqual(payload["bridge_status"], "accepted_for_owner_response_intake_bridge_not_proven")
        self.assertEqual(payload["owner_response_intake_readiness"], "ready_for_safe_owner_response_intake_not_proven")
        self.assertEqual(payload["safe_command_id"], "pending_same_safe_command_id")
        self.assertEqual(payload["evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertEqual(payload["safe_evidence_ref"], "pending_same_safe_evidence_ref")
        self.assertIn("safe_reviewer_ack_followup_escalation_status_summary", payload["accepted_materials"])
        self.assertIn("owner_response_material_packet", payload["missing_materials"])
        self.assertIn("hardware_material_pending", payload["blocked_materials"])
        self.assertEqual(payload["owner_route"], "field_owner")
        self.assertEqual(payload["support_route"], "support_triage")
        self.assertEqual(payload["reviewer_route"], "pr5_reviewer")
        self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["phone_browser_proof"], "not true phone/browser proof")
        self.assertEqual(payload["okr_progress_effect"], "no OKR percentage lift")
        self.assertIn("not verified terminal result", payload["non_claims"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["terminal_result_verified"])
        self.assertFalse(payload["owner_response_submission_allowed"])
        self.assertFalse(payload["reviewer_ack_submission_allowed"])
        self.assertFalse(payload["diagnostics_mutation_allowed"])
        self.assertFalse(payload["github_action_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["verified_terminal_result"])
        self.assertEqual(diagnostics_summary["evidence_ref"], payload["evidence_ref"])
        self.assertIn(
            "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary",
            encoded,
        )
        self.assertIn("source=software_proof", encoded)
        self.assertIn("not verified terminal result", encoded)
        self.assertIn("not true phone/browser proof", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("hardware_material_pending", encoded)
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_command_payload",
            "owner_response_submission_payload",
            "raw_reviewer_material",
            "signed_url",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "traceback",
            "complete artifact",
            "checksum",
            "verified terminal result success",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_states_are_not_proven(self):
        base_followup = (
            relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_payload()
        )
        cases = [
            (
                {"followup_status": ""},
                "blocked_missing_source_reviewer_ack_followup_escalation_status_not_proven",
            ),
            (
                {"expected_evidence_ref": "different-safe-ref"},
                "owner_response_intake_bridge_evidence_ref_mismatch_not_proven",
            ),
            (
                {"followup_status": "reviewer_ack_followup_blocked_missing_material_not_proven"},
                "owner_response_intake_bridge_missing_owner_material_not_proven",
            ),
            (
                {"followup_status": "reviewer_ack_followup_rejected_unsafe_not_proven"},
                "owner_response_intake_bridge_rejected_unsafe_not_proven",
            ),
            (
                {"raw_command_payload": {"T": 1}},
                "owner_response_intake_bridge_rejected_unsafe_not_proven",
            ),
        ]
        for extra_fields, expected_status in cases:
            with self.subTest(expected_status=expected_status):
                source_followup = dict(base_followup, **extra_fields)
                payload = (
                    relay_module.build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_payload(
                        source_followup_summary=source_followup
                    )
                )
                encoded = json.dumps(payload, ensure_ascii=False)

                self.assertEqual(payload["bridge_status"], expected_status)
                self.assertIn(expected_status, payload["supported_bridge_statuses"])
                self.assertEqual(payload["pr_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
                self.assertIn("hardware_material_pending", payload["blocker_status"])
                self.assertFalse(payload["delivery_success"])
                self.assertFalse(payload["primary_actions_enabled"])
                self.assertFalse(payload["safe_to_control"])
                self.assertFalse(payload["terminal_result_verified"])
                self.assertFalse(payload["owner_response_submission_allowed"])
                self.assertFalse(payload["reviewer_ack_submission_allowed"])
                self.assertFalse(payload["diagnostics_mutation_allowed"])
                self.assertFalse(payload["github_action_allowed"])
                self.assertFalse(payload["robot_command_side_effects_allowed"])
                self.assertFalse(payload["verified_terminal_result"])
                self.assertNotIn("raw_command_payload", encoded)
                self.assertNotIn("delivery_success\": true", encoded)
                self.assertNotIn("primary_actions_enabled\": true", encoded)
                self.assertNotIn("safe_to_control\": true", encoded)

    def test_pr5_mandatory_sensor_material_owner_response_review_handoff_alias_is_phone_safe(self):
        safe_summary = {
            "schema": "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1",
            "source_schema": "trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff.v1",
            "source_schema_version": 1,
            "evidence_boundary": (
                "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate"
            ),
            "source_evidence_boundary": (
                "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate"
            ),
            "capability": "pr5_mandatory_sensor_material_owner_response_review_handoff",
            "source": "software_proof",
            "safe_evidence_ref": "pr5-mandatory-sensor-owner-response-handoff-001",
            "handoff_status": "handoff_ready_not_proven",
            "overall_status": "not_proven",
            "handoff_reasons": ["safe handoff only; PR #5 remains unresolved"],
            "missing_material_summaries": [
                "2d_lidar_sku_source_receipt_procurement_material",
                "tof_sku_source_receipt_procurement_material",
            ],
            "next_required_evidence": ["hil_entry_material"],
            "reviewer_next_step": "Reviewer keeps PRRT_kwDOSWB9286CJ3tX unresolved.",
            "support_next_step": "Phone status renders this as read-only metadata.",
            "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "pr5_thread_state": "unresolved",
            "pr5_material_state": "hardware_material_pending",
            "evidence_boundary_status": "not_proven",
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": (
                "PR #5 mandatory sensor material owner response review handoff is "
                "metadata-only; source=software_proof; hardware_material_pending; "
                "not_proven; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false."
            ),
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "review_thread_updates_allowed": False,
            "source_payload_exposed": False,
            "command_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
            "field_pass": False,
            "sensor_installed": False,
            "pr_resolved": False,
        }
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "waiting_for_trash",
                "updated_at": time.time(),
                "diagnostics": {
                    "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary": safe_summary
                },
            },
        )
        self.assertEqual(status, 200)

        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(payload["capability"], "pr5_mandatory_sensor_material_owner_response_review_handoff")
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate",
        )
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["handoff_status"], "handoff_ready_not_proven")
        self.assertEqual(payload["safe_evidence_ref"], safe_summary["safe_evidence_ref"])
        self.assertEqual(payload["pr5_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["pr5_thread_state"], "unresolved")
        self.assertEqual(payload["pr5_material_state"], "hardware_material_pending")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["review_thread_updates_allowed"])
        self.assertFalse(payload["source_payload_exposed"])
        self.assertFalse(payload["command_allowed"])
        self.assertFalse(payload["nav2_triggered"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["field_pass"])
        self.assertFalse(payload["sensor_installed"])
        self.assertFalse(payload["pr_resolved"])
        self.assertEqual(
            diagnostics_payload[
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ]["safe_evidence_ref"],
            payload["safe_evidence_ref"],
        )
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

        unsafe = dict(
            safe_summary,
            safe_copy="Reviewer resolved; sensor installed; HIL pass; Start Delivery control enabled.",
            delivery_success=True,
            primary_actions_enabled=True,
            safe_to_control=True,
            raw_artifact={"topic": "/cmd_vel", "Authorization": "Bearer unsafe"},
        )
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "waiting_for_trash",
                "updated_at": time.time(),
                "diagnostics": {
                    "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary": unsafe
                },
            },
        )
        self.assertEqual(status, 200)
        status, blocked_payload = self.client.request("GET", "/api/status", token="")
        blocked = blocked_payload[
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        ]
        blocked_encoded = json.dumps(blocked_payload, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(blocked["handoff_status"], "blocked_unsafe_review_handoff_summary")
        self.assertFalse(blocked["delivery_success"])
        self.assertFalse(blocked["primary_actions_enabled"])
        self.assertFalse(blocked["safe_to_control"])
        self.assertNotIn("/cmd_vel", blocked_encoded)
        self.assertNotIn("Authorization", blocked_encoded)

    def test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_alias_is_phone_safe(self):
        safe_summary = {
            "schema": "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.v1",
            "source_schema": "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.v1",
            "source_schema_version": 1,
            "evidence_boundary": (
                "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate"
            ),
            "source_evidence_boundary": (
                "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate"
            ),
            "capability": "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake",
            "source": "software_proof",
            "status": "acknowledged_not_proven",
            "ack_intake_status": "acknowledged_not_proven",
            "overall_status": "not_proven",
            "reviewer_ack_status": {
                "status": "acknowledged_not_proven",
                "reason": "reviewer ACK metadata was recorded without resolving PR #5",
                "evidence_source": "software_proof",
            },
            "next_required_evidence": [
                "2d_lidar_sku_source_receipt_procurement_material",
                "tof_sku_source_receipt_procurement_material",
                "hil_entry_material",
            ],
            "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "pr5_thread_state": "unresolved",
            "pr5_material_state": "hardware_material_pending",
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
                "ack_post_allowed": False,
                "cursor_updates_allowed": False,
                "review_thread_updates_allowed": False,
                "robot_command_side_effects_allowed": False,
                "source_payload_exposed": False,
            },
            "safe_copy": (
                "PR #5 mandatory sensor material owner response reviewer ACK "
                "intake is metadata-only; source=software_proof; "
                "hardware_material_pending; not_proven; safe_to_control=false; "
                "delivery_success=false; primary_actions_enabled=false."
            ),
            "hardware_material_pending": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "review_thread_updates_allowed": False,
            "robot_command_side_effects_allowed": False,
            "source_payload_exposed": False,
        }
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "waiting_for_trash",
                "updated_at": time.time(),
                "diagnostics": {
                    "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary": safe_summary
                },
            },
        )
        self.assertEqual(status, 200)

        status, status_payload = self.client.request("GET", "/api/status", token="")
        diag_status, diagnostics_payload = self.client.request("GET", "/api/diagnostics", token="")
        payload = status_payload[
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        ]
        encoded = json.dumps({"status": status_payload, "diagnostics": diagnostics_payload}, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertEqual(diag_status, 200)
        self.assertEqual(
            payload["capability"],
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake",
        )
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate",
        )
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["ack_intake_status"], "acknowledged_not_proven")
        self.assertEqual(payload["pr5_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(payload["pr5_thread_state"], "unresolved")
        self.assertEqual(payload["pr5_material_state"], "hardware_material_pending")
        self.assertIn("hil_entry_material", payload["next_required_evidence"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ack_post_allowed"])
        self.assertFalse(payload["cursor_updates_allowed"])
        self.assertFalse(payload["review_thread_updates_allowed"])
        self.assertFalse(payload["robot_command_side_effects_allowed"])
        self.assertFalse(payload["source_payload_exposed"])
        self.assertEqual(
            diagnostics_payload[
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ]["ack_intake_status"],
            payload["ack_intake_status"],
        )
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "raw_path",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, encoded)

        unsafe = dict(
            safe_summary,
            safe_copy="Reviewer resolved; sensor installed; HIL pass; Start Delivery control enabled.",
            delivery_success=True,
            primary_actions_enabled=True,
            safe_to_control=True,
            raw_artifact={"topic": "/cmd_vel", "Authorization": "Bearer unsafe"},
        )
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "waiting_for_trash",
                "updated_at": time.time(),
                "diagnostics": {
                    "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary": unsafe
                },
            },
        )
        self.assertEqual(status, 200)
        status, blocked_payload = self.client.request("GET", "/api/status", token="")
        blocked = blocked_payload[
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        ]
        blocked_encoded = json.dumps(blocked_payload, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(
            blocked["ack_intake_status"],
            "blocked_unsafe_reviewer_ack_intake_summary",
        )
        self.assertFalse(blocked["delivery_success"])
        self.assertFalse(blocked["primary_actions_enabled"])
        self.assertFalse(blocked["safe_to_control"])
        self.assertNotIn("/cmd_vel", blocked_encoded)
        self.assertNotIn("Authorization", blocked_encoded)

    def test_mobile_web_phone_safe_api_uses_default_robot_id_and_fails_closed(self):
        with mock.patch.dict(os.environ, {"TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID": "robot-web-42"}):
            status, payload = self.client.request("GET", "/api/status", token="")
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["robot_id"], "robot-web-42")
        self.assertEqual(payload["overall_status"], "blocked")
        self.assertFalse(payload["production_ready"])
        self.assertFalse(payload["can_collect"])
        self.assertFalse(payload["can_confirm_dropoff"])
        self.assertFalse(payload["can_cancel"])
        self.assertFalse(payload["phone_readiness"]["can_continue"])
        self.assertFalse(payload["phone_readiness"]["action_permissions"]["can_collect"])
        self.assertFalse(payload["phone_readiness"]["command_safety"]["actions"]["start"]["enabled"])
        self.assertFalse(payload["phone_readiness"]["command_safety"]["actions"]["confirm_dropoff"]["enabled"])
        self.assertFalse(payload["phone_readiness"]["command_safety"]["actions"]["cancel"]["enabled"])
        self.assertIsNone(payload["latest_status"])
        for forbidden in (
            "phone-token",
            "Authorization",
            "Bearer",
            "postgres://",
            "queue URL",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_mobile_web_phone_safe_api_copies_latest_status_without_opening_actions(self):
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "Authorization Bearer secret should redact",
                "updated_at": time.time(),
                "diagnostics": {
                    "network": "relay_proof",
                    "serial_port": "/dev/ttyUSB0",
                    "ros_topic": "/cmd_vel",
                    "safe_hint": "waiting_for_ack",
                },
            },
        )
        self.assertEqual(status, 200)

        status, payload = self.client.request("GET", "/api/status", token="")
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "delivering")
        self.assertEqual(payload["latest_status"]["state"], "delivering")
        self.assertEqual(payload["latest_status"]["message"], "[redacted]")
        self.assertEqual(payload["latest_status"]["diagnostics"]["network"], "relay_proof")
        self.assertEqual(payload["latest_status"]["diagnostics"]["safe_hint"], "waiting_for_ack")
        self.assertEqual(payload["source"], "software_proof")
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["can_collect"])
        self.assertFalse(payload["phone_readiness"]["can_continue"])
        self.assertFalse(payload["phone_readiness"]["command_safety"]["actions"]["start"]["enabled"])
        for forbidden in (
            "Authorization",
            "Bearer",
            "secret",
            "/dev/ttyUSB0",
            "/cmd_vel",
            "serial_port",
            "ros_topic",
            "phone-token",
            str(REPO_ROOT),
        ):
            self.assertNotIn(forbidden, encoded)

    def test_mobile_web_status_preserves_safe_remote_degradation_state(self):
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "status_present",
                "updated_at": time.time(),
                "remote_readiness": {
                    "remote_ready": False,
                    "source": "software_proof",
                    "degradation_state": "command_pending",
                    "retry_hint": "wait_for_ack",
                    "safe_phone_copy": "命令仍在等待 ACK；主操作保持禁用。",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_to_control": False,
                    "raw_cloud_payload": {"Authorization": "Bearer hidden"},
                },
            },
        )
        self.assertEqual(status, 200)

        status, payload = self.client.request("GET", "/api/status", token="")
        encoded = json.dumps(payload, ensure_ascii=False)
        gate = payload["phone_readiness"]["cloud_hosted_mobile_web_gate"]
        remote_readiness = payload["remote_readiness"]

        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "command_pending")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(remote_readiness["degradation_state"], "command_pending")
        self.assertFalse(remote_readiness["remote_ready"])
        self.assertFalse(remote_readiness["delivery_success"])
        self.assertFalse(remote_readiness["primary_actions_enabled"])
        self.assertFalse(remote_readiness["safe_to_control"])
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate",
        )
        self.assertEqual(gate["capability"], "cloud_hosted_mobile_web_degradation_passthrough")
        self.assertFalse(gate["delivery_success"])
        self.assertFalse(gate["primary_actions_enabled"])
        self.assertFalse(gate["safe_to_control"])
        self.assertNotEqual(payload["state"], "status_present")
        for forbidden in (
            "Authorization",
            "Bearer",
            "raw_cloud_payload",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
            "/cmd_vel",
            "ttyUSB",
            str(REPO_ROOT),
        ):
            self.assertNotIn(forbidden, encoded)

    def test_mobile_web_diagnostics_contains_safe_summary_latest_status_and_no_leaks(self):
        status, _ = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "waiting_for_dropoff",
                "message": "waiting safely",
                "updated_at": time.time(),
                "diagnostics": {"network": "relay_proof", "database_url": "postgres://hidden"},
            },
        )
        self.assertEqual(status, 200)

        status, payload = self.client.request("GET", "/api/diagnostics", token="")
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(status, 200)
        self.assertEqual(payload["overall_status"], "blocked")
        self.assertEqual(payload["phone_safe_summary"]["state"], "waiting_for_dropoff")
        self.assertFalse(payload["phone_safe_summary"]["can_collect"])
        self.assertEqual(payload["latest_status"]["state"], "waiting_for_dropoff")
        self.assertEqual(payload["cloud_hosted_mobile_web_gate"]["overall_status"], "blocked")
        self.assertEqual(
            payload["evidence_boundary"],
            "software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate",
        )
        self.assertIn("real_4g_sim", payload["not_proven"])
        for forbidden in (
            "Authorization",
            "Bearer",
            "token",
            "postgres://",
            "database_url",
            "queue URL",
            str(REPO_ROOT),
            "/cmd_vel",
            "ttyUSB",
            "serial",
            "baudrate",
            "WAVE ROVER",
            "traceback",
            "complete artifact",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_mobile_web_missing_static_and_traversal_are_phone_safe(self):
        for path in ("/missing.css", "/../OKR.md", "/%2e%2e/OKR.md"):
            status, headers, body = self.client.raw_request("GET", path, token="")
            payload = json.loads(body.decode("utf-8") or "{}")
            encoded = json.dumps(payload, ensure_ascii=False)
            self.assertEqual(status, 404, path)
            self.assertIn("application/json", headers.get("Content-Type", ""))
            self.assertEqual(payload["error"]["code"], "not_found")
            self.assertNotIn(str(REPO_ROOT), encoded)
            self.assertNotIn("OKR.md", encoded)

    def test_readiness_fails_without_credential_gate(self):
        server = build_server("127.0.0.1", 0, self.state_path, "")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}", token="")
        try:
            status, payload = client.request("GET", "/readyz", token="")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        self.assertEqual(status, 503)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["checks"]["credential_gate"])
        self.assertEqual(payload["error"]["code"], "not_ready")

    def test_expired_command_is_not_returned_as_next(self):
        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/commands",
            self.command("cmd-expired", expires_at=time.time() - 1.0),
        )
        self.assertEqual(status, 201)

        status, payload = self.client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["command"])

    def test_bearer_auth_blocks_missing_and_wrong_token_without_leaks(self):
        for token in ("", "wrong-token"):
            status, payload = self.client.request("GET", "/robots/trashbot-001/status", token=token)
            encoded = json.dumps(payload, ensure_ascii=False)
            self.assertEqual(status, 401)
            self.assertEqual(payload["error"]["code"], "auth_failed")
            self.assertIn("手机登录已失效", payload["error"]["safe_phone_copy"])
            self.assertNotIn("phone-token", encoded)
            self.assertNotIn("Authorization", encoded)
            self.assertNotIn("wrong-token", encoded)

    def test_bad_requests_and_malformed_json_are_phone_safe(self):
        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/commands",
            self.command("cmd-bad", payload={}),
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "bad_request")
        self.assertIn("payload.target", payload["error"]["message"])

        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/commands",
            self.command("cmd-raw", type="cmd_vel", payload={"linear": 1.0}),
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "bad_request")
        self.assertNotIn("/cmd_vel", json.dumps(payload, ensure_ascii=False))

        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            raw_body=b"{bad-json",
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "malformed_json")
        self.assertNotIn("Traceback", json.dumps(payload, ensure_ascii=False))

    def test_status_missing_stale_and_missing_ack_have_distinct_errors(self):
        status, payload = self.client.request("GET", "/robots/new-robot/status")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "status_missing")

        status, payload = self.client.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "old status",
                "updated_at": time.time() - 120.0,
            },
        )
        self.assertEqual(status, 200)
        status, payload = self.client.request("GET", "/robots/trashbot-001/status")
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"]["code"], "status_stale")
        self.assertEqual(payload["status"]["state"], "delivering")

        status, payload = self.client.request("GET", "/robots/trashbot-001/commands/missing/ack")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "not_found")


class RemoteCloudRelayStoreTest(unittest.TestCase):
    def test_file_backed_o6_store_reloads_tasks_and_tunnel_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "o6_archive_state.json"
            fixture = {
                "schema": relay_module.O6_CLOUD_ARCHIVE_STORE_SCHEMA,
                "tasks": {
                    "task-o6-store": {
                        "robot_id": "trashbot-001",
                        "task_id": "task-o6-store",
                        "started_at_ms": 1000,
                        "finished_at_ms": 2000,
                        "trajectory_frames": [],
                        "events": [],
                        "evidence_refs": ["evidence/store-001.json"],
                        "labels": [],
                        "created_at_ms": 1500,
                        "updated_at_ms": 2500,
                        "selected": True,
                    }
                },
                "tunnel_status": {
                    "trashbot-001": {
                        "robot_id": "trashbot-001",
                        "tunnel_provider": "frp",
                        "endpoint": "https://tunnel.example.com/stream",
                        "observed_at_ms": 3000,
                        "ttl_seconds": 300,
                        "metadata": {
                            "ip_family": "ipv4",
                            "network_type": "cellular",
                        },
                        "created_at_ms": 3000,
                        "updated_at_ms": 3000,
                        "last_seen_at_ms": 3000,
                    }
                },
            }
            state_path.write_text(json.dumps(fixture), encoding="utf-8")

            with mock.patch.object(relay_module, "_now", return_value=4.0):
                restored = relay_module.FileBackedO6CloudArchiveStore(state_path)
                status, task_payload = restored.get_task("task-o6-store")
                self.assertEqual(status, 200)
                self.assertEqual(task_payload["task_list"]["total_tasks"], 1)

                status, robot_payload = restored.get_tunnel_status("trashbot-001")
                self.assertEqual(status, 200)
                self.assertEqual(robot_payload["robot_id"], "trashbot-001")
                self.assertEqual(robot_payload["tunnel_provider"], "frp")

                status, robots_payload = restored.list_tunnel_statuses()
                self.assertEqual(status, 200)
                self.assertEqual(robots_payload["robots"][0]["robot_id"], "trashbot-001")
                self.assertEqual(robots_payload["robots"][0]["status"], "online")

    def test_file_backed_store_persists_and_redacts_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.json"
            store = FileBackedRelayStore(state_path)
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-persist-1",
                    "type": "collect",
                    "expires_at": time.time() + 300.0,
                    "payload": {
                        "target": "trash_station",
                        "token": "must-not-persist",
                        "note": "never expose /cmd_vel or Bearer phone-token",
                        "serial_port": "/dev/ttyUSB0",
                    },
                },
            )
            store.post_status(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "delivering",
                    "message": "cloud URL https://user:secret@example.invalid",
                    "updated_at": time.time(),
                    "diagnostics": {"baudrate": 115200, "network": "relay_proof"},
                },
            )
            store.post_ack(
                "trashbot-001",
                "cmd-persist-1",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "failed",
                    "message": "Authorization header must not persist",
                    "updated_at": time.time(),
                    "result": {"authorization": "Bearer phone-token", "reason": "rejected"},
                },
            )

            persisted = state_path.read_text(encoding="utf-8")
            self.assertIn("trashbot.remote_cloud_relay_store.v1", persisted)
            self.assertIn("cmd-persist-1", persisted)
            for forbidden in (
                "must-not-persist",
                "phone-token",
                "Authorization",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "https://user:secret@",
            ):
                self.assertNotIn(forbidden, persisted)

            restored = FileBackedRelayStore(state_path)
            status, status_payload = restored.get_status("trashbot-001")
            self.assertEqual(status, 200)
            self.assertEqual(status_payload["status"]["state"], "delivering")
            status, ack_payload = restored.get_ack("trashbot-001", "cmd-persist-1")
            self.assertEqual(status, 200)
            self.assertEqual(ack_payload["ack"]["state"], "failed")
            self.assertIsNone(restored.next_command("trashbot-001", "")["command"])

    def test_sqlite_store_persists_command_status_and_ack_across_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.sqlite"
            store = SQLiteRelayStore(state_path)
            created_at = time.time()
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-sqlite-1",
                    "type": "collect",
                    "expires_at": created_at + 300.0,
                    "payload": {"target": "trash_station", "trash_type": 0},
                },
            )

            reopened = SQLiteRelayStore(state_path)
            next_payload = reopened.next_command("trashbot-001", "")
            self.assertEqual(next_payload["command"]["id"], "cmd-sqlite-1")
            self.assertEqual(next_payload["command"]["protocol_version"], PROTOCOL_VERSION)

            reopened.post_status(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "delivering",
                    "message": "sqlite relay status",
                    "updated_at": time.time(),
                    "diagnostics": {"network": "sqlite_proof"},
                },
            )
            reopened.post_ack(
                "trashbot-001",
                "cmd-sqlite-1",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "acked",
                    "message": "sqlite relay ack",
                    "updated_at": time.time(),
                    "result": {"bridge": "submitted"},
                },
            )

            restarted = SQLiteRelayStore(state_path)
            status, status_payload = restarted.get_status("trashbot-001")
            self.assertEqual(status, 200)
            self.assertEqual(status_payload["status"]["state"], "delivering")
            status, ack_payload = restarted.get_ack("trashbot-001", "cmd-sqlite-1")
            self.assertEqual(status, 200)
            self.assertEqual(ack_payload["ack"]["state"], "acked")
            self.assertIsNone(restarted.next_command("trashbot-001", "cmd-sqlite-1")["command"])

    def test_sqlite_http_contract_survives_relay_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.sqlite"
            server = build_server("127.0.0.1", 0, state_path, "phone-token", "sqlite")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            client = RelayHttpClient(f"http://127.0.0.1:{server.server_address[1]}")
            try:
                status, payload = client.request(
                    "POST",
                    "/robots/trashbot-001/commands",
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "id": "cmd-http-sqlite-1",
                        "type": "collect",
                        "expires_at": time.time() + 300.0,
                        "payload": {"target": "trash_station", "trash_type": 0},
                    },
                )
                self.assertEqual(status, 201)
                self.assertEqual(payload["command"]["id"], "cmd-http-sqlite-1")
                client.request(
                    "POST",
                    "/robots/trashbot-001/status",
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "state": "delivering",
                        "updated_at": time.time(),
                    },
                )
                client.request(
                    "POST",
                    "/robots/trashbot-001/commands/cmd-http-sqlite-1/ack",
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "state": "acked",
                        "updated_at": time.time(),
                    },
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

            restarted = build_server("127.0.0.1", 0, state_path, "phone-token", "sqlite")
            restarted_thread = threading.Thread(target=restarted.serve_forever, daemon=True)
            restarted_thread.start()
            restarted_client = RelayHttpClient(f"http://127.0.0.1:{restarted.server_address[1]}")
            try:
                status, payload = restarted_client.request("GET", "/robots/trashbot-001/status")
                self.assertEqual(status, 200)
                self.assertEqual(payload["status"]["state"], "delivering")
                status, payload = restarted_client.request(
                    "GET",
                    "/robots/trashbot-001/commands/cmd-http-sqlite-1/ack",
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload["ack"]["state"], "acked")
                status, payload = restarted_client.request(
                    "GET",
                    "/robots/trashbot-001/commands/next?last_ack_id=cmd-http-sqlite-1",
                )
                self.assertEqual(status, 200)
                self.assertIsNone(payload["command"])
            finally:
                restarted.shutdown()
                restarted.server_close()
                restarted_thread.join(timeout=1.0)

    def test_sqlite_backup_restore_drill_preserves_http_shapes_and_cursor_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.sqlite"
            artifact_path = pathlib.Path(tmp) / "relay_backup.json"
            restore_path = pathlib.Path(tmp) / "relay_restored.sqlite"
            store = SQLiteRelayStore(state_path)
            now = time.time()

            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-restore-acked",
                    "type": "collect",
                    "expires_at": now + 300.0,
                    "payload": {"target": "trash_station", "trash_type": 0},
                },
            )
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-restore-pending",
                    "type": "confirm_dropoff",
                    "expires_at": now + 300.0,
                    "payload": {},
                },
            )
            store.post_status(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "delivering",
                    "message": "backup restore source status",
                    "updated_at": now,
                    "diagnostics": {"network": "sqlite_backup_restore_proof"},
                },
            )
            store.post_ack(
                "trashbot-001",
                "cmd-restore-acked",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "acked",
                    "message": "backup restore source ack",
                    "updated_at": now,
                    "result": {"bridge": "submitted"},
                },
            )

            drill = backup_restore_drill_payload(state_path, artifact_path, restore_path)
            encoded = json.dumps(drill, ensure_ascii=False)
            self.assertTrue(drill["ok"])
            self.assertEqual(drill["evidence_boundary"], BACKUP_RESTORE_EVIDENCE_BOUNDARY)
            self.assertTrue(drill["checks"]["artifact_checksum"])
            self.assertTrue(drill["checks"]["restored_command_http_shape"])
            self.assertTrue(drill["checks"]["restored_status_http_shape"])
            self.assertTrue(drill["checks"]["restored_ack_http_shape"])
            self.assertTrue(drill["checks"]["cursor_ack_conservative"])
            for forbidden in (
                str(state_path),
                str(restore_path),
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
            ):
                self.assertNotIn(forbidden, encoded)

            restored = build_server("127.0.0.1", 0, restore_path, "phone-token", "sqlite")
            restored_thread = threading.Thread(target=restored.serve_forever, daemon=True)
            restored_thread.start()
            client = RelayHttpClient(f"http://127.0.0.1:{restored.server_address[1]}")
            try:
                status, payload = client.request("GET", "/robots/trashbot-001/status")
                self.assertEqual(status, 200)
                self.assertEqual(payload["status"]["state"], "delivering")
                status, payload = client.request("GET", "/robots/trashbot-001/commands/cmd-restore-acked/ack")
                self.assertEqual(status, 200)
                self.assertEqual(payload["ack"]["state"], "acked")
                status, payload = client.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
                self.assertEqual(status, 200)
                self.assertEqual(payload["command"]["id"], "cmd-restore-pending")
                status, payload = client.request(
                    "GET",
                    "/robots/trashbot-001/commands/next?last_ack_id=cmd-restore-acked",
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload["command"]["id"], "cmd-restore-pending")
            finally:
                restored.shutdown()
                restored.server_close()
                restored_thread.join(timeout=1.0)

    def test_sqlite_backup_restore_fails_closed_on_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.sqlite"
            artifact_path = pathlib.Path(tmp) / "relay_backup.json"
            restore_path = pathlib.Path(tmp) / "relay_restored.sqlite"
            store = SQLiteRelayStore(state_path)
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-checksum",
                    "type": "collect",
                    "expires_at": time.time() + 300.0,
                    "payload": {"target": "trash_station"},
                },
            )
            create_sqlite_backup_artifact(state_path, artifact_path)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            artifact["metadata"]["command_count"] = 99
            artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")

            summary = backup_artifact_summary(artifact_path)
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["reason_code"], "artifact_invalid")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                restore_sqlite_backup_artifact(artifact_path, restore_path)

    def test_sqlite_unwritable_path_is_phone_safe(self):
        store = SQLiteRelayStore(_unwritable_sqlite_path())
        self.assertFalse(store.state_store_writable())
        with self.assertRaisesRegex(ValueError, "sqlite state store is not ready"):
            store.next_command("trashbot-001", "")

    def test_network_recovery_drill_artifact_preserves_cursor_and_phone_safe_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "network_recovery.sqlite"
            artifact_path = pathlib.Path(tmp) / "network_recovery.json"

            result = create_network_recovery_artifact(
                artifact_path,
                state_path,
                state_backend="sqlite",
                robot_id="trashbot-001",
            )
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = network_recovery_artifact_summary(artifact_path)
            encoded = json.dumps({"result": result, "artifact": artifact, "summary": summary}, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], NETWORK_RECOVERY_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["evidence_boundary"], NETWORK_RECOVERY_EVIDENCE_BOUNDARY)
            self.assertEqual(artifact["overall_status"], "passed")
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(summary["step_count"], 4)
            self.assertFalse(artifact["cursor_invariant"]["ack_failure_advances_cursor"])
            self.assertTrue(artifact["cursor_invariant"]["terminal_ack_required_before_cursor_advance"])
            self.assertFalse(artifact["cursor_invariant"]["ack_is_delivery_success"])
            step_names = {step["name"] for step in artifact["steps"]}
            self.assertIn("relay_or_cloud_unreachable", step_names)
            self.assertIn("ack_post_failure_is_not_delivery_success", step_names)
            self.assertIn("recovery_command_status_ack_envelope", step_names)
            self.assertIn("status_stale_phone_safe_blocked", step_names)
            self.assertIn("delivery_success", artifact["not_proven"])
            self.assertIn("real_cloud", artifact["not_proven"])
            self.assertIn("real_4g_sim", artifact["not_proven"])
            for forbidden in (
                str(state_path),
                str(artifact_path),
                "Authorization",
                "Bearer",
                "token",
                "OSS secret",
                "AK/SK",
                "root password",
                "/tmp/",
                "/dev/",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ros topic",
                "/cmd_vel",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_network_recovery_summary_fails_closed_for_failed_stale_and_invalid_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            failed_path = root / "failed.json"
            stale_path = root / "stale.json"
            invalid_path = root / "invalid.json"

            failed_artifact = network_recovery_drill_payload(root / "failed.sqlite", now=1778562000.0)
            failed_artifact["overall_status"] = "failed"
            failed_body = {key: value for key, value in failed_artifact.items() if key != "checksum"}
            failed_artifact["checksum"] = _sha256_checksum(failed_body)
            failed_path.write_text(json.dumps(failed_artifact, ensure_ascii=False), encoding="utf-8")
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")

            stale_artifact = network_recovery_drill_payload(root / "stale.sqlite", now=1778562000.0)
            stale_path.write_text(json.dumps(stale_artifact, ensure_ascii=False), encoding="utf-8")

            missing = build_phone_network_recovery_summary(root / "missing.json", now=1778562000.0)
            invalid = build_phone_network_recovery_summary(invalid_path, now=1778562000.0)
            failed = build_phone_network_recovery_summary(failed_path, now=1778562000.0)
            stale = build_phone_network_recovery_summary(stale_path, now=1778562000.0 + 48 * 60 * 60)
            invalid_preflight = network_recovery_artifact_summary(invalid_path)

            self.assertEqual(missing["state"], "missing")
            self.assertEqual(invalid["state"], "invalid")
            self.assertEqual(failed["state"], "failed")
            self.assertEqual(stale["state"], "stale")
            self.assertFalse(invalid_preflight["ok"])
            self.assertEqual(invalid_preflight["reason_code"], "network_recovery_invalid")
            self.assertEqual(missing["evidence_boundary"], NETWORK_RECOVERY_PHONE_EVIDENCE_BOUNDARY)
            self.assertIn("delivery_success", missing["not_proven"])


class RemoteCloudRelayPreflightTest(unittest.TestCase):
    def test_cloud_deployment_readiness_artifact_generation_and_preflight_are_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "cloud_deployment_readiness.json"
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "http://127.0.0.1:8088",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "future_reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "missing",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "placeholder",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            result = create_cloud_deployment_readiness_artifact(artifact_path, env)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = cloud_deployment_readiness_artifact_summary(artifact_path)
            preflight_env = dict(env)
            preflight_env["TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT"] = str(artifact_path)
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"artifact": artifact, "summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], CLOUD_DEPLOYMENT_READINESS_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertIn("real_cloud", artifact["not_proven"])
            self.assertIn("real_4g_sim", artifact["not_proven"])
            self.assertEqual(summary["check_count"], 8)
            self.assertFalse(payload["production_ready"])
            self.assertEqual(payload["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_deployment_readiness"]["status"], "pass")
            self.assertFalse(checks["cloud_deployment_readiness"]["details"]["production_ready"])
            for required in (
                "public_base_url_tls_ingress",
                "healthcheck_endpoint",
                "bearer_credential_placeholder",
                "state_backend",
                "production_db_queue_gap",
                "oss_cdn_gap",
                "cellular_4g_sim_gap",
                "deployment_runbook_or_smoke",
            ):
                self.assertIn(required, encoded)
            for forbidden in (
                str(artifact_path),
                str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "replace-with-local-dev-token",
                "Authorization",
                "Bearer ",
                "postgres://",
                "queue URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "Traceback",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_deployment_readiness_blocks_hostile_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            hostile_path = root / "hostile_cloud_deployment_readiness.json"
            hostile = build_cloud_deployment_readiness_artifact_payload(
                {"TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token"},
                generated_at="2026-05-13T04:00:00Z",
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            summary = cloud_deployment_readiness_artifact_summary(hostile_path)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                    "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT": str(hostile_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_deployment_readiness"]["status"], "blocked")
            self.assertEqual(checks["cloud_deployment_readiness"]["code"], "cloud_deployment_readiness_artifact_invalid")
            for forbidden in (
                str(hostile_path),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_external_probe_bundle_artifact_and_preflight_are_phone_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state_path = root / "relay_state.json"
            artifact_path = root / "cloud_external_probe.json"
            server = build_server("127.0.0.1", 0, state_path, "phone-token")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                result = create_cloud_external_probe_bundle_artifact(artifact_path, base_url)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=1.0)

            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = cloud_external_probe_bundle_summary(artifact_path)
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "http://127.0.0.1:8088",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "future_reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "missing",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT": str(artifact_path),
            }
            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"result": result, "artifact": artifact, "summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], CLOUD_EXTERNAL_PROBE_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["evidence_boundary"], CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual({item["endpoint"] for item in artifact["endpoint_results"]}, {"/healthz", "/readyz", "/preflightz"})
            self.assertTrue(all(item["status"] == "pass" for item in artifact["endpoint_results"]))
            self.assertEqual(artifact["redaction_status"]["status"], "pass")
            self.assertIn("real_cloud", artifact["not_proven"])
            self.assertIn("real_https_tls", artifact["not_proven"])
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["evidence_boundary"], CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_external_probe_bundle"]["status"], "pass")
            self.assertFalse(checks["cloud_external_probe_bundle"]["details"]["production_ready"])
            for endpoint in ("/healthz", "/readyz", "/preflightz"):
                self.assertIn(endpoint, encoded)
            for forbidden in (
                base_url,
                str(artifact_path),
                str(root / "preflight_state.sqlite"),
                "phone-token",
                "replace-with-local-dev-token",
                "Authorization",
                "Bearer ",
                "postgres://",
                "queue URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "Traceback",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_external_probe_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            hostile_path = root / "hostile_cloud_external_probe.json"
            hostile = build_cloud_external_probe_bundle_payload(
                "http://127.0.0.1:1",
                generated_at="2026-05-13T06:00:00Z",
                timeout_sec=0.01,
            )
            for item in hostile["endpoint_results"]:
                item["status"] = "pass"
                item["http_status"] = 200 if item["endpoint"] != "/preflightz" else 503
                item["reachable"] = True
                item["json_ok"] = True
                item["expected_keys_present"] = True
            hostile["endpoint_contract_ready"] = True
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            summary = cloud_external_probe_bundle_summary(hostile_path)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                    "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT": str(hostile_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_external_probe_bundle"]["status"], "blocked")
            self.assertEqual(checks["cloud_external_probe_bundle"]["code"], "cloud_external_probe_artifact_invalid")
            for forbidden in (
                str(hostile_path),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_public_ingress_tls_gate_distinguishes_missing_and_config_present_without_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            missing_path = root / "cloud_public_ingress_tls_missing.json"
            present_path = root / "cloud_public_ingress_tls_present.json"
            missing_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "http://127.0.0.1:8088",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "future_reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "missing",
                "TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "missing_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            present_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "present_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_result = create_cloud_public_ingress_tls_artifact(missing_path, missing_env)
            present_result = create_cloud_public_ingress_tls_artifact(present_path, present_env)
            missing_artifact = json.loads(missing_path.read_text(encoding="utf-8"))
            present_artifact = json.loads(present_path.read_text(encoding="utf-8"))
            missing_payload_env = dict(missing_env)
            missing_payload_env["TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT"] = str(missing_path)
            present_payload_env = dict(present_env)
            present_payload_env["TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT"] = str(present_path)
            missing_payload = production_preflight_payload(missing_payload_env)
            present_payload = production_preflight_payload(present_payload_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            present_checks = {check["name"]: check for check in present_payload["checks"]}
            encoded = json.dumps(
                {
                    "missing_result": missing_result,
                    "present_result": present_result,
                    "missing_artifact": missing_artifact,
                    "present_artifact": present_artifact,
                    "missing_preflight": missing_payload,
                    "present_preflight": present_payload,
                },
                ensure_ascii=False,
            )

            self.assertTrue(missing_result["ok"])
            self.assertTrue(present_result["ok"])
            self.assertEqual(missing_artifact["schema"], CLOUD_PUBLIC_INGRESS_TLS_SCHEMA)
            self.assertEqual(present_artifact["evidence_boundary"], CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY)
            self.assertFalse(missing_artifact["production_ready"])
            self.assertFalse(present_artifact["production_ready"])
            self.assertEqual(missing_artifact["overall_status"], "blocked")
            self.assertEqual(present_artifact["overall_status"], "blocked")
            self.assertEqual(missing_artifact["state"], "missing_public_ingress_tls_config")
            self.assertEqual(present_artifact["state"], "public_ingress_tls_config_present_not_externally_proven")
            self.assertFalse(missing_artifact["config_package_present"])
            self.assertTrue(present_artifact["config_package_present"])
            self.assertFalse(present_artifact["external_probe_proven"])
            self.assertFalse(missing_payload["production_ready"])
            self.assertFalse(present_payload["production_ready"])
            self.assertEqual(missing_payload["overall_status"], "blocked")
            self.assertEqual(present_payload["overall_status"], "blocked")
            self.assertEqual(missing_payload["evidence_boundary"], CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY)
            self.assertEqual(present_payload["evidence_boundary"], CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY)
            self.assertEqual(
                missing_checks["cloud_public_ingress_tls"]["code"],
                "missing_public_ingress_tls_config",
            )
            self.assertEqual(
                present_checks["cloud_public_ingress_tls"]["code"],
                "public_ingress_tls_config_present_not_externally_proven",
            )
            self.assertFalse(present_checks["cloud_public_ingress_tls"]["details"]["external_probe_proven"])
            for marker in (
                "real_https_tls",
                "public_ingress_external_probe",
                "dns_resolution",
                "reverse_proxy_live_routing",
                "firewall_public_ingress",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(missing_path),
                str(present_path),
                str(root / "missing_state.sqlite"),
                str(root / "present_state.sqlite"),
                "relay.example.invalid",
                "replace-with-local-dev-token",
                "Authorization",
                "Bearer",
                "token",
                "private key",
                "certificate path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_public_ingress_tls_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            hostile_path = root / "hostile_cloud_public_ingress_tls.json"
            hostile = build_cloud_public_ingress_tls_artifact_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                    "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "reverse_proxy",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                    "TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG": "present",
                },
                generated_at="2026-05-13T08:00:00Z",
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token private key certificate path postgres://db "
                "queue URL raw state path /dev/ttyUSB0 baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            summary = cloud_public_ingress_tls_artifact_summary(hostile_path)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                    "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                    "TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG": "present",
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT": str(hostile_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_public_ingress_tls"]["status"], "blocked")
            self.assertEqual(checks["cloud_public_ingress_tls"]["code"], "cloud_public_ingress_tls_artifact_invalid")
            for forbidden in (
                str(hostile_path),
                "relay.example.invalid",
                "Authorization",
                "Bearer",
                "token",
                "private key",
                "certificate path",
                "postgres://",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_db_queue_config_gate_distinguishes_missing_and_config_present_without_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            missing_path = root / "cloud_db_queue_missing.json"
            present_path = root / "cloud_db_queue_present.json"
            missing_env = {
                "TRASHBOT_REMOTE_CLOUD_DB_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG": "missing",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "missing_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            present_env = {
                "TRASHBOT_REMOTE_CLOUD_DB_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG": "present",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "present_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_result = create_cloud_db_queue_config_artifact(missing_path, missing_env)
            present_result = create_cloud_db_queue_config_artifact(present_path, present_env)
            missing_artifact = json.loads(missing_path.read_text(encoding="utf-8"))
            present_artifact = json.loads(present_path.read_text(encoding="utf-8"))
            present_payload_env = dict(present_env)
            present_payload_env["TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT"] = str(present_path)
            present_payload = production_preflight_payload(present_payload_env)
            present_checks = {check["name"]: check for check in present_payload["checks"]}
            encoded = json.dumps(
                {
                    "missing_result": missing_result,
                    "present_result": present_result,
                    "missing_artifact": missing_artifact,
                    "present_artifact": present_artifact,
                    "present_preflight": present_payload,
                },
                ensure_ascii=False,
            )

            self.assertTrue(missing_result["ok"])
            self.assertTrue(present_result["ok"])
            self.assertEqual(missing_artifact["schema"], CLOUD_DB_QUEUE_CONFIG_SCHEMA)
            self.assertEqual(present_artifact["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
            self.assertEqual(missing_artifact["state"], "missing_cloud_db_queue_config")
            self.assertEqual(present_artifact["state"], "cloud_db_queue_config_present_not_externally_proven")
            self.assertFalse(missing_artifact["production_ready"])
            self.assertFalse(present_artifact["production_ready"])
            self.assertEqual(missing_artifact["overall_status"], "blocked")
            self.assertEqual(present_artifact["overall_status"], "blocked")
            self.assertTrue(present_artifact["config_package_present"])
            self.assertFalse(present_artifact["external_db_queue_probe_proven"])
            self.assertFalse(present_payload["production_ready"])
            self.assertEqual(present_payload["overall_status"], "blocked")
            self.assertEqual(present_payload["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
            self.assertEqual(
                present_checks["cloud_db_queue_config"]["code"],
                "cloud_db_queue_config_present_not_externally_proven",
            )
            self.assertFalse(present_checks["cloud_db_queue_config"]["details"]["external_db_queue_probe_proven"])
            for marker in (
                "production_db_or_queue",
                "production_queue_connection",
                "multi_instance_consistency",
                "production_backup_policy",
                "real_disaster_recovery",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(missing_path),
                str(present_path),
                str(root / "missing_state.sqlite"),
                str(root / "present_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "mysql://",
                "redis://",
                "amqp://",
                "queue URL",
                "database URL",
                "root password",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_db_queue_config_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            hostile_path = root / "hostile_cloud_db_queue_config.json"
            hostile = build_cloud_db_queue_config_artifact_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_DB_CONFIG": "present",
                    "TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG": "present",
                },
                generated_at="2026-05-13T10:00:00Z",
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL database URL "
                "raw state path /dev/ttyUSB0 baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            summary = cloud_db_queue_config_artifact_summary(hostile_path)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_DB_CONFIG": "present",
                    "TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG": "present",
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT": str(hostile_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_db_queue_config"]["status"], "blocked")
            self.assertEqual(checks["cloud_db_queue_config"]["code"], "cloud_db_queue_config_artifact_invalid")
            for forbidden in (
                str(hostile_path),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "database URL",
                "raw state path",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_reports_local_http_secret_oss_and_file_store_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "http://127.0.0.1:8088",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "future_reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "missing",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/<robot_id>/<date>/<task_id>/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "placeholder",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.json"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "file",
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_deployment_readiness"]["status"], "pass")
            self.assertEqual(checks["credential_provisioning"]["status"], "blocked")
            self.assertEqual(checks["tls_public_ingress"]["status"], "blocked")
            self.assertEqual(checks["oss_cdn"]["status"], "blocked")
            self.assertEqual(checks["state_store"]["status"], "warning")
            self.assertEqual(checks["backup_restore_drill"]["status"], "warning")
            self.assertEqual(checks["phone_safe_output"]["status"], "pass")
            self.assertIn("software_proof_docker_cloud_deployment_readiness_gate", encoded)
            for forbidden in (
                "replace-with-local-dev-token",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "ros topic",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_redacts_env_derived_hardware_and_ros_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated /dev/ttyACM0 serial_port=/dev/cu.usbserial /odom",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https /imu/data /battery /trashbot/collect_trash",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts /cmd_vel baudrate WAVE ROVER Authorization",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.json"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "postgres Bearer token root password OSS secret",
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            # env-derived detail 字段必须降级为白名单枚举，不能把硬件/ROS/凭证片段透传给手机。
            self.assertEqual(checks["tls_public_ingress"]["details"]["tls_mode"], "invalid_or_unsupported")
            self.assertEqual(checks["tls_public_ingress"]["details"]["public_ingress"], "invalid_or_unsupported")
            self.assertEqual(checks["oss_cdn"]["details"]["credential_mode"], "invalid_or_unsupported")
            self.assertEqual(checks["state_store"]["details"]["backend"], "file")
            for forbidden in (
                "/dev/ttyACM0",
                "/dev/cu.usbserial",
                "serial_port",
                "/odom",
                "/imu/data",
                "/battery",
                "/trashbot/collect_trash",
                "/cmd_vel",
                "baudrate",
                "WAVE ROVER",
                "Authorization",
                "Bearer",
                "token",
                "root password",
                "OSS secret",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_blocks_unwritable_state_store(self):
        env = {
            "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
            "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
            "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
            "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
            "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
            "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
            "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
            "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
            "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
            "TRASHBOT_REMOTE_CLOUD_STATE": _unwritable_json_state_path(),
            "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "file",
        }

        payload = production_preflight_payload(env)
        checks = {check["name"]: check for check in payload["checks"]}

        self.assertFalse(payload["production_ready"])
        self.assertEqual(checks["state_store"]["status"], "blocked")
        self.assertEqual(checks["state_store"]["code"], "state_store_not_writable")

    def test_preflight_recognizes_sqlite_backend_without_production_claims_or_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertEqual(payload["evidence_boundary"], CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["state_store"]["status"], "warning")
            self.assertEqual(checks["state_store"]["code"], "sqlite_state_store_proof_only")
            self.assertEqual(checks["backup_restore_drill"]["code"], "backup_restore_drill_not_run")
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("multi_instance_consistency", payload["not_proven"])
            self.assertIn("backup_restore", payload["not_proven"])
            self.assertIn("production_backup_policy", payload["not_proven"])
            self.assertIn("real_disaster_recovery", payload["not_proven"])
            for forbidden in (
                "production-token-value",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "OSS secret",
                "root password",
                "ros topic",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_accepts_local_backup_restore_artifact_without_production_dr_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "relay_state.sqlite"
            artifact_path = pathlib.Path(tmp) / "relay_backup.json"
            store = SQLiteRelayStore(state_path)
            now = time.time()
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "id": "cmd-preflight-backup",
                    "type": "collect",
                    "expires_at": now + 300.0,
                    "payload": {"target": "trash_station"},
                },
            )
            store.post_status(
                "trashbot-001",
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "state": "idle",
                    "updated_at": now,
                },
            )
            create_sqlite_backup_artifact(state_path, artifact_path)
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(state_path),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertEqual(payload["evidence_boundary"], BACKUP_RESTORE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["backup_restore_drill"]["status"], "pass")
            self.assertEqual(checks["backup_restore_drill"]["details"]["command_count"], 1)
            self.assertNotIn("backup_restore", payload["not_proven"])
            self.assertIn("production_backup_policy", payload["not_proven"])
            self.assertIn("real_disaster_recovery", payload["not_proven"])
            for forbidden in (
                str(state_path),
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_network_recovery_artifact_as_software_proof_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = pathlib.Path(tmp) / "network_recovery.sqlite"
            artifact_path = pathlib.Path(tmp) / "network_recovery.json"
            create_network_recovery_artifact(artifact_path, state_path, state_backend="sqlite")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(state_path),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["evidence_boundary"], NETWORK_RECOVERY_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["network_recovery_drill"]["status"], "pass")
            self.assertEqual(checks["network_recovery_drill"]["details"]["step_count"], 4)
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("delivery_success", payload["not_proven"])
            for forbidden in (
                str(state_path),
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_blocks_invalid_or_stale_network_recovery_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/prod/date/task/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["network_recovery_drill"]["status"], "warning")

            invalid_path = root / "invalid_network_recovery.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            self.assertEqual(invalid_checks["network_recovery_drill"]["status"], "blocked")
            self.assertEqual(invalid_checks["network_recovery_drill"]["code"], "network_recovery_artifact_invalid")

    def test_oss_cdn_manifest_artifact_generation_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "oss_cdn_manifest.json"

            result = create_oss_cdn_manifest_artifact(
                artifact_path,
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-12",
            )
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = oss_cdn_manifest_summary(artifact_path)
            encoded = json.dumps(artifact, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], OSS_CDN_MANIFEST_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY)
            self.assertEqual(artifact["bucket"], OSS_CDN_BUCKET)
            self.assertEqual(artifact["region"], OSS_CDN_REGION)
            self.assertEqual(artifact["prefix"], "rober/robot-local-proof/2026-05-12/task-local-proof/")
            self.assertEqual(artifact["cdn_base_url"], OSS_CDN_BASE_URL)
            self.assertEqual(
                artifact["objects"][0]["cdn_url"],
                "https://cdn.bytegallop.com/rober/robot-local-proof/2026-05-12/task-local-proof/diagnostic_snapshot.json",
            )
            self.assertEqual(summary["object_count"], 1)
            for required in (
                "real_oss_upload",
                "sts_issuance",
                "cdn_origin_fetch",
                "lifecycle_policy",
                "production_account",
                "real_cloud",
                "real_4g_sim",
                "https_tls_public_ingress",
                "production_db_or_queue",
                "nav2_or_fixed_route_delivery",
                "wave_rover_or_hil",
            ):
                self.assertIn(required, artifact["not_proven"])
            for forbidden in (
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "root password",
                "OSS secret",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_oss_cdn_manifest_validation_fails_closed_on_checksum_and_url_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            checksum_path = pathlib.Path(tmp) / "manifest_checksum.json"
            url_path = pathlib.Path(tmp) / "manifest_url.json"
            create_oss_cdn_manifest_artifact(
                checksum_path,
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-12",
            )

            checksum_artifact = json.loads(checksum_path.read_text(encoding="utf-8"))
            checksum_artifact["bucket"] = "other-bucket"
            checksum_path.write_text(json.dumps(checksum_artifact, ensure_ascii=False), encoding="utf-8")
            checksum_summary = oss_cdn_manifest_summary(checksum_path)
            self.assertFalse(checksum_summary["ok"])
            self.assertEqual(checksum_summary["reason_code"], "manifest_invalid")

            url_artifact = build_oss_cdn_manifest_payload(
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-12",
            )
            url_artifact["objects"][0]["cdn_url"] = "https://cdn.bytegallop.com/rober/wrong.json"
            body = {key: value for key, value in url_artifact.items() if key != "checksum"}
            # 用原 checksum 保持篡改状态，校验必须失败，不能只看 schema happy path。
            url_path.write_text(json.dumps(url_artifact, ensure_ascii=False), encoding="utf-8")
            self.assertNotEqual(url_artifact["checksum"], json.dumps(body, ensure_ascii=False))
            url_summary = oss_cdn_manifest_summary(url_path)
            self.assertFalse(url_summary["ok"])
            self.assertEqual(url_summary["reason_code"], "manifest_invalid")

    def test_phone_oss_cdn_manifest_summary_covers_ready_missing_invalid_and_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_manifest.json"
            invalid_path = root / "invalid_manifest.json"
            stale_path = root / "stale_manifest.json"
            ready_artifact = build_oss_cdn_manifest_payload(
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-12",
                created_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready_artifact, ensure_ascii=False), encoding="utf-8")
            invalid_artifact = dict(ready_artifact)
            invalid_artifact["bucket"] = "other-bucket"
            invalid_path.write_text(json.dumps(invalid_artifact, ensure_ascii=False), encoding="utf-8")
            stale_artifact = build_oss_cdn_manifest_payload(
                "robot-local-proof",
                "task-stale-proof",
                date_text="2026-05-12",
                created_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale_artifact, ensure_ascii=False), encoding="utf-8")

            ready = build_phone_oss_cdn_manifest_summary(ready_path, now=1778562000.0)
            missing = build_phone_oss_cdn_manifest_summary(root / "missing.json", now=1778562000.0)
            invalid = build_phone_oss_cdn_manifest_summary(invalid_path, now=1778562000.0)
            stale = build_phone_oss_cdn_manifest_summary(stale_path, now=1778562000.0)
            encoded = json.dumps(
                {"ready": ready, "missing": missing, "invalid": invalid, "stale": stale},
                ensure_ascii=False,
            )

            self.assertEqual(ready["state"], "ready")
            self.assertEqual(ready["evidence_boundary"], OSS_CDN_PHONE_MANIFEST_EVIDENCE_BOUNDARY)
            self.assertEqual(ready["object_count"], 1)
            self.assertEqual(ready["staleness"], "fresh")
            self.assertEqual(missing["state"], "missing")
            self.assertEqual(invalid["state"], "invalid")
            self.assertEqual(stale["state"], "stale")
            self.assertIn("real_oss_upload", ready["not_proven"])
            self.assertIn("real_4g_sim", ready["not_proven"])
            self.assertIn("wave_rover_or_hil", ready["not_proven"])
            self.assertNotIn("object_key", encoded)
            self.assertNotIn("checksum", encoded)
            self.assertNotIn(str(ready_path), encoded)

    def test_preflight_consumes_valid_oss_cdn_manifest_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "oss_cdn_manifest.json"
            create_oss_cdn_manifest_artifact(
                artifact_path,
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-12",
            )
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertEqual(payload["evidence_boundary"], OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["oss_cdn_manifest"]["status"], "pass")
            self.assertEqual(checks["oss_cdn_manifest"]["details"]["object_count"], 1)
            self.assertIn("real_oss_upload", payload["not_proven"])
            self.assertIn("sts_issuance", payload["not_proven"])
            self.assertIn("cdn_origin_fetch", payload["not_proven"])
            self.assertIn("lifecycle_policy", payload["not_proven"])
            self.assertIn("production_account", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("https_tls_public_ingress", payload["not_proven"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("nav2_or_fixed_route_delivery", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_oss_cdn_manifest_missing_and_blocks_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["oss_cdn_manifest"]["status"], "warning")
            self.assertEqual(missing_checks["oss_cdn_manifest"]["code"], "oss_cdn_manifest_artifact_missing")

            invalid_path = pathlib.Path(tmp) / "invalid_manifest.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["oss_cdn_manifest"]["status"], "blocked")
            self.assertEqual(invalid_checks["oss_cdn_manifest"]["code"], "oss_cdn_manifest_artifact_invalid")
            self.assertNotIn(str(invalid_path), encoded)

    def test_oss_cdn_live_probe_artifact_and_preflight_stay_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            manifest_path = root / "oss_cdn_manifest.json"
            live_probe_path = root / "oss_cdn_live_probe.json"
            create_oss_cdn_manifest_artifact(
                manifest_path,
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-13",
            )
            fake_probe = {
                "status": "passed",
                "code": "http_head_observed",
                "http_status": 200,
                "reachable": True,
                "method": "HEAD",
                "latency_ms": 3,
            }
            with mock.patch.object(relay_module, "_probe_oss_cdn_object", return_value=fake_probe):
                result = create_oss_cdn_live_probe_artifact(live_probe_path, manifest_path, timeout_sec=0.01)
            artifact = json.loads(live_probe_path.read_text(encoding="utf-8"))
            summary = oss_cdn_live_probe_summary(live_probe_path)
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-13/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT": str(manifest_path),
                "TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT": str(live_probe_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {"result": result, "artifact": artifact, "summary": summary, "preflight": payload},
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], OSS_CDN_LIVE_PROBE_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["evidence_boundary"], OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["live_probe_complete"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(summary["object_count"], 1)
            self.assertEqual(summary["probe_count"], 1)
            self.assertTrue(summary["object_probe_observed"])
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["oss_cdn_live_probe"]["status"], "pass")
            self.assertFalse(checks["oss_cdn_live_probe"]["details"]["production_ready"])
            self.assertFalse(checks["oss_cdn_live_probe"]["details"]["live_probe_complete"])
            for marker in (
                "real_oss_upload",
                "sts_issuance",
                "cdn_origin_fetch",
                "real_cloud",
                "real_4g_sim",
                "wave_rover_or_hil",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(manifest_path),
                str(live_probe_path),
                str(root / "relay_state.sqlite"),
                "https://cdn.bytegallop.com/rober/",
                '"object_key":',
                "production-token-value",
                "Authorization",
                "Bearer",
                "token",
                "OSS secret",
                "response body",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_oss_cdn_live_probe_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            manifest_path = root / "oss_cdn_manifest.json"
            hostile_path = root / "hostile_oss_cdn_live_probe.json"
            create_oss_cdn_manifest_artifact(
                manifest_path,
                "robot-local-proof",
                "task-local-proof",
                date_text="2026-05-13",
            )
            hostile = build_oss_cdn_live_probe_payload(
                manifest_path,
                generated_at="2026-05-13T14:00:00Z",
                probe_fn=lambda _url, timeout_sec=2.0: {
                    "status": "passed",
                    "code": "http_head_observed",
                    "http_status": 200,
                    "reachable": True,
                    "method": "HEAD",
                    "latency_ms": 1,
                },
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token https://cdn.bytegallop.com/rober/ "
                "credential-bearing response body raw state path /dev/ttyUSB0 baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")
            env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT": str(hostile_path),
            }

            missing_payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                }
            )
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            summary = oss_cdn_live_probe_summary(hostile_path)
            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertEqual(missing_checks["oss_cdn_live_probe"]["status"], "warning")
            self.assertEqual(missing_checks["oss_cdn_live_probe"]["code"], "oss_cdn_live_probe_artifact_missing")
            self.assertFalse(summary["ok"])
            self.assertEqual(checks["oss_cdn_live_probe"]["status"], "blocked")
            self.assertEqual(checks["oss_cdn_live_probe"]["code"], "oss_cdn_live_probe_artifact_invalid")
            for forbidden in (
                str(manifest_path),
                str(hostile_path),
                str(root / "relay_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "https://cdn.bytegallop.com/rober/",
                "credential-bearing",
                "response body",
                "raw state path",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_credential_rotation_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "credential_rotation.json"
            result = create_credential_rotation_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = credential_rotation_artifact_summary(artifact_path)
            phone = build_phone_credential_rotation_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], CREDENTIAL_ROTATION_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY)
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], CREDENTIAL_ROTATION_PHONE_EVIDENCE_BOUNDARY)
            self.assertEqual(phone["bearer_rotation_status"], "local_rotation_gate_passed")
            self.assertIn("production_credential_rotation", phone["not_proven"])
            self.assertIn("sts_issuance", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_credential_rotation_summary_fails_closed_for_invalid_stale_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_credential_rotation.json"
            invalid_path = root / "invalid_credential_rotation.json"
            stale_path = root / "stale_credential_rotation.json"
            hostile_path = root / "hostile_credential_rotation.json"
            ready = build_credential_rotation_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["schema"] = "wrong"
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_credential_rotation_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token AK/SK OSS secret root password raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_credential_rotation_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_credential_rotation_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_credential_rotation_summary(stale_path, now=1778562000.0)
            hostile_summary = build_phone_credential_rotation_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_credential_rotation_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "AK/SK",
                "OSS secret",
                "root password",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_credential_rotation_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "credential_rotation.json"
            create_credential_rotation_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["evidence_boundary"], CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["credential_rotation"]["status"], "pass")
            self.assertEqual(
                checks["credential_rotation"]["details"]["bearer_rotation_status"],
                "local_rotation_gate_passed",
            )
            self.assertIn("production_credential_rotation", payload["not_proven"])
            self.assertIn("sts_issuance", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("nav2_or_fixed_route_delivery", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "AK/SK",
                "OSS secret",
                "root password",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_credential_rotation_missing_and_blocks_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["credential_rotation"]["status"], "warning")
            self.assertEqual(missing_checks["credential_rotation"]["code"], "credential_rotation_artifact_missing")

            invalid_path = pathlib.Path(tmp) / "invalid_credential_rotation.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["credential_rotation"]["status"], "blocked")
            self.assertEqual(invalid_checks["credential_rotation"]["code"], "credential_rotation_artifact_invalid")
            self.assertNotIn(str(invalid_path), encoded)

    def test_provisioning_audit_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "provisioning_audit.json"
            result = create_provisioning_audit_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = provisioning_audit_artifact_summary(artifact_path)
            phone = build_phone_provisioning_audit_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], PROVISIONING_AUDIT_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], PROVISIONING_AUDIT_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], PROVISIONING_AUDIT_PHONE_EVIDENCE_BOUNDARY)
            self.assertEqual(phone["robot_provisioning_status"], "local_contract_artifact_present")
            self.assertEqual(phone["sts_issuance_status"], "not_issued_boundary_documented")
            self.assertEqual(phone["audit_log_status"], "local_audit_contract_artifact_present")
            self.assertFalse(phone["production_ready"])
            self.assertEqual(phone["overall_status"], "blocked")
            self.assertIn("real_sts_issuance", phone["not_proven"])
            self.assertIn("real_audit_log_sink", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_provisioning_audit_summary_fails_closed_for_invalid_stale_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_provisioning_audit.json"
            invalid_path = root / "invalid_provisioning_audit.json"
            stale_path = root / "stale_provisioning_audit.json"
            hostile_path = root / "hostile_provisioning_audit.json"
            ready = build_provisioning_audit_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["schema"] = "wrong"
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_provisioning_audit_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token AK/SK OSS secret root password credential URL "
                "raw state path /dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_provisioning_audit_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_provisioning_audit_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_provisioning_audit_summary(stale_path, now=1778562000.0)
            hostile_summary = build_phone_provisioning_audit_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_provisioning_audit_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "AK/SK",
                "OSS secret",
                "root password",
                "credential URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_provisioning_audit_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "provisioning_audit.json"
            create_provisioning_audit_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], PROVISIONING_AUDIT_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["provisioning_audit"]["status"], "pass")
            self.assertEqual(
                checks["provisioning_audit"]["details"]["sts_issuance_status"],
                "not_issued_boundary_documented",
            )
            self.assertFalse(checks["provisioning_audit"]["details"]["production_ready"])
            self.assertIn("production_robot_provisioning", payload["not_proven"])
            self.assertIn("real_sts_issuance", payload["not_proven"])
            self.assertIn("real_audit_log_sink", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("nav2_or_fixed_route_delivery", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "AK/SK",
                "OSS secret",
                "root password",
                "credential URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_provisioning_audit_missing_and_blocks_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["provisioning_audit"]["status"], "warning")
            self.assertEqual(missing_checks["provisioning_audit"]["code"], "provisioning_audit_artifact_missing")

            invalid_path = pathlib.Path(tmp) / "invalid_provisioning_audit.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["provisioning_audit"]["status"], "blocked")
            self.assertEqual(invalid_checks["provisioning_audit"]["code"], "provisioning_audit_artifact_invalid")
            self.assertNotIn(str(invalid_path), encoded)

    def test_production_store_queue_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "production_store_queue.json"
            result = create_production_store_queue_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = production_store_queue_artifact_summary(artifact_path)
            phone = build_phone_production_store_queue_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], PRODUCTION_STORE_QUEUE_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], PRODUCTION_STORE_QUEUE_PHONE_EVIDENCE_BOUNDARY)
            self.assertEqual(phone["store_contract_status"], "local_store_contract_artifact_present")
            self.assertEqual(phone["queue_contract_status"], "local_queue_contract_artifact_present")
            self.assertEqual(phone["consistency_status"], "multi_instance_consistency_not_proven")
            self.assertFalse(phone["production_ready"])
            self.assertEqual(phone["overall_status"], "blocked")
            self.assertIn("production_db_or_queue", phone["not_proven"])
            self.assertIn("multi_instance_consistency", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_production_store_queue_summary_fails_closed_for_invalid_stale_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_production_store_queue.json"
            invalid_path = root / "invalid_production_store_queue.json"
            stale_path = root / "stale_production_store_queue.json"
            hostile_path = root / "hostile_production_store_queue.json"
            ready = build_production_store_queue_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["schema"] = "wrong"
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_production_store_queue_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_production_store_queue_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_production_store_queue_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_production_store_queue_summary(stale_path, now=1778562000.0)
            hostile_summary = build_phone_production_store_queue_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_production_store_queue_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_production_store_queue_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "production_store_queue.json"
            create_production_store_queue_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["production_store_queue"]["status"], "pass")
            self.assertEqual(
                checks["production_store_queue"]["details"]["consistency_status"],
                "multi_instance_consistency_not_proven",
            )
            self.assertFalse(checks["production_store_queue"]["details"]["production_ready"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("multi_instance_consistency", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("nav2_or_fixed_route_delivery", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "postgres://",
                "queue URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_production_store_queue_missing_and_blocks_invalid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["production_store_queue"]["status"], "warning")
            self.assertEqual(
                missing_checks["production_store_queue"]["code"],
                "production_store_queue_artifact_missing",
            )

            invalid_path = pathlib.Path(tmp) / "invalid_production_store_queue.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["production_store_queue"]["status"], "blocked")
            self.assertEqual(
                invalid_checks["production_store_queue"]["code"],
                "production_store_queue_artifact_invalid",
            )
            self.assertNotIn(str(invalid_path), encoded)

    def test_queue_ordering_drill_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "queue_ordering_drill.json"
            result = create_queue_ordering_drill_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = queue_ordering_drill_artifact_summary(artifact_path)
            phone = build_phone_queue_ordering_drill_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], QUEUE_ORDERING_DRILL_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY)
            self.assertEqual(artifact["adjacent_command_ids"], ["cmd-9", "cmd-10"])
            self.assertEqual(artifact["observed_order"], ["cmd-9", "cmd-10"])
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], QUEUE_ORDERING_DRILL_PHONE_EVIDENCE_BOUNDARY)
            self.assertIn("cmd-9_before_cmd-10", phone["ordering_invariant"])
            self.assertIn("parallel_local_submits", phone["concurrency_invariant"])
            self.assertIn("terminal_ack", phone["cursor_invariant"])
            self.assertIn("does_not_mean_delivery_success", phone["ack_invariant"])
            self.assertIn("production_queue_ordering", phone["not_proven"])
            self.assertIn("production_db_or_queue", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_queue_ordering_drill_summary_fails_closed_for_invalid_stale_failed_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_queue_ordering.json"
            invalid_path = root / "invalid_queue_ordering.json"
            stale_path = root / "stale_queue_ordering.json"
            failed_path = root / "failed_queue_ordering.json"
            hostile_path = root / "hostile_queue_ordering.json"
            ready = build_queue_ordering_drill_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["schema"] = "wrong"
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_queue_ordering_drill_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            failed = build_queue_ordering_drill_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
                drill_status="failed",
            )
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_queue_ordering_drill_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_queue_ordering_drill_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_queue_ordering_drill_summary(stale_path, now=1778562000.0)
            failed_summary = build_phone_queue_ordering_drill_summary(failed_path, now=1778562000.0)
            hostile_summary = build_phone_queue_ordering_drill_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_queue_ordering_drill_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "failed": failed_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(failed_summary["state"], "failed")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_queue_ordering_drill_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "queue_ordering_drill.json"
            create_queue_ordering_drill_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["queue_ordering_drill"]["status"], "pass")
            self.assertEqual(checks["queue_ordering_drill"]["details"]["adjacent_command_ids"], ["cmd-9", "cmd-10"])
            self.assertFalse(checks["queue_ordering_drill"]["details"]["production_ready"])
            self.assertIn("production_queue_ordering", payload["not_proven"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("multi_instance_consistency", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "postgres://",
                "queue URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_queue_ordering_missing_and_blocks_invalid_or_failed_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["queue_ordering_drill"]["status"], "warning")
            self.assertEqual(
                missing_checks["queue_ordering_drill"]["code"],
                "queue_ordering_drill_artifact_missing",
            )

            invalid_path = pathlib.Path(tmp) / "invalid_queue_ordering.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded_invalid = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["queue_ordering_drill"]["status"], "blocked")
            self.assertEqual(
                invalid_checks["queue_ordering_drill"]["code"],
                "queue_ordering_drill_artifact_invalid",
            )
            self.assertNotIn(str(invalid_path), encoded_invalid)

            failed_path = pathlib.Path(tmp) / "failed_queue_ordering.json"
            failed = build_queue_ordering_drill_artifact_payload("robot-local-proof", drill_status="failed")
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            failed_env = dict(base_env)
            failed_env["TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT"] = str(failed_path)
            failed_payload = production_preflight_payload(failed_env)
            failed_checks = {check["name"]: check for check in failed_payload["checks"]}

            self.assertEqual(failed_checks["queue_ordering_drill"]["status"], "blocked")
            self.assertEqual(
                failed_checks["queue_ordering_drill"]["code"],
                "queue_ordering_drill_artifact_failed",
            )

    def test_transaction_isolation_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "transaction_isolation.json"
            result = create_transaction_isolation_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = transaction_isolation_artifact_summary(artifact_path)
            phone = build_phone_transaction_isolation_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], TRANSACTION_ISOLATION_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY)
            self.assertEqual(artifact["command_a_id"], "cmd-transaction-a")
            self.assertEqual(artifact["command_b_id"], "cmd-transaction-b")
            self.assertEqual(artifact["command_a_ack_state"], "processing")
            self.assertEqual(artifact["terminal_ack_ids"], ["cmd-transaction-b"])
            self.assertEqual(artifact["cursor_after_interleaving"], "cmd-before-transaction-a")
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], TRANSACTION_ISOLATION_PHONE_EVIDENCE_BOUNDARY)
            self.assertIn("unfinished_command_a", phone["cursor_invariant"])
            self.assertIn("not_delivery_success", phone["ack_invariant"])
            self.assertIn("production_transaction_isolation", phone["not_proven"])
            self.assertIn("production_db_or_queue", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_transaction_isolation_summary_fails_closed_for_invalid_stale_failed_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_transaction_isolation.json"
            invalid_path = root / "invalid_transaction_isolation.json"
            stale_path = root / "stale_transaction_isolation.json"
            failed_path = root / "failed_transaction_isolation.json"
            hostile_path = root / "hostile_transaction_isolation.json"
            ready = build_transaction_isolation_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["delivery_success"] = True
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_transaction_isolation_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            failed = build_transaction_isolation_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
                drill_status="failed",
            )
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL raw state path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_transaction_isolation_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_transaction_isolation_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_transaction_isolation_summary(stale_path, now=1778562000.0)
            failed_summary = build_phone_transaction_isolation_summary(failed_path, now=1778562000.0)
            hostile_summary = build_phone_transaction_isolation_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_transaction_isolation_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "failed": failed_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(failed_summary["state"], "failed")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "raw state path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_transaction_isolation_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "transaction_isolation.json"
            create_transaction_isolation_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["transaction_isolation"]["status"], "pass")
            self.assertEqual(
                checks["transaction_isolation"]["details"]["cursor_after_interleaving"],
                "cmd-before-transaction-a",
            )
            self.assertFalse(checks["transaction_isolation"]["details"]["delivery_success"])
            self.assertFalse(checks["transaction_isolation"]["details"]["production_ready"])
            self.assertIn("production_transaction_isolation", payload["not_proven"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("multi_instance_consistency", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "postgres://",
                "queue URL",
                "raw state path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_transaction_isolation_missing_and_blocks_invalid_or_failed_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["transaction_isolation"]["status"], "warning")
            self.assertEqual(
                missing_checks["transaction_isolation"]["code"],
                "transaction_isolation_artifact_missing",
            )

            invalid_path = pathlib.Path(tmp) / "invalid_transaction_isolation.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded_invalid = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["transaction_isolation"]["status"], "blocked")
            self.assertEqual(
                invalid_checks["transaction_isolation"]["code"],
                "transaction_isolation_artifact_invalid",
            )
            self.assertNotIn(str(invalid_path), encoded_invalid)

            failed_path = pathlib.Path(tmp) / "failed_transaction_isolation.json"
            failed = build_transaction_isolation_artifact_payload("robot-local-proof", drill_status="failed")
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            failed_env = dict(base_env)
            failed_env["TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT"] = str(failed_path)
            failed_payload = production_preflight_payload(failed_env)
            failed_checks = {check["name"]: check for check in failed_payload["checks"]}

            self.assertEqual(failed_checks["transaction_isolation"]["status"], "blocked")
            self.assertEqual(
                failed_checks["transaction_isolation"]["code"],
                "transaction_isolation_artifact_failed",
            )

    def test_production_recovery_artifact_generation_and_phone_summary_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "production_recovery.json"
            result = create_production_recovery_artifact(artifact_path, "robot-local-proof")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = production_recovery_artifact_summary(artifact_path)
            phone = build_phone_production_recovery_summary(artifact_path)
            encoded_phone = json.dumps(phone, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertEqual(artifact["schema"], PRODUCTION_RECOVERY_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(artifact["local_backup_restore_status"], "docker_local_backup_restore_artifact_verified")
            self.assertEqual(artifact["production_backup_policy_status"], "blocked_not_proven")
            self.assertEqual(artifact["disaster_recovery_status"], "blocked_not_proven")
            self.assertEqual(summary["state"], "ready")
            self.assertEqual(phone["state"], "ready")
            self.assertEqual(phone["evidence_boundary"], PRODUCTION_RECOVERY_PHONE_EVIDENCE_BOUNDARY)
            self.assertEqual(phone["recovery_drill_status"], "schema_integrity_invariants_verified")
            self.assertFalse(phone["production_ready"])
            self.assertEqual(phone["overall_status"], "blocked")
            self.assertIn("production_backup_policy", phone["not_proven"])
            self.assertIn("real_disaster_recovery", phone["not_proven"])
            self.assertIn("production_db_or_queue", phone["not_proven"])
            self.assertNotIn("checksum", encoded_phone)
            self.assertNotIn(str(artifact_path), encoded_phone)
            self.assertNotIn("robot-local-proof", encoded_phone)

    def test_production_recovery_summary_fails_closed_for_invalid_stale_failed_blocked_and_hostile_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            ready_path = root / "ready_production_recovery.json"
            invalid_path = root / "invalid_production_recovery.json"
            stale_path = root / "stale_production_recovery.json"
            failed_path = root / "failed_production_recovery.json"
            blocked_path = root / "blocked_production_recovery.json"
            hostile_path = root / "hostile_production_recovery.json"
            ready = build_production_recovery_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
            )
            ready_path.write_text(json.dumps(ready, ensure_ascii=False), encoding="utf-8")
            invalid = dict(ready)
            invalid["checksum"] = "bad"
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            stale = build_production_recovery_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-10T04:00:00Z",
            )
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            failed = build_production_recovery_artifact_payload(
                "robot-local-proof",
                generated_at="2026-05-12T04:00:00Z",
                drill_status="failed",
            )
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            blocked = dict(ready)
            blocked["production_ready"] = True
            body = {key: value for key, value in blocked.items() if key != "checksum"}
            blocked["checksum"] = _sha256_checksum(body)
            blocked_path.write_text(json.dumps(blocked, ensure_ascii=False), encoding="utf-8")
            hostile = dict(ready)
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL backup path "
                "/dev/ttyUSB0 serial baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            ok = build_phone_production_recovery_summary(ready_path, now=1778562000.0)
            invalid_summary = build_phone_production_recovery_summary(invalid_path, now=1778562000.0)
            stale_summary = build_phone_production_recovery_summary(stale_path, now=1778562000.0)
            failed_summary = build_phone_production_recovery_summary(failed_path, now=1778562000.0)
            blocked_summary = build_phone_production_recovery_summary(blocked_path, now=1778562000.0)
            hostile_summary = build_phone_production_recovery_summary(hostile_path, now=1778562000.0)
            missing_summary = build_phone_production_recovery_summary(root / "missing.json", now=1778562000.0)
            encoded = json.dumps(
                {
                    "ok": ok,
                    "invalid": invalid_summary,
                    "stale": stale_summary,
                    "failed": failed_summary,
                    "blocked": blocked_summary,
                    "hostile": hostile_summary,
                    "missing": missing_summary,
                },
                ensure_ascii=False,
            )

            self.assertEqual(ok["state"], "ready")
            self.assertEqual(invalid_summary["state"], "invalid")
            self.assertEqual(stale_summary["state"], "stale")
            self.assertEqual(failed_summary["state"], "failed")
            self.assertEqual(blocked_summary["state"], "invalid")
            self.assertEqual(hostile_summary["state"], "invalid")
            self.assertEqual(missing_summary["state"], "missing")
            for forbidden in (
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "backup path",
                "/dev/ttyUSB0",
                "serial",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_db_queue_external_probe_bundle_and_preflight_are_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            artifact_path = root / "cloud_db_queue_external_probe.json"
            env = {
                "TRASHBOT_REMOTE_CLOUD_DB_CONNECTIVITY_PROBE_STATUS": "not_run",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_CONNECTIVITY_PROBE_STATUS": "not_run",
                "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_MULTI_INSTANCE_CONSISTENCY_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_BACKUP_RECOVERY_EXTERNAL_PROBE_STATUS": "not_externally_proven",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            result = create_cloud_db_queue_external_probe_bundle_artifact(artifact_path, env)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = cloud_db_queue_external_probe_bundle_summary(artifact_path)
            preflight_env = dict(env)
            preflight_env["TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT"] = str(artifact_path)
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {"result": result, "artifact": artifact, "summary": summary, "preflight": payload},
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["evidence_boundary"], CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["external_probe_complete"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(summary["probe_count"], 8)
            self.assertEqual(summary["db_connectivity_status"], "not_run")
            self.assertEqual(summary["queue_connectivity_status"], "not_run")
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_db_queue_external_probe_bundle"]["status"], "pass")
            self.assertFalse(
                checks["cloud_db_queue_external_probe_bundle"]["details"]["production_ready"]
            )
            self.assertFalse(
                checks["cloud_db_queue_external_probe_bundle"]["details"]["external_probe_complete"]
            )
            self.assertEqual(
                checks["cloud_db_queue_external_probe_bundle"]["details"]["redaction_status"]["status"],
                "pass",
            )
            for marker in (
                "real_production_db_connectivity",
                "real_production_queue_connectivity",
                "multi_instance_consistency",
                "production_transaction_isolation",
                "real_disaster_recovery",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(artifact_path),
                str(root / "relay_state.sqlite"),
                "Authorization",
                "Bearer",
                "postgres://",
                "mysql://",
                "redis://",
                "amqp://",
                "database URL",
                "queue URL",
                "credential-bearing endpoint",
                "root password",
                "raw state path",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_db_queue_external_probe_warns_missing_and_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["cloud_db_queue_external_probe_bundle"]["status"], "warning")
            self.assertEqual(
                missing_checks["cloud_db_queue_external_probe_bundle"]["code"],
                "cloud_db_queue_external_probe_artifact_missing",
            )

            hostile_path = root / "hostile_cloud_db_queue_external_probe.json"
            hostile = build_cloud_db_queue_external_probe_bundle_payload(
                base_env,
                generated_at="2026-05-13T12:00:00Z",
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token postgres://db secret queue URL database URL "
                "credential-bearing endpoint raw state path /dev/ttyUSB0 baudrate WAVE ROVER ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")
            hostile_env = dict(base_env)
            hostile_env["TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT"] = str(hostile_path)

            summary = cloud_db_queue_external_probe_bundle_summary(hostile_path)
            payload = production_preflight_payload(hostile_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_db_queue_external_probe_bundle"]["status"], "blocked")
            self.assertEqual(
                checks["cloud_db_queue_external_probe_bundle"]["code"],
                "cloud_db_queue_external_probe_artifact_invalid",
            )
            for forbidden in (
                str(hostile_path),
                str(root / "relay_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "secret",
                "queue URL",
                "database URL",
                "credential-bearing endpoint",
                "raw state path",
                "/dev/ttyUSB0",
                "baudrate",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_worker_migration_rehearsal_artifact_and_preflight_are_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state_path = root / "worker_migration_rehearsal.sqlite"
            artifact_path = root / "cloud_worker_migration_rehearsal.json"
            env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            result = create_cloud_worker_migration_rehearsal_artifact(artifact_path, state_path)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = cloud_worker_migration_rehearsal_artifact_summary(artifact_path)
            preflight_env = dict(env)
            preflight_env["TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT"] = str(artifact_path)
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {"result": result, "artifact": artifact, "summary": summary, "preflight": payload},
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["summary_schema"], CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(artifact["primary_actions_enabled"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertTrue(artifact["migration_rehearsal"]["sqlite_state_initialized"])
            self.assertTrue(artifact["migration_rehearsal"]["schema_version_marked"])
            self.assertEqual(artifact["migration_rehearsal"]["idempotent_replay_status"], "passed")
            self.assertTrue(artifact["migration_rehearsal"]["bad_schema_fail_closed"])
            self.assertTrue(artifact["migration_rehearsal"]["bad_checksum_fail_closed"])
            self.assertTrue(artifact["migration_rehearsal"]["stale_artifact_fail_closed"])
            self.assertEqual(artifact["worker_rehearsal"]["command_enqueue_status"], "passed")
            self.assertEqual(artifact["worker_rehearsal"]["ack_acceptance_status"], "accepted")
            self.assertEqual(artifact["worker_rehearsal"]["ack_processing_status"], "processing")
            self.assertFalse(artifact["worker_rehearsal"]["terminal_ack_is_delivery_success"])
            self.assertTrue(artifact["worker_rehearsal"]["cursor_semantics_preserved"])
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_worker_migration_rehearsal"]["status"], "pass")
            self.assertFalse(checks["cloud_worker_migration_rehearsal"]["details"]["production_ready"])
            self.assertFalse(checks["cloud_worker_migration_rehearsal"]["details"]["delivery_success"])
            self.assertFalse(checks["cloud_worker_migration_rehearsal"]["details"]["primary_actions_enabled"])
            self.assertEqual(
                checks["cloud_worker_migration_rehearsal"]["details"]["redaction_status"]["status"],
                "pass",
            )
            for marker in (
                "software_proof_docker_cloud_worker_migration_rehearsal_gate",
                "real_production_db_connectivity",
                "production_migration_run",
                "production_queue_worker_run",
                "delivery_success",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(artifact_path),
                str(state_path),
                str(root / "preflight_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "mysql://",
                "redis://",
                "amqp://",
                "database URL",
                "queue URL",
                "credential-bearing endpoint",
                "root password",
                "raw local path",
                "/tmp/",
                "/dev/ttyUSB0",
                "UART",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_worker_migration_rehearsal_blocks_bad_schema_checksum_and_stale_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state_path = root / "worker_migration_rehearsal.sqlite"
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["cloud_worker_migration_rehearsal"]["status"], "warning")
            self.assertEqual(
                missing_checks["cloud_worker_migration_rehearsal"]["code"],
                "cloud_worker_migration_rehearsal_artifact_missing",
            )

            bad_schema_path = root / "bad_schema_cloud_worker_migration_rehearsal.json"
            bad_schema = build_cloud_worker_migration_rehearsal_artifact_payload(
                state_path,
                generated_at="2026-05-17T00:00:00Z",
            )
            bad_schema["schema"] = "trashbot.unsupported"
            bad_schema_path.write_text(json.dumps(bad_schema, ensure_ascii=False), encoding="utf-8")
            bad_schema_env = dict(base_env)
            bad_schema_env["TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT"] = str(bad_schema_path)
            bad_schema_payload = production_preflight_payload(bad_schema_env)
            bad_schema_checks = {check["name"]: check for check in bad_schema_payload["checks"]}
            self.assertFalse(cloud_worker_migration_rehearsal_artifact_summary(bad_schema_path)["ok"])
            self.assertEqual(bad_schema_checks["cloud_worker_migration_rehearsal"]["status"], "blocked")

            bad_checksum_path = root / "bad_checksum_cloud_worker_migration_rehearsal.json"
            bad_checksum = build_cloud_worker_migration_rehearsal_artifact_payload(
                root / "bad_checksum_state.sqlite",
                generated_at="2026-05-17T00:00:00Z",
            )
            bad_checksum["checksum"] = "sha256:bad"
            bad_checksum_path.write_text(json.dumps(bad_checksum, ensure_ascii=False), encoding="utf-8")
            bad_checksum_env = dict(base_env)
            bad_checksum_env["TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT"] = str(bad_checksum_path)
            bad_checksum_payload = production_preflight_payload(bad_checksum_env)
            bad_checksum_checks = {check["name"]: check for check in bad_checksum_payload["checks"]}
            self.assertFalse(cloud_worker_migration_rehearsal_artifact_summary(bad_checksum_path)["ok"])
            self.assertEqual(bad_checksum_checks["cloud_worker_migration_rehearsal"]["status"], "blocked")

            stale_path = root / "stale_cloud_worker_migration_rehearsal.json"
            stale = build_cloud_worker_migration_rehearsal_artifact_payload(
                root / "stale_state.sqlite",
                generated_at="2020-01-01T00:00:00Z",
            )
            body = {key: value for key, value in stale.items() if key != "checksum"}
            stale["checksum"] = _sha256_checksum(body)
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            stale_env = dict(base_env)
            stale_env["TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT"] = str(stale_path)
            stale_payload = production_preflight_payload(stale_env)
            stale_checks = {check["name"]: check for check in stale_payload["checks"]}
            encoded = json.dumps(
                {
                    "bad_schema": bad_schema_payload,
                    "bad_checksum": bad_checksum_payload,
                    "stale": stale_payload,
                },
                ensure_ascii=False,
            )

            self.assertFalse(cloud_worker_migration_rehearsal_artifact_summary(stale_path)["ok"])
            self.assertEqual(stale_checks["cloud_worker_migration_rehearsal"]["status"], "blocked")
            for forbidden in (
                str(bad_schema_path),
                str(bad_checksum_path),
                str(stale_path),
                str(state_path),
                str(root / "preflight_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "redis://",
                "queue URL",
                "raw local path",
                "/tmp/",
                "/dev/ttyUSB0",
                "UART",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_worker_cutover_drain_artifact_preflight_and_rerun_are_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state_path = root / "worker_cutover_drain.sqlite"
            artifact_path = root / "cloud_worker_cutover_drain.json"
            rerun_artifact_path = root / "cloud_worker_cutover_drain_rerun.json"
            robot_id = "robot-local-proof"
            store = SQLiteRelayStore(state_path)
            now = time.time()
            for index in range(2):
                status_code, submitted = store.submit_command(
                    robot_id,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "id": f"cmd-cutover-drain-{index + 1}",
                        "type": "collect",
                        "expires_at": now + 300.0,
                        "payload": {"target": f"cutover_drain_station_{index + 1}", "trash_type": index},
                    },
                )
                self.assertEqual(status_code, 201)
                self.assertFalse(submitted["duplicate"])

            result = create_cloud_worker_cutover_drain_artifact(
                artifact_path,
                state_path,
                state_backend="sqlite",
                robot_id=robot_id,
            )
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = cloud_worker_cutover_drain_artifact_summary(artifact_path)
            rerun_result = create_cloud_worker_cutover_drain_artifact(
                rerun_artifact_path,
                state_path,
                state_backend="sqlite",
                robot_id=robot_id,
            )
            rerun_artifact = json.loads(rerun_artifact_path.read_text(encoding="utf-8"))
            preflight_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT": str(artifact_path),
            }
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {
                    "result": result,
                    "artifact": artifact,
                    "summary": summary,
                    "rerun_result": rerun_result,
                    "rerun_artifact": rerun_artifact,
                    "preflight": payload,
                },
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertTrue(rerun_result["ok"])
            self.assertEqual(artifact["schema"], CLOUD_WORKER_CUTOVER_DRAIN_SCHEMA)
            self.assertEqual(artifact["summary_schema"], CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA)
            self.assertEqual(artifact["evidence_boundary"], CLOUD_WORKER_CUTOVER_DRAIN_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(artifact["primary_actions_enabled"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(artifact["cutover_drain"]["pending_count_before"], 2)
            self.assertEqual(artifact["cutover_drain"]["drained_count"], 2)
            self.assertEqual(artifact["cutover_drain"]["pending_count_after"], 0)
            self.assertEqual(artifact["cutover_drain"]["cursor_after"], "none")
            self.assertEqual(artifact["cutover_drain"]["partial_drain_status"], "passed")
            self.assertEqual(artifact["cutover_drain"]["idempotent_rerun_status"], "passed")
            self.assertFalse(artifact["cutover_drain"]["robot_action_triggered"])
            self.assertEqual(artifact["terminal_ack_summary"]["terminal_ack_count"], 2)
            self.assertFalse(artifact["terminal_ack_summary"]["terminal_ack_is_delivery_success"])
            self.assertEqual(rerun_artifact["cutover_drain"]["pending_count_before"], 0)
            self.assertEqual(rerun_artifact["cutover_drain"]["drained_count"], 0)
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], CLOUD_WORKER_CUTOVER_DRAIN_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_worker_cutover_drain"]["status"], "pass")
            self.assertFalse(checks["cloud_worker_cutover_drain"]["details"]["production_ready"])
            self.assertFalse(checks["cloud_worker_cutover_drain"]["details"]["delivery_success"])
            self.assertFalse(checks["cloud_worker_cutover_drain"]["details"]["primary_actions_enabled"])
            self.assertEqual(checks["cloud_worker_cutover_drain"]["details"]["terminal_ack_count"], 2)
            self.assertEqual(
                checks["cloud_worker_cutover_drain"]["details"]["redaction_status"]["status"],
                "pass",
            )
            for marker in (
                "software_proof_docker_cloud_worker_cutover_drain_gate",
                "trashbot.cloud_worker_cutover_drain.v1",
                "trashbot.cloud_worker_cutover_drain_summary.v1",
                "real_production_worker_cutover",
                "production_worker_drain",
                "delivery_success",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(artifact_path),
                str(rerun_artifact_path),
                str(state_path),
                str(root / "preflight_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "mysql://",
                "redis://",
                "amqp://",
                "database URL",
                "queue URL",
                "credential-bearing endpoint",
                "root password",
                "raw local path",
                "/tmp/",
                "/dev/ttyUSB0",
                "UART",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_worker_cutover_drain_fails_closed_for_partial_stale_schema_and_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            state_path = root / "worker_cutover_drain.sqlite"
            robot_id = "robot-local-proof"
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["cloud_worker_cutover_drain"]["status"], "warning")
            self.assertEqual(
                missing_checks["cloud_worker_cutover_drain"]["code"],
                "cloud_worker_cutover_drain_artifact_missing",
            )

            partial_store = SQLiteRelayStore(state_path)
            now = time.time()
            for index in range(2):
                partial_store.submit_command(
                    robot_id,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "id": f"cmd-partial-cutover-{index + 1}",
                        "type": "collect",
                        "expires_at": now + 300.0,
                        "payload": {"target": f"partial_cutover_{index + 1}", "trash_type": index},
                    },
                )
            partial_path = root / "partial_cloud_worker_cutover_drain.json"
            partial = build_cloud_worker_cutover_drain_artifact_payload(
                state_path,
                state_backend="sqlite",
                robot_id=robot_id,
                max_drain_count=1,
                generated_at="2026-05-17T00:00:00Z",
            )
            partial_path.write_text(json.dumps(partial, ensure_ascii=False), encoding="utf-8")
            partial_env = dict(base_env)
            partial_env["TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT"] = str(partial_path)
            partial_payload = production_preflight_payload(partial_env)
            partial_checks = {check["name"]: check for check in partial_payload["checks"]}
            self.assertFalse(cloud_worker_cutover_drain_artifact_summary(partial_path)["ok"])
            self.assertEqual(partial_checks["cloud_worker_cutover_drain"]["status"], "blocked")

            bad_schema_path = root / "bad_schema_cloud_worker_cutover_drain.json"
            bad_schema = build_cloud_worker_cutover_drain_artifact_payload(
                root / "bad_schema_state.sqlite",
                state_backend="sqlite",
                generated_at="2026-05-17T00:00:00Z",
            )
            bad_schema["schema"] = "trashbot.unsupported"
            bad_schema_path.write_text(json.dumps(bad_schema, ensure_ascii=False), encoding="utf-8")
            bad_schema_env = dict(base_env)
            bad_schema_env["TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT"] = str(bad_schema_path)
            bad_schema_payload = production_preflight_payload(bad_schema_env)
            bad_schema_checks = {check["name"]: check for check in bad_schema_payload["checks"]}
            self.assertFalse(cloud_worker_cutover_drain_artifact_summary(bad_schema_path)["ok"])
            self.assertEqual(bad_schema_checks["cloud_worker_cutover_drain"]["status"], "blocked")

            bad_boundary_path = root / "bad_boundary_cloud_worker_cutover_drain.json"
            bad_boundary = build_cloud_worker_cutover_drain_artifact_payload(
                root / "bad_boundary_state.sqlite",
                state_backend="sqlite",
                generated_at="2026-05-17T00:00:00Z",
            )
            bad_boundary["evidence_boundary"] = "software_proof_docker_unsupported_boundary"
            bad_boundary["checksum"] = _sha256_checksum({k: v for k, v in bad_boundary.items() if k != "checksum"})
            bad_boundary_path.write_text(json.dumps(bad_boundary, ensure_ascii=False), encoding="utf-8")
            bad_boundary_env = dict(base_env)
            bad_boundary_env["TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT"] = str(bad_boundary_path)
            bad_boundary_payload = production_preflight_payload(bad_boundary_env)
            bad_boundary_checks = {check["name"]: check for check in bad_boundary_payload["checks"]}
            self.assertFalse(cloud_worker_cutover_drain_artifact_summary(bad_boundary_path)["ok"])
            self.assertEqual(bad_boundary_checks["cloud_worker_cutover_drain"]["status"], "blocked")

            stale_path = root / "stale_cloud_worker_cutover_drain.json"
            stale = build_cloud_worker_cutover_drain_artifact_payload(
                root / "stale_state.sqlite",
                state_backend="sqlite",
                generated_at="2020-01-01T00:00:00Z",
            )
            stale["checksum"] = _sha256_checksum({k: v for k, v in stale.items() if k != "checksum"})
            stale_path.write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
            stale_env = dict(base_env)
            stale_env["TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT"] = str(stale_path)
            stale_payload = production_preflight_payload(stale_env)
            stale_checks = {check["name"]: check for check in stale_payload["checks"]}
            self.assertFalse(cloud_worker_cutover_drain_artifact_summary(stale_path)["ok"])
            self.assertEqual(stale_checks["cloud_worker_cutover_drain"]["status"], "blocked")

            unsafe_path = root / "unsafe_cloud_worker_cutover_drain.json"
            unsafe = build_cloud_worker_cutover_drain_artifact_payload(
                root / "unsafe_state.sqlite",
                state_backend="sqlite",
                generated_at="2026-05-17T00:00:00Z",
            )
            unsafe["safe_summary"] = "raw local path should fail closed"
            unsafe["retry_hint"] = "Bearer token should fail closed"
            unsafe["checksum"] = _sha256_checksum({k: v for k, v in unsafe.items() if k != "checksum"})
            unsafe_path.write_text(json.dumps(unsafe, ensure_ascii=False), encoding="utf-8")
            unsafe_env = dict(base_env)
            unsafe_env["TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT"] = str(unsafe_path)
            unsafe_payload = production_preflight_payload(unsafe_env)
            unsafe_checks = {check["name"]: check for check in unsafe_payload["checks"]}
            encoded = json.dumps(
                {
                    "partial": partial_payload,
                    "bad_schema": bad_schema_payload,
                    "bad_boundary": bad_boundary_payload,
                    "stale": stale_payload,
                    "unsafe": unsafe_payload,
                },
                ensure_ascii=False,
            )

            self.assertFalse(cloud_worker_cutover_drain_artifact_summary(unsafe_path)["ok"])
            self.assertEqual(unsafe_checks["cloud_worker_cutover_drain"]["status"], "blocked")
            for forbidden in (
                str(partial_path),
                str(bad_schema_path),
                str(bad_boundary_path),
                str(stale_path),
                str(unsafe_path),
                str(state_path),
                str(root / "preflight_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "postgres://",
                "redis://",
                "queue URL",
                "raw local path",
                "/tmp/",
                "/dev/ttyUSB0",
                "UART",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_external_evidence_intake_artifact_and_preflight_are_blocked_by_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            artifact_path = root / "external_evidence_intake.json"
            env = {
                "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_PUBLIC_INGRESS_TLS_STATUS": "not_proven",
                "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_OSS_CDN_STATUS": "not_proven",
                "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_DB_QUEUE_STATUS": "not_proven",
                "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_4G_SIM_STATUS": "not_proven",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            result = create_external_evidence_intake_artifact(artifact_path, env)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = external_evidence_intake_artifact_summary(artifact_path)
            preflight_env = dict(env)
            preflight_env["TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT"] = str(artifact_path)
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {"result": result, "artifact": artifact, "summary": summary, "preflight": payload},
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], EXTERNAL_EVIDENCE_INTAKE_SCHEMA)
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["evidence_boundary"], EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY)
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["external_evidence_complete"])
            self.assertEqual(artifact["overall_status"], "blocked")
            self.assertEqual(summary["material_count"], 4)
            self.assertEqual(summary["public_ingress_tls_status"], "not_proven")
            self.assertEqual(summary["oss_cdn_status"], "not_proven")
            self.assertEqual(summary["production_db_queue_status"], "not_proven")
            self.assertEqual(summary["four_g_sim_status"], "not_proven")
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["external_evidence_intake"]["status"], "pass")
            self.assertFalse(checks["external_evidence_intake"]["details"]["production_ready"])
            self.assertFalse(checks["external_evidence_intake"]["details"]["external_evidence_complete"])
            self.assertEqual(
                checks["external_evidence_intake"]["details"]["redaction_status"]["status"],
                "pass",
            )
            for marker in (
                "public_ingress_tls",
                "oss_cdn",
                "production_db_queue",
                "four_g_sim",
                "real_cloud",
                "real_4g_sim",
                "delivery_success",
            ):
                self.assertIn(marker, encoded)
            for forbidden in (
                str(artifact_path),
                str(root / "relay_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "https://",
                "credential-bearing endpoint",
                "OSS_ACCESS_KEY_SECRET",
                "AK/SK",
                "postgres://",
                "redis://",
                "response body",
                "traceback",
                "/dev/ttyUSB0",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_external_evidence_intake_blocks_hostile_artifact_without_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }
            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["external_evidence_intake"]["status"], "warning")
            self.assertEqual(
                missing_checks["external_evidence_intake"]["code"],
                "external_evidence_intake_artifact_missing",
            )

            hostile_path = root / "hostile_external_evidence_intake.json"
            hostile = build_external_evidence_intake_artifact_payload(
                base_env,
                generated_at="2026-05-13T12:00:00Z",
            )
            hostile["safe_summary"] = (
                "Authorization Bearer token https://cloud.example.com credential-bearing endpoint "
                "OSS_ACCESS_KEY_SECRET AK/SK postgres://db redis://queue response body traceback "
                "/dev/ttyUSB0 ROS topic /cmd_vel"
            )
            body = {key: value for key, value in hostile.items() if key != "checksum"}
            hostile["checksum"] = _sha256_checksum(body)
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")
            hostile_env = dict(base_env)
            hostile_env["TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT"] = str(hostile_path)

            summary = external_evidence_intake_artifact_summary(hostile_path)
            payload = production_preflight_payload(hostile_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["external_evidence_intake"]["status"], "blocked")
            self.assertEqual(
                checks["external_evidence_intake"]["code"],
                "external_evidence_intake_artifact_invalid",
            )
            for forbidden in (
                str(hostile_path),
                str(root / "relay_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "https://cloud.example.com",
                "credential-bearing endpoint",
                "OSS_ACCESS_KEY_SECRET",
                "AK/SK",
                "postgres://",
                "redis://",
                "response body",
                "traceback",
                "/dev/ttyUSB0",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_consumes_valid_production_recovery_artifact_without_production_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact_path = pathlib.Path(tmp) / "production_recovery.json"
            create_production_recovery_artifact(artifact_path, "robot-local-proof")
            env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT": str(artifact_path),
            }

            payload = production_preflight_payload(env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(payload, ensure_ascii=False)

            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["overall_status"], "blocked")
            self.assertEqual(payload["evidence_boundary"], PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["production_recovery"]["status"], "pass")
            self.assertEqual(
                checks["production_recovery"]["details"]["production_backup_policy_status"],
                "blocked_not_proven",
            )
            self.assertEqual(
                checks["production_recovery"]["details"]["disaster_recovery_status"],
                "blocked_not_proven",
            )
            self.assertFalse(checks["production_recovery"]["details"]["production_ready"])
            self.assertIn("production_backup_policy", payload["not_proven"])
            self.assertIn("real_disaster_recovery", payload["not_proven"])
            self.assertIn("production_db_or_queue", payload["not_proven"])
            self.assertIn("multi_instance_consistency", payload["not_proven"])
            self.assertIn("real_cloud", payload["not_proven"])
            self.assertIn("real_4g_sim", payload["not_proven"])
            self.assertIn("wave_rover_or_hil", payload["not_proven"])
            for forbidden in (
                str(artifact_path),
                "production-token-value",
                "Authorization",
                "Bearer",
                "postgres://",
                "queue URL",
                "backup path",
                "/cmd_vel",
                "ttyUSB",
                "baudrate",
                "WAVE ROVER",
                "/trashbot/",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_preflight_warns_when_production_recovery_missing_and_blocks_invalid_or_failed_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "production-token-value",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "https://relay.example.invalid",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "terminated",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "public_https",
                "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET": "bytegallop",
                "TRASHBOT_REMOTE_CLOUD_OSS_REGION": "oss-cn-hangzhou",
                "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX": "rober/robot-local-proof/2026-05-12/task-local-proof/",
                "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL": "https://cdn.bytegallop.com/rober/",
                "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE": "sts",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(pathlib.Path(tmp) / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            missing_payload = production_preflight_payload(base_env)
            missing_checks = {check["name"]: check for check in missing_payload["checks"]}
            self.assertEqual(missing_checks["production_recovery"]["status"], "warning")
            self.assertEqual(
                missing_checks["production_recovery"]["code"],
                "production_recovery_artifact_missing",
            )

            invalid_path = pathlib.Path(tmp) / "invalid_production_recovery.json"
            invalid_path.write_text(json.dumps({"schema": "wrong"}, ensure_ascii=False), encoding="utf-8")
            invalid_env = dict(base_env)
            invalid_env["TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT"] = str(invalid_path)
            invalid_payload = production_preflight_payload(invalid_env)
            invalid_checks = {check["name"]: check for check in invalid_payload["checks"]}
            encoded_invalid = json.dumps(invalid_payload, ensure_ascii=False)

            self.assertEqual(invalid_checks["production_recovery"]["status"], "blocked")
            self.assertEqual(
                invalid_checks["production_recovery"]["code"],
                "production_recovery_artifact_invalid",
            )
            self.assertNotIn(str(invalid_path), encoded_invalid)

            failed_path = pathlib.Path(tmp) / "failed_production_recovery.json"
            failed = build_production_recovery_artifact_payload("robot-local-proof", drill_status="failed")
            failed_path.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
            failed_env = dict(base_env)
            failed_env["TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT"] = str(failed_path)
            failed_payload = production_preflight_payload(failed_env)
            failed_checks = {check["name"]: check for check in failed_payload["checks"]}

            self.assertEqual(failed_checks["production_recovery"]["status"], "blocked")
            self.assertEqual(
                failed_checks["production_recovery"]["code"],
                "production_recovery_artifact_failed",
            )


def load_tests(loader, tests, pattern):
    # sprint 验收命令会把 `A or B` 作为 `unittest -k` 参数；标准 unittest 不解析布尔 or。
    # 这里仅为本模块测试加载做兼容，确保给定验收命令能稳定选中两组相关回归测试。
    raw_patterns = [str(item).strip("*") for item in (getattr(loader, "testNamePatterns", None) or [])]
    or_patterns = [item for item in raw_patterns if " or " in item]
    if not or_patterns:
        return tests

    terms = []
    for item in or_patterns:
        terms.extend(part.strip() for part in item.split(" or ") if part.strip())
    suite = unittest.TestSuite()
    unfiltered_loader = unittest.TestLoader()
    for case in (RemoteCloudRelayHttpTest, RemoteCloudRelayStoreTest, RemoteCloudRelayPreflightTest):
        for name in unfiltered_loader.getTestCaseNames(case):
            test_id = f"{__name__}.{case.__name__}.{name}"
            if any(term in name or term in test_id for term in terms):
                suite.addTest(case(name))
    return suite


if __name__ == "__main__":
    unittest.main()
