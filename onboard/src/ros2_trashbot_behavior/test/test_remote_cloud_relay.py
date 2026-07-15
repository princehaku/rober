import importlib.util
import io
import json
import hashlib
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
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[4]
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
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ENV,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_EVIDENCE_BOUNDARY,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
    CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_EVIDENCE_BOUNDARY,
    CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_SCHEMA,
    CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
    CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
    CDN_TLS_EXTERNAL_EVIDENCE_ENV,
    CDN_TLS_EXTERNAL_EVIDENCE_EVIDENCE_BOUNDARY,
    CDN_TLS_EXTERNAL_EVIDENCE_SCHEMA,
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
    build_cloud_production_cutover_readiness_packet_payload,
    cloud_deployment_readiness_artifact_summary,
    cloud_db_queue_config_artifact_summary,
    cloud_db_queue_external_probe_bundle_summary,
    cloud_external_probe_bundle_summary,
    cloud_public_ingress_tls_artifact_summary,
    cdn_tls_external_evidence_artifact_summary,
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
    create_cloud_production_cutover_readiness_packet_artifact,
    external_evidence_intake_artifact_summary,
    cloud_worker_migration_rehearsal_artifact_summary,
    cloud_worker_cutover_drain_artifact_summary,
    cloud_external_evidence_review_decision_artifact_summary,
    cloud_production_cutover_readiness_packet_summary,
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


def _load_cloud_external_evidence_review_decision_tool():
    # pc-tools 目录名不能直接 import；测试按绝对路径加载，避免改包结构。
    tool_path = WORKSPACE_ROOT / "pc-tools" / "evidence" / "cloud_external_evidence_review_decision.py"
    spec = importlib.util.spec_from_file_location("cloud_external_evidence_review_decision_tool", tool_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        self.assertTrue(body["archive_task_query_filters_ready_not_production_proof"])
        self.assertEqual(
            body["archive_task_query_filters_proof_scope"],
            "software_proof_o6_archive_task_query_filters_only",
        )
        self.assertEqual(body["applied_filters"]["status"], "all")
        self.assertEqual(body["filter_semantics"], "and")
        self.assertEqual(body["filtered_result_count"], 0)
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

    def test_o6_cloud_archive_tasks_list_filters_robot_task_date_status_and_limit(self):
        def create_task(task_id, robot_id, started_at_ms, finished_at_ms, *, failure=False):
            payload = self._o6_archive_task_payload(
                task_id=task_id,
                robot_id=robot_id,
                finished_at=finished_at_ms,
            )
            payload["started_at_ms"] = started_at_ms
            if failure:
                payload["events"] = [
                    {
                        "event_id": f"evt-{task_id}",
                        "event_type": "task.failure",
                        "occurred_at_ms": finished_at_ms,
                        "summary": "local mock failure marker",
                        "severity": "error",
                        "evidence_refs": [f"events/{task_id}.json"],
                    }
                ]
            status, _ = self.client.request("POST", "/api/o6/archive/tasks", payload)
            self.assertEqual(status, 201)

        create_task("task-archive-filter-a", "trashbot-alpha", 86400000, 86401000)
        create_task("task-archive-filter-b", "trashbot-beta", 172800000, 172801000)
        create_task("task-archive-filter-c", "trashbot-alpha", 172800000, 172801000, failure=True)
        create_task("task-archive-filter-d", "trashbot-alpha", 172800000, 172802000)

        status, by_robot_limited = self.client.request(
            "GET",
            "/api/o6/archive/tasks?robot_id=trashbot-alpha&limit=1",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertTrue(by_robot_limited["archive_task_query_filters_ready_not_production_proof"])
        self.assertEqual(by_robot_limited["filter_semantics"], "and")
        self.assertEqual(by_robot_limited["filtered_result_count"], 3)
        self.assertEqual(by_robot_limited["task_list"]["total_tasks"], 1)
        self.assertEqual(by_robot_limited["applied_filters"]["robot_id"], "trashbot-alpha")
        self.assertEqual(by_robot_limited["applied_filters"]["limit"], 1)
        for key in (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "connects_cloud_production",
            "robot_control_executed",
        ):
            self.assertFalse(by_robot_limited[key])

        status, by_task = self.client.request(
            "GET",
            "/api/o6/archive/tasks?task_id=task-archive-filter-b",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(by_task["filtered_result_count"], 1)
        self.assertEqual(by_task["task_list"]["tasks"][0]["task_id"], "task-archive-filter-b")
        self.assertEqual(by_task["task_list"]["tasks"][0]["robot_id"], "trashbot-beta")

        status, by_date = self.client.request(
            "GET",
            "/api/o6/archive/tasks?date=1970-01-03",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(by_date["filtered_result_count"], 3)
        self.assertEqual(by_date["date_filter_source"], "started_at_ms")

        status, combined = self.client.request(
            "GET",
            "/api/o6/archive/tasks?robot_id=trashbot-alpha&date=1970-01-03&status=completed_mock&limit=2",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(combined["filtered_result_count"], 1)
        self.assertEqual(combined["task_list"]["tasks"][0]["task_id"], "task-archive-filter-d")
        self.assertEqual(
            combined["applied_filters"],
            {
                "robot_id": "trashbot-alpha",
                "task_id": "",
                "date": "1970-01-03",
                "status": "completed_mock",
                "limit": 2,
            },
        )

        status, failed = self.client.request(
            "GET",
            "/api/o6/archive/tasks?status=failed_mock",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(failed["filtered_result_count"], 1)
        self.assertEqual(failed["task_list"]["tasks"][0]["task_id"], "task-archive-filter-c")

        status, unknown = self.client.request(
            "GET",
            "/api/o6/archive/tasks?robot_id=trashbot-missing",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(unknown["filtered_result_count"], 0)
        self.assertEqual(unknown["task_list"]["tasks"], [])
        self.assertEqual(unknown["blocked_reasons"], ["archive_task_query_filter_no_matches"])

        matches, source = relay_module._o6_cloud_archive_task_date_match_source(
            {"finished_at_ms": 172800000},
            "1970-01-03",
        )
        self.assertTrue(matches)
        self.assertEqual(source, "finished_at_ms")

    def test_o6_cloud_archive_tasks_list_query_filters_fail_closed_without_store_mutation(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-archive-query-filter-safe"),
        )
        self.assertEqual(status, 201)

        invalid_paths = [
            "/api/o6/archive/tasks?unknown=1",
            "/api/o6/archive/tasks?date=2026-02-30",
            f"/api/o6/archive/tasks?robot_id={'a' * 129}",
            "/api/o6/archive/tasks?robot_id=/tmp/archive.json",
            "/api/o6/archive/tasks?robot_id=https%3A%2F%2Fexample.test%2Ftasks%3Ftoken%3Dsecret",
            "/api/o6/archive/tasks?task_id=QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0MTIzNDU2Nzg5MA",
            "/api/o6/archive/tasks?robot_id=trashbot-001&robot_id=trashbot-002",
            "/api/o6/archive/tasks?limit=1&limit=2",
            "/api/o6/archive/tasks?status=completed_mock&status=failed_mock",
            "/api/o6/archive/tasks?status=invalid",
        ]
        for path in invalid_paths:
            status, body = self.client.request("GET", path, token="")
            self.assertEqual(status, 400, path)
            self.assertEqual(body["error"]["code"], "bad_request")
            self.assertIn("invalid_archive_task_query_filter", body["error"]["message"])
            encoded = json.dumps(body, ensure_ascii=False).lower()
            self.assertNotIn("secret", encoded)
            self.assertNotIn("/tmp/archive.json", encoded)
            self.assertNotIn("qujdrev", encoded)

        status, listing = self.client.request("GET", "/api/o6/archive/tasks", token="")
        self.assertEqual(status, 200)
        self.assertEqual(listing["filtered_result_count"], 1)
        self.assertEqual(listing["task_list"]["tasks"][0]["task_id"], "task-o6-archive-query-filter-safe")

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

        real_claim_payload = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-real-claim",
            "started_at_ms": 1000,
            "finished_at_ms": 2000,
            "trajectory_frames": [],
            "events": [],
            "evidence_refs": [],
            "delivery_success": True,
        }
        status, body = self.client.request("POST", "/api/o6/archive/tasks", real_claim_payload)
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

    def _field_evidence_manifest_payload(self):
        # 这个 fixture 模拟 field_route_evidence_manifest.py 输出，只包含 artifact 摘要，不读真实文件。
        return {
            "schema": relay_module.FIELD_EVIDENCE_MANIFEST_SCHEMA,
            "run_id": "field-run-001",
            "generated_at": "2026-07-09T00:00:00+00:00",
            "source": "local_fixture",
            "mode": "local",
            "artifact_root": "/tmp/field_evidence",
            "preflight_json": "/tmp/field_preflight.json",
            "preflight_status": "ready_for_live_route_capture_not_proven",
            "preflight": {
                "status": "ready_for_live_route_capture_not_proven",
                "dry_run": False,
                "blocked_reason": None,
                "read_ok": True,
            },
            "gate_pass": True,
            "artifact_status": "gated",
            "artifact_health": {
                "status": "gated",
                "required_count": 4,
                "present_count": 4,
                "missing_count": 0,
                "blocked_count": 0,
                "summary": "all_required_artifacts_present",
            },
            "input_manifest": {
                "present": False,
                "status": "not_found",
                "dangerous_true_fields": [],
                "safe_for_reuse": True,
            },
            "source_manifest": {
                "present": True,
                "status": "source_manifest",
                "schema": "trashbot.vision_samples.v1",
                "sample_count": 2,
                "blocked_reason": None,
            },
            "manifest_gate": {
                "schema": relay_module.FIELD_EVIDENCE_MANIFEST_SCHEMA,
                "status": "gated",
                "gate_pass": True,
                "blocked_reason": None,
                "source": "local_fixture",
            },
            "route_root_seed_gate": {
                "schema": "trashbot.algorithm.route_root_seed_gate.v1",
                "status": "route_root_seed_ready_without_route_bag",
                "gate_pass": True,
                "route_bag_required": False,
                "route_bag_present": False,
                "blocked_reasons": ["route_bag_missing_optional"],
                "next_required_evidence": ["route_bag_optional_evidence"],
            },
            "status": "field_evidence_manifest_ready_not_delivery_proof",
            "blocked_reason": None,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "field_motion_evidence_packet": self._field_motion_evidence_packet_payload(),
            "delivery_result_evidence": self._delivery_result_evidence_payload(),
            "nav2_goal_execution_evidence": self._nav2_goal_execution_evidence_payload(),
            "route_bag_evidence": self._route_bag_evidence_payload(),
            "route_bag_payload_replay": self._route_bag_payload_replay_payload(),
            "route_bag_semantic_replay": self._route_bag_semantic_replay_payload(),
            "route_bag_full_semantic_decode_matrix": self._route_bag_full_semantic_decode_matrix_payload(),
            "route_bag_pose_progress_replay": self._route_bag_pose_progress_replay_payload(),
            "same_task_mission_evidence_gate": self._same_task_mission_evidence_gate_payload(
                "field-evidence-field-run-001"
            ),
            "derived_replay": {
                "generated": True,
                "frame_count": 2,
                "output": "/tmp/field_evidence/fixed_route_replay.jsonl",
                "source_route_csv": "/tmp/field_evidence/route.csv",
                "blocked_reason": None,
            },
            "artifacts": {
                "route_csv": {
                    "required": True,
                    "present": True,
                    "path": "/tmp/field_evidence/route.csv",
                    "size_bytes": 128,
                    "mtime_utc": "2026-07-09T00:00:01+00:00",
                    "sha256": "a" * 64,
                    "reason": None,
                },
                "replay_jsonl": {
                    "required": True,
                    "present": True,
                    "path": "/tmp/field_evidence/fixed_route_replay.jsonl",
                    "size_bytes": 256,
                    "mtime_utc": "2026-07-09T00:00:02+00:00",
                    "sha256": "b" * 64,
                    "reason": None,
                },
                "keyframes": {
                    "required": True,
                    "present": True,
                    "path": "/tmp/field_evidence/keyframes",
                    "size_bytes": 512,
                    "mtime_utc": "2026-07-09T00:00:03+00:00",
                    "sha256": "c" * 64,
                    "reason": None,
                    "file_count": 2,
                },
                "source_manifest": {
                    "required": True,
                    "present": True,
                    "path": "/tmp/field_evidence/manifest.json",
                    "size_bytes": 64,
                    "mtime_utc": "2026-07-09T00:00:04+00:00",
                    "sha256": "d" * 64,
                    "reason": None,
                },
            },
        }

    def _field_motion_evidence_packet_payload(self):
        # motion packet 只提供 O6/O7 需要的保守摘要，不带任何真实控制或原始路径回显。
        return {
            "schema": relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA,
            "proof_scope": relay_module.O6_FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE,
            "status": "field_motion_packet_ready_not_delivery_proof",
            "route_summary": {
                "frame_count": 17,
                "nonzero_displacement_observed": True,
                "displacement_m": 4.25,
            },
            "motion_log_summary": {
                "live_motion_evidence_present": True,
                "evidence_sources": [
                    "remote_capture_motion_log",
                    "/tmp/should-not-echo-motion.log",
                ],
            },
            "route_bag_or_live_nav2_log": {
                "present": True,
                "source": "derived_replay_jsonl",
                "route_bag_present": False,
                "live_motion_log_present": True,
                "path": "/tmp/should-not-echo-nav2.log",
                "root": "/tmp/should-not-echo-root",
            },
            "route_bag_pose_progress_replay": self._route_bag_pose_progress_replay_payload(),
            "blocked_reasons": ["route_bag_missing_optional"],
            "next_required_evidence": ["route_bag_optional_evidence"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _nav2_goal_execution_evidence_payload(self):
        # Nav2 goal evidence 只模拟 O11 proof 的白名单摘要，不携带日志路径、root 或原始 action payload。
        return {
            "schema": relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
            "proof_scope": relay_module.O6_NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
            "status": "nav2_goal_execution_ready_not_delivery_proof",
            "proof_status": "software_proof",
            "source": "o11_nav2_goal_execution_proof",
            "goal_requested": True,
            "goal_sent": True,
            "goal_accepted": True,
            "result_received": True,
            "goal_result_status": "STATUS_SUCCEEDED",
            "result_status_code": 4,
            "nav2_goal_execution_proven": True,
            "base_motion_command_nonzero_proven": True,
            "base_command_mode": "T1",
            "requested_base_command_mode": "T1",
            "pose_progress_summary": {
                "pose_sample_count": 6,
                "distance_m": 0.42,
                "progress_observed": True,
            },
            "base_feedback_summary": {
                "feedback_sample_count": 5,
                "nonzero_feedback_seen": True,
            },
            "base_command_summary": {
                "command_sample_count": 4,
                "nonzero_command_seen": True,
            },
            "blocked_reasons": ["delivery_record_missing"],
            "next_required_evidence": ["real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _delivery_result_evidence_payload(self):
        # delivery result 只提供安全裁剪后的 operator/dropoff 摘要，不允许任何真实送达成功宣称外溢。
        return {
            "schema": relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA,
            "proof_scope": relay_module.O6_DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
            "status": "delivery_result_evidence_ready_not_delivery_proof",
            "source": "field_delivery_result_record",
            "source_schema": "trashbot.delivery_result_record.v1",
            "record_present": True,
            "record_read_ok": True,
            "record_status": "operator_confirmed_not_production_accepted",
            "delivery_result_claimed": True,
            "operator_confirmation_present": True,
            "dropoff_confirmation_type": "operator_button_confirmed",
            "completed_at_utc": "2026-07-09T08:15:00Z",
            "linked_nav2_goal_execution_proven": True,
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": ["real_delivery_record_or_operator_video"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _route_execution_result_delivery_readiness_payload(self, task_id="field-evidence-field-run-001"):
        # 结果链 readiness 只表达“同一 task 的结果摘要已可读回”，不表达真实 route execution 或 delivery success。
        return {
            "schema": relay_module.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
            "source_schema": relay_module.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
            "status": "route_execution_result_delivery_readiness_ready_not_delivery_proof",
            "source": "algorithm_route_execution_result_delivery_readiness_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "route_execution_result_status": "nav2_result_summary_ready",
            "route_execution_result_source": "nav2_goal_execution_evidence",
            "route_execution_result_ready": True,
            "route_execution_success": False,
            "delivery_result_readiness_status": "delivery_result_summary_ready",
            "delivery_result_readiness_source": "delivery_result_evidence",
            "delivery_result_readiness_ready": True,
            "operator_confirmation_readiness_status": "operator_confirmation_summary_ready",
            "operator_confirmation_readiness_source": "delivery_result_evidence",
            "operator_confirmation_readiness_ready": True,
            "linked_nav2_goal_execution_proven": True,
            "linked_delivery_result_claimed": True,
            "linked_operator_confirmation_present": True,
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": ["real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _route_delivery_closure_packet_payload(self, task_id="field-evidence-field-run-001"):
        # closure packet 只表达软件证据闭合，不表达真实 delivery success 或已执行控制。
        return {
            "schema": relay_module.ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
            "source_schema": relay_module.ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
            "status": "route_delivery_closure_ready_not_success_proof",
            "source": "algorithm_route_delivery_closure_packet_summary",
            "task_id": task_id,
            "linked_route_execution_result_delivery_readiness_ready": True,
            "linked_nav2_goal_execution_ready": True,
            "linked_delivery_result_ready": True,
            "linked_operator_confirmation_ready": True,
            "linked_pose_progress_ready": True,
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": ["real_delivery_result_trace", "real_pose_progress_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _same_task_mission_evidence_gate_payload(self, task_id="field-evidence-field-run-001"):
        # same-task gate 只证明同一 task 的多段摘要互相对齐，不证明真实送达成功。
        return {
            "schema": relay_module.SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
            "source_schema": relay_module.SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
            "proof_scope": relay_module.O6_SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE,
            "status": "same_task_mission_gate_ready_not_success_proof",
            "source": "algorithm_same_task_mission_evidence_gate_summary",
            "task_id": task_id,
            "terminal_refs": [
                "captures/cloud_terminal_result.json",
                "captures/route_execution_summary.json",
            ],
            "mission_artifact_delta": {
                "same_task_id_consumed": True,
                "cloud_terminal_result_source_consumed": True,
                "route_execution_readiness_consumed": True,
                "route_delivery_closure_consumed": True,
                "nonzero_pose_progress_consumed": True,
                "live_or_field_command_executed": False,
                "support_only_reason": "support_only_same_task_readback_without_live_command",
                "okr_credit_allowed": False,
            },
            "linked_readiness_flags": {
                "delivery_result_evidence_ready": True,
                "cloud_terminal_result_ready": True,
                "route_execution_result_delivery_readiness_ready": True,
                "route_delivery_closure_packet_ready": True,
                "route_bag_pose_progress_replay_ready": True,
                "same_task_id_match": True,
            },
            "linked_delivery_result_evidence_ready": True,
            "linked_cloud_terminal_result_ready": True,
            "linked_route_execution_result_delivery_readiness_ready": True,
            "linked_route_delivery_closure_packet_ready": True,
            "linked_route_bag_pose_progress_replay_ready": True,
            "same_task_id_match": True,
            "same_task_id_consumed": True,
            "live_or_field_command_executed": False,
            "support_only_reason": "support_only_same_task_readback_without_live_command",
            "okr_credit_allowed": False,
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": ["production_cloud_task_trace", "real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _same_task_field_material_packet_payload(self, task_id="field-evidence-field-run-001"):
        # same-task field material packet 这里按 Algorithm 实际 shape 提供：顶层 sample_refs=list，细节在 material_summaries。
        return {
            "schema": relay_module.SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
            "source_schema": relay_module.SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
            "proof_scope": relay_module.O6_SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE,
            "status": "ready_not_delivery_proof",
            "source": "algorithm_same_task_field_material_packet_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "present_materials": ["route_csv", "keyframes", "route_bag_or_rosbag", "replay_jsonl"],
            "missing_materials": ["map_yaml"],
            "map_yaml_present": False,
            "route_csv_present": True,
            "keyframes_present": True,
            "route_bag_or_rosbag_present": True,
            "replay_jsonl_present": True,
            "counts": {
                "present_material_count": 4,
                "missing_material_count": 1,
                "map_yaml_count": 0,
                "route_csv_count": 1,
                "keyframe_count": 17,
                "route_bag_or_rosbag_count": 1,
                "replay_jsonl_count": 1,
            },
            "sample_refs": [
                "captures/route.csv",
                "captures/keyframes/keyframe-0001.jpg",
                "captures/route_001.db3",
                "captures/fixed_route_replay.jsonl",
            ],
            "material_summaries": {
                "map_yaml": {
                    "present": False,
                    "count": 0,
                    "sample_refs": [],
                },
                "route_csv": {
                    "present": True,
                    "basename": "route.csv",
                    "size_bytes": 128,
                    "sha256_prefix": "1234567890abcdef",
                    "count": 1,
                    "sample_refs": ["captures/route.csv"],
                },
                "keyframes": {
                    "present": True,
                    "basename": "keyframe-0001.jpg",
                    "size_bytes": 2048,
                    "sha256_prefix": "abcdef1234567890",
                    "count": 17,
                    "sample_refs": ["captures/keyframes/keyframe-0001.jpg"],
                },
                "route_bag_or_rosbag": {
                    "present": True,
                    "basename": "route_001.db3",
                    "size_bytes": 4096,
                    "sha256_prefix": "1122334455667788",
                    "count": 1,
                    "sample_refs": ["captures/route_001.db3"],
                },
                "replay_jsonl": {
                    "present": True,
                    "basename": "fixed_route_replay.jsonl",
                    "size_bytes": 512,
                    "sha256_prefix": "aabbccddeeff0011",
                    "count": 1,
                    "sample_refs": ["captures/fixed_route_replay.jsonl"],
                },
            },
            "same_task_id_consumed": True,
            "live_or_field_material_consumed": True,
            "blocked_reasons": [
                "same_task_field_material_map_yaml_missing_optional",
                "real_delivery_success_not_proven",
            ],
            "next_required_evidence": [
                "map_yaml_material_optional",
                "live_route_execution_trace",
                "real_delivery_result_trace",
            ],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _same_task_replay_packet_readback_payload(
        self,
        task_id="task_o3_28_pose_fixed_route_consumer_20260713_0402",
    ):
        # 05:02 accepted packet 这里只作为 readback 证据消费；所有控制、HIL、送达字段必须保持 false。
        return {
            "schema": relay_module.SAME_TASK_REPLAY_PACKET_SOURCE_SCHEMA,
            "source_schema": relay_module.SAME_TASK_REPLAY_PACKET_SOURCE_SCHEMA,
            "artifact_boundary": relay_module.O3_SAME_TASK_REPLAY_PACKET_PROOF_SCOPE,
            "status": "same_task_replay_packet_ready_not_route_execution_proof",
            "source": "algorithm_same_task_replay_packet_summary",
            "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
            "task_id": task_id,
            "route_intent_id": (
                "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
            ),
            "route_csv_row_count": 28,
            "replay_jsonl_event_count": 28,
            "path_structured_pose_count": 28,
            "same_task_identity_verified": True,
            "same_task_replay_packet_ready": True,
            "source_refs": {
                "source_summary_ref": (
                    "sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/"
                    "artifacts/algorithm/same_task_replay_packet_summary.json"
                ),
                "packet_jsonl_ref": (
                    "sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/"
                    "artifacts/algorithm/same_task_route_replay_packet.jsonl"
                ),
                "route_csv_ref": (
                    "sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/"
                    "artifacts/algorithm/fixed_route_28_pose_route.csv"
                ),
                "replay_jsonl_ref": (
                    "sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/"
                    "artifacts/algorithm/fixed_route_28_pose_replay.jsonl"
                ),
            },
            "source_fingerprints": {
                "summary": "9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93",
                "route_csv": "61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601",
                "replay_jsonl": "530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5",
            },
            "blocked_reasons": [],
            "next_required_evidence": [
                "controlled_route_execution_record_for_same_packet",
                "delivery_or_operator_acceptance_record",
                "current_live_hil_acceptance",
            ],
            "route_execution_success": False,
            "delivery_success": False,
            "hil_pass": False,
            "safe_to_control": False,
            "robot_control_executed": False,
            "primary_actions_enabled": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
            "connects_cloud_production": False,
        }

    def _bounded_route_execution_gate_material_payload(
        self,
        task_id="task_o3_28_pose_fixed_route_consumer_20260713_0402",
    ):
        # 07:07 gate 与 08:09 bounded plan 只作为 O6/O7 readback 摘要，不允许升级成控制能力。
        fixed_false_fields = {
            "safe_to_control": False,
            "delivery_success": False,
            "route_execution_success": False,
            "hil_pass": False,
            "robot_control_executed": False,
            "connects_cloud_production": False,
            "primary_actions_enabled": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
        }
        controlled_gate = {
            "schema": relay_module.CONTROLLED_ROUTE_EXECUTION_GATE_RECORD_SOURCE_SCHEMA,
            "proof_boundary": relay_module.O3_CONTROLLED_ROUTE_EXECUTION_GATE_RECORD_PROOF_SCOPE,
            "artifact_boundary": relay_module.O3_CONTROLLED_ROUTE_EXECUTION_GATE_RECORD_PROOF_SCOPE,
            "controlled_route_execution_gate_status": "fail_closed_input_packet_validated",
            "packet_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_PACKET_ID,
            "task_id": task_id,
            "route_intent_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_ROUTE_INTENT_ID,
            "route_csv_row_count": 28,
            "replay_jsonl_event_count": 28,
            "path_structured_pose_count": 28,
            "same_task_identity_verified": True,
            "same_task_replay_packet_ready": True,
            "no_motion_control_guard": [
                "no /cmd_vel",
                "no /api/base/manual",
                "no NavigateToPose",
                "no WAVE ROVER UART",
            ],
            "rejected_claims": [
                "route_execution_success",
                "delivery_success",
                "hil_pass",
                "safe_to_control",
                "robot_control_executed",
                "NavigateToPose",
                "/cmd_vel",
                "/api/base/manual",
                "WAVE ROVER UART",
            ],
            "fixed_false_fields": fixed_false_fields,
            **fixed_false_fields,
        }
        bounded_plan = {
            "schema": relay_module.BOUNDED_ROUTE_COMMAND_PLAN_SOURCE_SCHEMA,
            "proof_boundary": relay_module.O3_BOUNDED_ROUTE_COMMAND_PLAN_PROOF_SCOPE,
            "artifact_boundary": relay_module.O3_BOUNDED_ROUTE_COMMAND_PLAN_PROOF_SCOPE,
            "bounded_route_command_plan_status": "bounded_plan_ready_not_control_proof",
            "execution_plan_status": "blocked_pending_live_safety_gate",
            "packet_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_PACKET_ID,
            "task_id": task_id,
            "route_intent_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_ROUTE_INTENT_ID,
            "route_csv_row_count": 28,
            "path_structured_pose_count": 28,
            "segment_count": 27,
            "global_abort_criteria": [f"abort_{index:02d}" for index in range(11)],
            "bounded_segment_plan": [
                {"segment_index": index, "abort_check_ids": ["operator_stop_requested"]}
                for index in range(27)
            ],
            "next_live_command_gate": {
                "status": "blocked_until_new_controlled_live_execution_sprint",
                "forbidden_in_this_artifact": [
                    "no /cmd_vel",
                    "no /api/base/manual",
                    "no NavigateToPose",
                    "no WAVE ROVER UART",
                ],
            },
            "fixed_false_fields": fixed_false_fields,
            **fixed_false_fields,
        }
        return {
            "schema": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_MATERIAL_PROOF_SCOPE,
            "evidence_boundary": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_MATERIAL_PROOF_SCOPE,
            "status": "bounded_route_execution_gate_material_ready_not_route_execution_proof",
            "source": "algorithm_controlled_route_execution_gate_and_bounded_plan",
            "task_id": task_id,
            "controlled_route_execution_gate_record": controlled_gate,
            "bounded_route_command_plan": bounded_plan,
            "blocked_reasons": ["route_execution_not_run"],
            "next_required_evidence": [
                "explicit_live_safety_operator_gate",
                "current_live_hil_acceptance",
                "same_window_nav2_controller_result",
                "delivery_operator_acceptance_evidence",
            ],
            **fixed_false_fields,
        }

    def _bounded_route_terminal_result_material_payload(
        self,
        task_id="task_o3_28_pose_fixed_route_consumer_20260713_0402",
    ):
        # 00:24 O5 bridge 是本轮 O6 的唯一来源；这里固定身份和 false fields，防止误升格为 delivery。
        fixed_false_fields = {
            key: False for key in sorted(relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_FALSE_KEYS)
        }
        return {
            "schema": relay_module.O5_BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA,
            "proof_boundary": relay_module.O5_BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_SCOPE,
            "source": "o5_bounded_route_terminal_result_bridge",
            "safe_evidence_ref": "o5_bounded_route_terminal_result_bridge_summary.json",
            "task_id": task_id,
            "packet_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_PACKET_ID,
            "route_intent_id": relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_ROUTE_INTENT_ID,
            "route_csv_row_count": 28,
            "path_structured_pose_count": 28,
            "segment_count": 27,
            "result_code": relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_CODE,
            "terminal_result_state": relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_STATE,
            "reconciliation_state": relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_STATE,
            "source_identity_verified": True,
            "source_counts_verified": True,
            "source_fixed_false_fields_verified": True,
            "fixed_false_fields": fixed_false_fields,
            **fixed_false_fields,
        }

    def _current_field_evidence_material_payload(self, task_id="field-evidence-field-run-001"):
        # current field evidence material 只保留当前上位机材料的安全摘要，不回显 URL、路径或正文。
        return {
            "schema": relay_module.CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA,
            "source_schema": relay_module.CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_CURRENT_FIELD_EVIDENCE_MATERIAL_PROOF_SCOPE,
            "status": "current_field_evidence_material_ready_not_route_execution_proof",
            "source": "current_field_evidence_smoke_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "present_materials": [
                "camera_frame",
                "radar_scan",
                "nav2_no_motion_path",
                "manual_gate",
            ],
            "missing_materials": ["map_material"],
            "camera_frame_observed": True,
            "radar_scan_observed": True,
            "map_material_observed": False,
            "nav2_no_motion_path_generated": True,
            "manual_gate_blocked_expected": True,
            "live_or_field_material_consumed": True,
            "current_field_evidence_ready_not_route_execution_proof": True,
            "blocked_reasons": ["real_route_execution_trace_missing"],
            "next_required_evidence": ["live_route_execution_trace", "operator_confirmation_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "hil_pass": False,
            "connects_cloud_production": False,
            "real_cloud_db_connected": False,
            "real_oss_connected": False,
        }

    def _field_operator_confirmation_material_payload(self, task_id="field-evidence-field-run-001"):
        # operator material 只提供人工报告/确认的安全摘要，不把原始备注、路径或真实送达成功写入 O6。
        return {
            "schema": relay_module.FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA,
            "source_schema": relay_module.FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE,
            "status": "field_operator_confirmation_material_ready_not_delivery_proof",
            "source": "operator_confirmation_material_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "operator_report_present": True,
            "operator_report_status": "operator_report_ready",
            "operator_confirmation_present": True,
            "operator_confirmation_status": "operator_confirmation_ready",
            "operator_present": True,
            "physical_clearance_confirmed": True,
            "emergency_stop_ready": True,
            "observed_motion": True,
            "observed_stop": True,
            "reported_at": "2026-07-10T07:22:00Z",
            "same_task_id_consumed": True,
            "linked_route_material_present": True,
            "linked_delivery_material_present": True,
            "operator_material_consumed": True,
            "support_only_reason": "operator_material_not_delivery_success_proof",
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": [
                "real_live_nav2_route_execution_trace",
                "real_delivery_result_trace",
            ],
            "material_summaries": {
                "operator_report": {
                    "present": True,
                    "status": "operator_report_ready",
                    "basename": "operator_report.json",
                    "size_bytes": 320,
                    "sha256_prefix": "aa11bb22cc33dd44",
                    "count": 1,
                    "sample_refs": ["captures/operator_report.json"],
                },
                "operator_confirmation": {
                    "present": True,
                    "status": "operator_confirmation_ready",
                    "basename": "operator_confirmation.json",
                    "size_bytes": 240,
                    "sha256_prefix": "bb22cc33dd44ee55",
                    "count": 1,
                    "sample_refs": ["captures/operator_confirmation.json"],
                },
                "route_material": {
                    "present": True,
                    "status": "route_material_ready",
                    "basename": "route_execution_readiness.json",
                    "size_bytes": 384,
                    "sha256_prefix": "cc33dd44ee55ff66",
                    "count": 1,
                    "sample_refs": ["captures/route_execution_readiness.json"],
                },
                "delivery_material": {
                    "present": True,
                    "status": "delivery_material_ready",
                    "basename": "delivery_result_evidence.json",
                    "size_bytes": 288,
                    "sha256_prefix": "dd44ee55ff667788",
                    "count": 1,
                    "sample_refs": ["captures/delivery_result_evidence.json"],
                },
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
            "connects_cloud_production": False,
            "real_cloud_db_connected": False,
            "real_oss_connected": False,
        }

    def _clean_baseline_nav2_path_material_payload(self, task_id="field-evidence-field-run-001"):
        # clean-baseline Nav2 path material 只表达 no-motion 规划材料，不证明真实 route execution 或控制成功。
        return {
            "schema": relay_module.CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA,
            "source_schema": relay_module.CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_PROOF_SCOPE,
            "status": "clean_baseline_nav2_path_material_ready_not_route_execution_proof",
            "source": "clean_baseline_nav2_refresh_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "first_attempt_status": "tf_root_cause_blocked",
            "retry_status": "path_generated_after_retry",
            "path_generation_succeeded": True,
            "path_generated": True,
            "path_point_count": 31,
            "planner_server_active": True,
            "managed_runtime_started": True,
            "managed_runtime_cleanup_ok": True,
            "initialpose_published": True,
            "amcl_pose_observed": True,
            "map_server_active": True,
            "amcl_active": True,
            "cleanup_readback_clean": True,
            "material_sample_refs": {
                "refresh_summary": {
                    "present": True,
                    "basename": "clean_baseline_nav2_refresh_summary.json",
                    "size_bytes": 420,
                    "sha256_prefix": "9988776655443322",
                    "count": 1,
                    "sample_refs": ["captures/clean_baseline_nav2_refresh_summary.json"],
                },
                "latest_readback": {
                    "present": True,
                    "basename": "clean_baseline_nav2_latest.json",
                    "size_bytes": 256,
                    "sha256_prefix": "1122aabb3344ccdd",
                    "count": 1,
                    "sample_refs": ["captures/clean_baseline_nav2_latest.json"],
                },
                "status_artifact": {
                    "present": True,
                    "basename": "clean_baseline_nav2_status.json",
                    "size_bytes": 196,
                    "sha256_prefix": "a1b2c3d4e5f60123",
                    "count": 1,
                    "sample_refs": ["captures/clean_baseline_nav2_status.json"],
                },
            },
            "blocked_reasons": ["real_route_execution_trace_missing"],
            "next_required_evidence": ["live_route_execution_trace", "operator_confirmation_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
            "connects_cloud_production": False,
            "real_cloud_db_connected": False,
            "real_oss_connected": False,
        }

    def _pc_live_nav2_execution_material_payload(self, task_id="field-evidence-field-run-001"):
        # 这份 canonical material 只证明 PC live Nav2/bridge 摘要可回读，不证明 wheel L/R 非零、路线执行成功或送达成功。
        return {
            "schema": relay_module.PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA,
            "source_schema": relay_module.PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_PROOF_SCOPE,
            "status": "pc_live_nav2_execution_material_ready_not_delivery_proof",
            "source": "algorithm_pc_live_nav2_execution_material_summary",
            "source_sprint": "2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "goal_accepted": True,
            "cancel_accepted": True,
            "goal_result_status": "goal_timeout_cancel_requested",
            "uses_base_uart": True,
            "base_command_nonzero_observed": True,
            "base_command_nonzero_count": 733,
            "base_feedback_sample_count": 5941,
            "base_feedback_lr_nonzero_proven": False,
            "base_feedback_imu_attitude_delta_observed": True,
            "blocked_reasons": [
                "same_window_wheel_lr_nonzero_feedback_missing",
                "real_route_execution_success_not_proven",
            ],
            "next_required_evidence": [
                "same_window_wheel_lr_nonzero_feedback",
                "real_live_nav2_route_execution_trace",
            ],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
        }

    def _pc_live_nav2_execution_material_legacy_payload(self, task_id="artifact-bundle-task-001"):
        # 这份 legacy material 模拟 Algorithm 返工前字段，验证 O6 对 nav2_goal_accepted/nav2_terminal_status 兼容读取。
        return {
            "schema": relay_module.PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA,
            "source_schema": relay_module.PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_PROOF_SCOPE,
            "status": "pc_live_nav2_execution_material_ready_not_delivery_proof",
            "source": "algorithm_pc_live_nav2_execution_material_summary",
            "source_sprint": "2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "nav2_goal_accepted": True,
            "cancel_accepted": True,
            "nav2_terminal_status": "goal_timeout_cancel_requested",
            "uses_base_uart": True,
            "base_command_nonzero_observed": True,
            "base_command_nonzero_count": 733,
            "base_feedback_sample_count": 5941,
            "base_feedback_lr_nonzero_proven": False,
            "base_feedback_imu_attitude_delta_observed": True,
            "blocked_reasons": [
                "same_window_wheel_lr_nonzero_feedback_missing",
                "real_route_execution_success_not_proven",
            ],
            "next_required_evidence": [
                "same_window_wheel_lr_nonzero_feedback",
                "real_live_nav2_route_execution_trace",
            ],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
        }

    def _localization_path_material_readback_payload(self, task_id="field-evidence-field-run-001"):
        # localization/path readback 只表达同 run localization 已观测、path 仍失败，cross-run comparator 不能覆盖 same-run false 结论。
        return {
            "schema": relay_module.LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA,
            "source_schema": relay_module.LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA,
            "proof_scope": relay_module.O6_LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE,
            "status": "localization_path_material_readback_ready_not_route_execution_proof",
            "source": "o1_localization_path_material_bridge_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "localization_path_material_bridge_present": True,
            "same_run_localization_material_present": True,
            "same_run_map_once_observed": True,
            "same_run_amcl_pose_observed": True,
            "same_run_localization_tf_map_to_odom": True,
            "same_run_localization_tf_map_to_base_link": True,
            "same_run_path_generation_requested": True,
            "same_run_path_generation_succeeded": False,
            "same_run_path_generated": False,
            "same_run_path_point_count": 0,
            "same_run_path_proven": False,
            "cross_run_clean_baseline_path_comparator_present": False,
            "cross_run_clean_baseline_path_summary": {},
            "cross_run_clean_baseline_same_run_override_allowed": False,
            "cross_run_clean_baseline_path_comparator_blocked_reasons": [],
            "blocked_reasons": ["current_same_run_path_generation_failed"],
            "next_required_evidence": [
                "current_same_run_feedback_t1001_log",
                "current_same_run_nav2_path_generation_trace",
            ],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "nav2_route_execution_success": False,
            "hil_pass": False,
            "connects_cloud_production": False,
        }

    def _same_task_route_execution_material_packet_payload(self, task_id="field-evidence-field-run-001"):
        # route execution material packet 只证明同一 task 的执行材料摘要已消费，不证明真实送达或控制安全。
        return {
            "schema": relay_module.SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
            "source_schema": relay_module.SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
            "proof_scope": relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE,
            "evidence_boundary": relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE,
            "status": "route_execution_material_ready_not_delivery_proof",
            "source": "algorithm_same_task_route_execution_material_packet_summary",
            "task_id": task_id,
            "task_id_source": "manifest_task_id",
            "same_task_id_consumed": True,
            "route_execution_material_consumed": True,
            "live_or_field_command_evidence_present": True,
            "delivery_or_operator_material_consumed": True,
            "route_execution_credit_candidate": True,
            "credit_support_only_reason": None,
            "credit_required_evidence": [
                "real_live_nav2_route_execution_trace",
                "real_delivery_result_trace",
                "operator_confirmation_trace",
            ],
            "same_task_field_material_packet_status": "ready_not_delivery_proof",
            "source_sections": [
                "same_task_field_material_packet",
                "route_execution_result_delivery_readiness",
                "route_bag_pose_progress_replay",
                "route_delivery_closure_packet",
            ],
            "material_summaries": {
                "same_task_field_material_packet": {
                    "status": "ready_not_delivery_proof",
                    "present": True,
                    "basename": "same_task_field_material_packet.json",
                    "size_bytes": 256,
                    "sha256_prefix": "1234567890abcdef",
                    "count": 1,
                    "sample_refs": ["captures/same_task_field_material_packet.json"],
                },
                "route_execution_result_delivery_readiness": {
                    "status": "route_execution_result_delivery_readiness_ready_not_delivery_proof",
                    "present": True,
                    "basename": "route_execution_readiness.json",
                    "size_bytes": 384,
                    "sha256_prefix": "abcdef1234567890",
                    "count": 1,
                    "sample_refs": ["captures/route_execution_readiness.json"],
                },
                "route_bag_pose_progress_replay": {
                    "status": "ready_not_live_nav2_proof",
                    "present": True,
                    "basename": "route_bag_pose_progress_replay.json",
                    "size_bytes": 512,
                    "sha256_prefix": "1122334455667788",
                    "count": 1,
                    "sample_refs": ["captures/route_bag_pose_progress_replay.json"],
                },
                "route_delivery_closure_packet": {
                    "status": "route_delivery_closure_ready_not_success_proof",
                    "present": True,
                    "basename": "route_delivery_closure_packet.json",
                    "size_bytes": 128,
                    "sha256_prefix": "aabbccddeeff0011",
                    "count": 1,
                    "sample_refs": ["captures/route_delivery_closure_packet.json"],
                },
            },
            "blocked_reasons": ["real_delivery_success_not_proven"],
            "next_required_evidence": [
                "real_live_nav2_route_execution_trace",
                "real_delivery_result_trace",
                "operator_confirmation_trace",
            ],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
        }

    def _route_bag_evidence_payload(self):
        # route bag evidence 只证明 DB3 摘要已被 Algorithm 读取，不证明 live Nav2 run 或送达成功。
        return {
            "schema": relay_module.ROUTE_BAG_EVIDENCE_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
            "status": "ready_not_route_execution_proof",
            "source": "algorithm_route_bag_summary",
            "source_label": "board_live_full_stack_route_bag",
            "task_id": "route-bag-task-001",
            "task_id_source": "manifest_task_id",
            "metadata_present": True,
            "db3_present": True,
            "db3_read_ok": True,
            "db3_size_bytes": 4096,
            "db3_sha256_prefix": "0123456789abcdef",
            "topic_count": 3,
            "message_count": 42,
            "timestamp_first_ns": 1710000000000000000,
            "timestamp_last_ns": 1710000000123000000,
            "sample_topic_names": ["/tf", "/odom", "/scan"],
            "blocked_reasons": ["local_mock_only", "not_proven"],
            "next_required_evidence": ["live_nav2_pose_progress", "real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _route_bag_payload_replay_payload(self):
        # payload replay 只证明 DB3 消息摘要可回读，不证明真实路线执行或任何控制成功。
        return {
            "schema": relay_module.ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
            "status": "route_bag_payload_replay_ready_not_route_execution_proof",
            "source": "algorithm_route_bag_payload_replay_summary",
            "source_label": "board_live_full_stack_route_bag",
            "task_id": "route-bag-task-001",
            "task_id_source": "manifest_task_id",
            "metadata_present": True,
            "db3_present": True,
            "db3_read_ok": True,
            "db3_size_bytes": 4096,
            "db3_sha256_prefix": "0123456789abcdef",
            "topic_count": 3,
            "message_count": 42,
            "timestamp_first_ns": 1710000000000000000,
            "timestamp_last_ns": 1710000000123000000,
            "sample_topic_names": ["/tf", "/odom", "/scan"],
            "payload_sample_count": 3,
            "payload_size_min_bytes": 12,
            "payload_size_max_bytes": 128,
            "payload_size_avg_bytes": 64,
            "payload_sha256_prefix_samples": [
                "a1b2c3d4e5f6a7b8",
                "b1c2d3e4f5a6b7c8",
                "c1d2e3f4a5b6c7d8",
            ],
            "blocked_reasons": ["local_mock_only", "not_proven"],
            "next_required_evidence": ["live_nav2_pose_progress", "real_route_execution_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _route_bag_semantic_replay_payload(self):
        # semantic replay 只回显白名单语义摘要，不回显 raw payload/base64/path/token 或控制话题。
        return {
            "schema": relay_module.ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE,
            "status": "route_bag_semantic_replay_ready_not_route_execution_proof",
            "source": "algorithm_route_bag_semantic_replay_summary",
            "source_label": "board_live_full_stack_route_bag",
            "task_id": "route-bag-task-001",
            "task_id_source": "manifest_task_id",
            "metadata_present": True,
            "db3_present": True,
            "db3_read_ok": True,
            "db3_size_bytes": 4096,
            "db3_sha256_prefix": "0123456789abcdef",
            "topic_count": 4,
            "message_count": 48,
            "timestamp_first_ns": 1710000000000000000,
            "timestamp_last_ns": 1710000000187000000,
            "sample_topic_names": ["/scan", "/camera/image_raw", "/tf_static", "/odom"],
            "semantic_sample_count": 6,
            "semantic_decode_ok_count": 5,
            "semantic_decode_failed_count": 1,
            "semantic_topic_types": [
                "sensor_msgs.msg.LaserScan",
                "sensor_msgs.msg.Image",
                "tf2_msgs.msg.TFMessage",
                "nav_msgs.msg.Odometry",
            ],
            "laser_scan_summary": {
                "sample_count": 2,
                "range_sample_count": 1440,
                "finite_range_count": 1408,
                "range_min": 0.12,
                "range_max": 5.8,
                "angle_min": -1.57,
                "angle_max": 1.57,
                "angle_increment": 0.00436,
            },
            "image_summary": {
                "sample_count": 1,
                "width": 640,
                "height": 480,
                "encoding": "rgb8",
                "step": 1920,
                "data_size_bytes": 921600,
            },
            "tf_summary": {
                "sample_count": 2,
                "transform_count": 4,
                "frame_id_samples": ["map", "odom"],
                "child_frame_id_samples": ["base_link", "laser"],
            },
            "blocked_reasons": ["local_mock_only", "not_proven"],
            "next_required_evidence": ["live_nav2_pose_progress", "real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _route_bag_full_semantic_decode_matrix_payload(self):
        # full semantic decode matrix 只提供 per topic/type 覆盖摘要，不携带任何 ROS payload 原文。
        return {
            "schema": relay_module.ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
            "source_schema": relay_module.ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE,
            "status": "route_bag_full_semantic_decode_matrix_ready_not_route_execution_proof",
            "source": "algorithm_route_bag_full_semantic_decode_matrix_summary",
            "source_label": "board_live_full_stack_route_bag",
            "task_id": "route-bag-task-001",
            "task_id_source": "manifest_task_id",
            "topic_type_count": 5,
            "decoded_topic_type_count": 3,
            "unsupported_topic_type_count": 1,
            "failed_topic_type_count": 1,
            "decoded_message_sample_count": 14,
            "decode_failed_message_sample_count": 1,
            "unsupported_message_sample_count": 2,
            "coverage_ratio": 0.8,
            "topic_type_matrix": [
                {
                    "topic": "/scan",
                    "type": "sensor_msgs/msg/LaserScan",
                    "status": "decoded",
                    "decoder": "laser_scan_summary_decoder",
                    "message_sample_count": 6,
                    "decoded_message_sample_count": 6,
                    "unsupported_message_sample_count": 0,
                    "decode_failed_message_sample_count": 0,
                },
                {
                    "topic": "/camera/image_raw",
                    "type": "sensor_msgs/msg/Image",
                    "status": "unsupported",
                    "message_sample_count": 2,
                    "decoded_message_sample_count": 0,
                    "unsupported_message_sample_count": 2,
                    "decode_failed_message_sample_count": 0,
                    "blocked_reasons": ["decoder_missing_for_image_payload"],
                },
                {
                    "topic": "/odom",
                    "type": "nav_msgs/msg/Odometry",
                    "status": "decoded",
                    "decoder": "decode_odometry_payload",
                    "message_sample_count": 5,
                    "decoded_message_sample_count": 5,
                    "unsupported_message_sample_count": 0,
                    "decode_failed_message_sample_count": 0,
                },
                {
                    "topic": "/diagnostics",
                    "type": "diagnostic_msgs/msg/DiagnosticArray",
                    "status": "decoded",
                    "decoder_name": "decode_diagnostic_array_payload",
                    "message_sample_count": 3,
                    "decoded_message_sample_count": 3,
                    "unsupported_message_sample_count": 0,
                    "decode_failed_message_sample_count": 0,
                },
                {
                    "topic": "/tf_static",
                    "type": "tf2_msgs/msg/TFMessage",
                    "status": "failed",
                    "message_sample_count": 1,
                    "decoded_message_sample_count": 0,
                    "unsupported_message_sample_count": 0,
                    "decode_failed_message_sample_count": 1,
                    "blocked_reasons": ["sample_decode_failed"],
                },
            ],
            "blocked_reasons": ["local_mock_only", "not_proven"],
            "next_required_evidence": ["route_bag_decoder_coverage_for_unsupported_types"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "live_nav2_run_proven": False,
            "route_execution_success": False,
            "connects_cloud_production": False,
        }

    def _route_bag_pose_progress_replay_payload(self):
        # pose progress replay 只回显白名单位姿摘要，不回显原始 ROS payload、路径或控制字段。
        return {
            "schema": relay_module.ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
            "proof_scope": relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
            "status": "ready_not_live_nav2_proof",
            "source": "algorithm_route_bag_pose_progress_replay_summary",
            "source_label": "board_live_full_stack_route_bag",
            "task_id": "route-bag-task-001",
            "task_id_source": "manifest_task_id",
            "metadata_present": True,
            "db3_present": True,
            "db3_read_ok": True,
            "db3_size_bytes": 4096,
            "db3_sha256_prefix": "0123456789abcdef",
            "topic_count": 4,
            "message_count": 48,
            "timestamp_first_ns": 1710000000000000000,
            "timestamp_last_ns": 1710000000187000000,
            "sample_topic_names": ["/tf", "/odom", "/scan"],
            "pose_sample_count": 6,
            "pose_decode_ok_count": 5,
            "pose_decode_failed_count": 1,
            "pose_topic_types": [
                "tf2_msgs.msg.TFMessage",
                "nav_msgs.msg.Odometry",
            ],
            "pose_frame_pairs": [
                {"parent_frame": "map", "child_frame": "base_link"},
                {"parent_frame": "odom", "child_frame": "base_link"},
            ],
            "pose_time_span_ns": {
                "start_ns": 1710000000000000000,
                "end_ns": 1710000000187000000,
                "duration_ns": 187000000,
            },
            "start_pose": {
                "frame": "map",
                "x_m": 1.0,
                "y_m": 2.0,
                "yaw_rad": 0.2,
            },
            "end_pose": {
                "frame": "map",
                "x_m": 2.5,
                "y_m": 3.0,
                "yaw_rad": 0.22,
            },
            "displacement_m": 1.8,
            "nonzero_pose_progress_observed": True,
            "blocked_reasons": ["local_mock_only", "not_proven"],
            "next_required_evidence": ["live_nav2_pose_progress", "real_delivery_result_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }

    def _cloud_external_probe_payload(self, task_id):
        # live endpoint probe readback 只回显 endpoint 覆盖和 contract ready，不回显 base URL 或响应体。
        return {
            "schema": relay_module.O6_CLOUD_EXTERNAL_PROBE_READBACK_SCHEMA,
            "source_schema": relay_module.CLOUD_EXTERNAL_PROBE_SCHEMA,
            "proof_scope": relay_module.CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
            "task_id": task_id,
            "status": "cloud_external_probe_ready_not_production_proof",
            "source": "o5_same_task_mission_archive_smoke",
            "endpoint_count": 3,
            "endpoints_covered": ["/healthz", "/readyz", "/preflightz"],
            "endpoint_contract_ready": True,
            "base_url_scheme": "http",
            "blocked_reasons": [],
            "next_required_evidence": ["real_public_https_probe", "production_cloud_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "connects_cloud_production": False,
        }

    def _cloud_db_queue_external_probe_payload(self, task_id):
        # DB/queue probe 只保留枚举化状态矩阵，明确当前不是 production DB/queue 成功证明。
        return {
            "schema": relay_module.O6_CLOUD_DB_QUEUE_EXTERNAL_PROBE_READBACK_SCHEMA,
            "source_schema": relay_module.CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
            "proof_scope": relay_module.CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
            "task_id": task_id,
            "status": "cloud_db_queue_external_probe_ready_not_production_proof",
            "source": "o5_same_task_mission_archive_smoke",
            "probe_count": 8,
            "probe_names": [
                "backup_recovery",
                "db_connectivity",
                "migration_check",
                "multi_instance_consistency",
                "ordering_check",
                "queue_connectivity",
                "transaction_isolation",
                "worker_check",
            ],
            "probe_statuses": {
                "db_connectivity_status": "not_externally_proven",
                "queue_connectivity_status": "not_externally_proven",
                "migration_check_status": "not_externally_proven",
                "worker_check_status": "not_externally_proven",
                "multi_instance_consistency_status": "not_externally_proven",
                "ordering_check_status": "not_externally_proven",
                "transaction_isolation_status": "not_externally_proven",
                "backup_recovery_status": "not_externally_proven",
            },
            "external_probe_complete": False,
            "blocked_reasons": [],
            "next_required_evidence": ["real_db_queue_probe", "production_db_queue_trace"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "connects_cloud_production": False,
        }

    def _phone_browser_terminal_material_payload(self, task_id):
        # phone/browser terminal material 只模拟同 task 安全摘要，不携带真实截图、DOM、URL 或凭证。
        return {
            "schema": relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_SCHEMA,
            "proof_scope": relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_PROOF_SCOPE,
            "task_id": task_id,
            "status": "phone_browser_terminal_material_ready_not_delivery_proof",
            "source": "local_mock_phone_browser_terminal_material",
            "safe_evidence_ref": "phone-browser-terminal-summary.json",
            "accepted_materials": [
                "true_phone_browser_evidence",
                "diagnostics_mobile_safe_summary",
                "terminal_result_summary",
            ],
            "terminal_result_type": "browser_terminal_material_summary",
            "true_phone_browser_evidence": True,
            "diagnostics_mobile_safe_summary": True,
            "terminal_result_summary": True,
            "safe_to_control": False,
            "delivery_success": False,
            "route_execution_success": False,
            "hil_pass": False,
            "connects_cloud_production": False,
            "robot_control_executed": False,
        }

    def _field_evidence_archive_request_payload(self):
        # 这个请求体模拟 O6 archive ingest 的新合同：只给 manifest，让 relay 自己派生轨迹与摘要。
        return {
            "robot_id": "trashbot-001",
            "task_id": "field-evidence-field-run-001",
            "field_evidence_manifest": self._field_evidence_manifest_payload(),
            "route_execution_result_delivery_readiness": self._route_execution_result_delivery_readiness_payload(
                "field-evidence-field-run-001"
            ),
            "route_delivery_closure_packet": self._route_delivery_closure_packet_payload(
                "field-evidence-field-run-001"
            ),
            "same_task_field_material_packet": self._same_task_field_material_packet_payload(
                "field-evidence-field-run-001"
            ),
            "localization_path_material_readback": self._localization_path_material_readback_payload(
                "field-evidence-field-run-001"
            ),
            "current_field_evidence_material": self._current_field_evidence_material_payload(
                "field-evidence-field-run-001"
            ),
            "field_operator_confirmation_material": self._field_operator_confirmation_material_payload(
                "field-evidence-field-run-001"
            ),
            "clean_baseline_nav2_path_material": self._clean_baseline_nav2_path_material_payload(
                "field-evidence-field-run-001"
            ),
            "pc_live_nav2_execution_material": self._pc_live_nav2_execution_material_payload(
                "field-evidence-field-run-001"
            ),
            "same_task_route_execution_material_packet": self._same_task_route_execution_material_packet_payload(
                "field-evidence-field-run-001"
            ),
            "phone_browser_terminal_material": self._phone_browser_terminal_material_payload(
                "field-evidence-field-run-001"
            ),
            "bounded_route_terminal_result_material": self._bounded_route_terminal_result_material_payload(
                "field-evidence-field-run-001"
            ),
            "cloud_external_probe": self._cloud_external_probe_payload("field-evidence-field-run-001"),
            "cloud_db_queue_external_probe": self._cloud_db_queue_external_probe_payload(
                "field-evidence-field-run-001"
            ),
        }

    def _live_camera_keyframe_annotation_material_payload(self, task_id="artifact-bundle-task-001"):
        # fixture 只提供冻结 metadata；0/0 invocation 与四 delta=false 防止被误标成 live。
        return {
            "schema": relay_module.LIVE_CAMERA_KEYFRAME_MANIFEST_SCHEMA,
            "task_id": task_id,
            "source_mode": "fixture",
            "source_proof": "fixture_contract_only",
            "topic": "/camera/image_raw",
            "message_type": "sensor_msgs/msg/Image",
            "publisher_count_at_inventory": 1,
            "stamp_sec": 1784091091,
            "stamp_nanosec": 123456789,
            "width": 640,
            "height": 480,
            "step": 1920,
            "encoding": "rgb8",
            "is_bigendian": False,
            "media_basename": "fixture-camera-keyframe.png",
            "media_byte_size": 4096,
            "sha256": "9f" * 32,
            "captured_at_utc": "2026-07-15T04:11:31Z",
            "inventory_ssh_invocation_count": 0,
            "single_frame_capture_invocation_count": 0,
            "redaction_boundary": {
                "classification": "metadata_only_camera_keyframe",
                "raw_pixels_in_manifest": False,
                "binary_inline_in_api": False,
                "binary_logged": False,
                "absolute_path_exposed": False,
                "remote_host_exposed": False,
                "ui_metadata_only": True,
                "privacy_review_status": "not_approved_metadata_only",
                "media_access_scope": "sprint_local_artifact_only",
            },
            "annotation_ready": True,
            "blocked_reasons": [],
            "not_proven": ["live_camera_keyframe_not_captured", "privacy_review_not_approved"],
            "current_run_artifact_delta": False,
            "external_artifact_delta": False,
            "live_control_delta": False,
            "user_action_delta": False,
            "safe_to_control": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "delivery_success": False,
            "hil_pass": False,
        }

    def _artifact_bundle_payload(self):
        # artifact bundle 只提供结构化 ref 和少量轨迹/事件摘要，不读取真实文件内容。
        return {
            "artifact_bundle": {
                "schema": relay_module.O6_ARTIFACT_BUNDLE_SCHEMA,
                "robot_id": "trashbot-001",
                "task_id": "artifact-bundle-task-001",
                "status": "bundle_ready_not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "field_motion_evidence_packet": self._field_motion_evidence_packet_payload(),
                "delivery_result_evidence": self._delivery_result_evidence_payload(),
                "route_execution_result_delivery_readiness": self._route_execution_result_delivery_readiness_payload(
                    "artifact-bundle-task-001"
                ),
                "route_delivery_closure_packet": self._route_delivery_closure_packet_payload(
                    "artifact-bundle-task-001"
                ),
                "same_task_mission_evidence_gate": self._same_task_mission_evidence_gate_payload(
                    "artifact-bundle-task-001"
                ),
                "cloud_external_probe": self._cloud_external_probe_payload("artifact-bundle-task-001"),
                "cloud_db_queue_external_probe": self._cloud_db_queue_external_probe_payload(
                    "artifact-bundle-task-001"
                ),
                "nav2_goal_execution_evidence": self._nav2_goal_execution_evidence_payload(),
                "route_bag_evidence": self._route_bag_evidence_payload(),
                "route_bag_payload_replay": self._route_bag_payload_replay_payload(),
                "route_bag_semantic_replay": self._route_bag_semantic_replay_payload(),
                "route_bag_full_semantic_decode_matrix": self._route_bag_full_semantic_decode_matrix_payload(),
                "route_bag_pose_progress_replay": self._route_bag_pose_progress_replay_payload(),
                "same_task_field_material_packet": self._same_task_field_material_packet_payload(
                    "artifact-bundle-task-001"
                ),
                "localization_path_material_readback": self._localization_path_material_readback_payload(
                    "artifact-bundle-task-001"
                ),
                "current_field_evidence_material": self._current_field_evidence_material_payload(
                    "artifact-bundle-task-001"
                ),
                "field_operator_confirmation_material": self._field_operator_confirmation_material_payload(
                    "artifact-bundle-task-001"
                ),
                "clean_baseline_nav2_path_material": self._clean_baseline_nav2_path_material_payload(
                    "artifact-bundle-task-001"
                ),
                "pc_live_nav2_execution_material": self._pc_live_nav2_execution_material_payload(
                    "artifact-bundle-task-001"
                ),
                "same_task_route_execution_material_packet": self._same_task_route_execution_material_packet_payload(
                    "artifact-bundle-task-001"
                ),
                "phone_browser_terminal_material": self._phone_browser_terminal_material_payload(
                    "artifact-bundle-task-001"
                ),
                "bounded_route_terminal_result_material": (
                    self._bounded_route_terminal_result_material_payload("artifact-bundle-task-001")
                ),
                "route_refs": [
                    "captures/route.csv",
                ],
                "replay_refs": [
                    "captures/fixed_route_replay.jsonl",
                ],
                "keyframe_refs": [
                    "captures/keyframe-0001.jpg",
                ],
                "evidence_refs": [
                    "captures/evidence-0001.json",
                ],
                "trajectory_frames": [
                    {
                        "frame_index": 0,
                        "timestamp_ms": 1720483200000,
                        "x_m": 1.0,
                        "y_m": 2.0,
                        "yaw_rad": 0.2,
                        "speed_mps": 0.0,
                        "state": "bundle_ingested",
                        "evidence_ref": "captures/keyframe-0001.jpg",
                    }
                ],
                "events": [
                    {
                        "event_id": "artifact-bundle-note-001",
                        "event_type": "operator.note",
                        "occurred_at_ms": 1720483200500,
                        "summary": "artifact bundle event summary",
                        "severity": "info",
                        "evidence_refs": ["captures/evidence-0001.json"],
                    }
                ],
            }
        }

    def _offline_artifact_seed_smoke_payload(self):
        # 这组 fixture 直接引用仓库里的真实离线材料，验证 probe 只读与脱敏摘要合同。
        route_root = "sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route"
        replay_ref = "sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl"
        return {
            "artifact_bundle": {
                "schema": relay_module.O6_ARTIFACT_BUNDLE_SCHEMA,
                "robot_id": "trashbot-001",
                "task_id": "offline-artifact-seed-smoke-001",
                "status": "offline_artifact_seed_smoke_ready",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "route_refs": [f"{route_root}/route.csv"],
                "replay_refs": [replay_ref],
                "keyframe_refs": [f"{route_root}/keyframes/001.jpg"],
                "evidence_refs": [f"{route_root}/manifest.json"],
                "trajectory_frames": [
                    {
                        "frame_index": 0,
                        "timestamp_ms": 1781025357570,
                        "x_m": 0.0,
                        "y_m": 0.0,
                        "yaw_rad": 0.0,
                        "speed_mps": 0.0,
                        "state": "offline_artifact_seed_smoke",
                        "evidence_ref": f"{route_root}/keyframes/001.jpg",
                    }
                ],
                "events": [
                    {
                        "event_id": "offline-artifact-seed-smoke-note",
                        "event_type": "operator.note",
                        "occurred_at_ms": 1781025358570,
                        "summary": "offline artifact seed smoke seeded from repo fixtures",
                        "severity": "info",
                        "evidence_refs": [f"{route_root}/manifest.json"],
                    }
                ],
                "artifact_access_root": str(WORKSPACE_ROOT),
            }
        }

    def test_o6_field_evidence_manifest_ingest_seeds_archive_and_consumer_read(self):
        status, created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            self._field_evidence_archive_request_payload(),
        )

        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], relay_module.O6_FIELD_EVIDENCE_ARCHIVE_SCHEMA)
        self.assertEqual(created["source"], "local_mock_field_evidence_archive")
        self.assertTrue(created["field_evidence_written"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["primary_actions_enabled"])
        self.assertEqual(created["task"]["task_id"], "field-evidence-field-run-001")
        self.assertEqual(created["task"]["task_origin"], "field_evidence_manifest")
        self.assertEqual(created["task"]["field_evidence"]["run_id"], "field-run-001")
        self.assertEqual(created["task"]["field_evidence"]["manifest_gate"]["gate_pass"], True)
        self.assertEqual(created["task"]["field_evidence"]["derived_replay"]["frame_count"], 2)
        self.assertEqual(created["task"]["field_evidence"]["request_summary"]["trajectory_frame_count"], 2)
        self.assertEqual(created["task"]["field_evidence"]["request_summary"]["event_count"], 0)
        self.assertEqual(created["task"]["field_evidence"]["request_summary"]["evidence_ref_count"], 0)
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_media_preflight"]["schema"],
            relay_module.O6_ARTIFACT_MEDIA_PREFLIGHT_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_access_probe"]["schema"],
            relay_module.O6_ARTIFACT_ACCESS_PROBE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_access_probe"]["proof_scope"],
            relay_module.O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE,
        )
        self.assertEqual(created["task"]["field_evidence"]["artifact_access_probe"]["status"], "blocked_not_proven")
        self.assertEqual(
            created["task"]["field_evidence"]["route_root_seed_gate"]["schema"],
            relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_root_seed_gate"]["route_root_seed_status"],
            "local_mock_route_root_seed_ready",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["field_motion_evidence_packet"]["schema"],
            relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["field_motion_evidence_packet"]["proof_scope"],
            relay_module.O6_FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["field_motion_evidence_packet"]["status"],
            "field_motion_packet_ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["field_motion_evidence_packet"]["route_summary"]["frame_count"],
            17,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["field_motion_evidence_packet"]["motion_log_summary"][
                "evidence_sources"
            ],
            ["remote_capture_motion_log"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["delivery_result_evidence"]["schema"],
            relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["delivery_result_evidence"]["proof_scope"],
            relay_module.O6_DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["delivery_result_evidence"]["status"],
            "delivery_result_evidence_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["delivery_result_evidence"]["operator_confirmation_present"]
        )
        self.assertFalse(created["task"]["field_evidence"]["delivery_result_evidence"]["delivery_success"])
        self.assertEqual(
            created["task"]["field_evidence"]["route_execution_result_delivery_readiness"]["schema"],
            relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_execution_result_delivery_readiness"]["proof_scope"],
            relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_execution_result_delivery_readiness"]["status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["route_execution_result_delivery_readiness"][
                "linked_nav2_goal_execution_proven"
            ]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_delivery_closure_packet"]["schema"],
            relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_delivery_closure_packet"]["proof_scope"],
            relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_delivery_closure_packet"]["status"],
            "route_delivery_closure_ready_not_success_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["route_delivery_closure_packet"]["linked_pose_progress_ready"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["schema"],
            relay_module.O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["proof_scope"],
            relay_module.O6_SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["terminal_refs"],
            ["cloud_terminal_result.json", "route_execution_summary.json"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["mission_artifact_delta"],
            {
                "same_task_id_consumed": True,
                "cloud_terminal_result_source_consumed": True,
                "route_execution_readiness_consumed": True,
                "route_delivery_closure_consumed": True,
                "nonzero_pose_progress_consumed": True,
                "live_or_field_command_executed": False,
            },
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"][
                "linked_cloud_terminal_result_ready"
            ]
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["same_task_id_consumed"]
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["live_or_field_command_executed"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["support_only_reason"],
            "support_only_same_task_readback_without_live_command",
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["okr_credit_allowed"]
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_mission_evidence_gate"]["delivery_success"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_external_probe"]["schema"],
            relay_module.O6_CLOUD_EXTERNAL_PROBE_READBACK_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_external_probe"]["status"],
            "cloud_external_probe_ready_not_production_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_db_queue_external_probe"]["schema"],
            relay_module.O6_CLOUD_DB_QUEUE_EXTERNAL_PROBE_READBACK_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_db_queue_external_probe"]["probe_count"],
            8,
        )
        self.assertFalse(
            created["task"]["field_evidence"]["route_execution_result_delivery_readiness"][
                "route_execution_success"
            ]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["schema"],
            relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["proof_scope"],
            relay_module.O6_NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["status"],
            "nav2_goal_execution_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["nav2_goal_execution_proven"]
        )
        self.assertFalse(created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["delivery_success"])
        self.assertEqual(
            created["task"]["field_evidence"]["nav2_goal_execution_evidence"]["pose_progress_summary"][
                "pose_sample_count"
            ],
            6,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_evidence"]["schema"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_evidence"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_evidence"]["status"],
            "ready_not_route_execution_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_evidence"]["source_schema"],
            relay_module.ROUTE_BAG_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_evidence"]["sample_topic_names"],
            ["tf", "odom", "scan"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_payload_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_payload_replay"]["status"],
            "route_bag_payload_replay_ready_not_route_execution_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_payload_replay"]["payload_sample_count"],
            3,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_payload_replay"]["sample_topic_names"],
            ["tf", "odom", "scan"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_payload_replay"]["payload_sha256_prefix_samples"],
            ["a1b2c3d4e5f6a7b8", "b1c2d3e4f5a6b7c8", "c1d2e3f4a5b6c7d8"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_semantic_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_semantic_replay"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_semantic_replay"]["status"],
            "route_bag_semantic_replay_ready_not_route_execution_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_semantic_replay"]["semantic_topic_types"],
            [
                "sensor_msgs.msg.LaserScan",
                "sensor_msgs.msg.Image",
                "tf2_msgs.msg.TFMessage",
                "nav_msgs.msg.Odometry",
            ],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_semantic_replay"]["image_summary"]["encoding"],
            "rgb8",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["schema"],
            relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["status"],
            "route_bag_full_semantic_decode_matrix_ready_not_route_execution_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["counts"][
                "decoded_topic_type_count"
            ],
            3,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][0],
            {
                "topic": "scan",
                "type": "sensor_msgs.msg.LaserScan",
                "status": "decoded",
                "message_sample_count": 6,
                "decoded_message_sample_count": 6,
                "unsupported_message_sample_count": 0,
                "decode_failed_message_sample_count": 0,
                "decoder_name": "laser_scan_summary_decoder",
                "decoder": "laser_scan_summary_decoder",
            },
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][2],
            {
                "topic": "odom",
                "type": "nav_msgs.msg.Odometry",
                "status": "decoded",
                "message_sample_count": 5,
                "decoded_message_sample_count": 5,
                "unsupported_message_sample_count": 0,
                "decode_failed_message_sample_count": 0,
                "decoder_name": "decode_odometry_payload",
                "decoder": "decode_odometry_payload",
            },
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3],
            {
                "topic": "diagnostics",
                "type": "diagnostic_msgs.msg.DiagnosticArray",
                "status": "decoded",
                "message_sample_count": 3,
                "decoded_message_sample_count": 3,
                "unsupported_message_sample_count": 0,
                "decode_failed_message_sample_count": 0,
                "decoder_name": "decode_diagnostic_array_payload",
                "decoder": "decode_diagnostic_array_payload",
            },
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["status"],
            "ready_not_live_nav2_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["pose_sample_count"],
            6,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["pose_topic_types"],
            ["tf2_msgs.msg.TFMessage", "nav_msgs.msg.Odometry"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["pose_frame_pairs"],
            [
                {"parent_frame": "map", "child_frame": "base_link"},
                {"parent_frame": "odom", "child_frame": "base_link"},
            ],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["start_pose"]["frame"],
            "map",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["route_bag_pose_progress_replay"]["displacement_m"],
            1.8,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["status"],
            "ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["present_materials"],
            ["route_csv", "keyframes", "route_bag_or_rosbag", "replay_jsonl"],
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["map_yaml_present"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["sample_refs"][0],
            "route.csv",
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["material_sample_refs"][
                "route_csv"
            ]["basename"],
            "route.csv",
        )
        self.assertIn(
            "same_task_field_material_map_yaml_missing_optional",
            created["task"]["field_evidence"]["same_task_field_material_packet"]["blocked_reasons"],
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_field_material_packet"]["same_task_id_consumed"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["proof_scope"],
            relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["status"],
            "route_execution_material_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "route_execution_material_consumed"
            ]
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "live_or_field_command_evidence_present"
            ]
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "delivery_or_operator_material_consumed"
            ]
        )
        self.assertTrue(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "route_execution_credit_candidate"
            ]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "credit_required_evidence"
            ],
            [
                "real_live_nav2_route_execution_trace",
                "real_delivery_result_trace",
                "operator_confirmation_trace",
            ],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["source_sections"],
            [
                "same_task_field_material_packet",
                "route_execution_result_delivery_readiness",
                "route_bag_pose_progress_replay",
                "route_delivery_closure_packet",
            ],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"][
                "material_sample_refs"
            ]["route_bag_pose_progress_replay"]["basename"],
            "route_bag_pose_progress_replay.json",
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["delivery_success"]
        )
        self.assertFalse(
            created["task"]["field_evidence"]["same_task_route_execution_material_packet"]["safe_to_control"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["schema"],
            relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_SCHEMA,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["proof_scope"],
            relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_PROOF_SCOPE,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["status"],
            "phone_browser_terminal_material_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["same_task_id_consumed"]
        )
        self.assertEqual(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["accepted_materials"],
            [
                "true_phone_browser_evidence",
                "diagnostics_mobile_safe_summary",
                "terminal_result_summary",
            ],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["safe_evidence_ref"],
            "phone-browser-terminal-summary.json",
        )
        self.assertFalse(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["route_execution_success"]
        )
        self.assertFalse(created["task"]["field_evidence"]["phone_browser_terminal_material"]["hil_pass"])
        self.assertFalse(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["connects_cloud_production"]
        )
        self.assertFalse(
            created["task"]["field_evidence"]["phone_browser_terminal_material"]["robot_control_executed"]
        )
        self.assertFalse(created["task"]["field_evidence"]["route_bag_evidence"]["delivery_success"])
        self.assertFalse(created["task"]["field_evidence"]["route_bag_evidence"]["safe_to_control"])
        self.assertFalse(created["task"]["field_evidence"]["route_root_seed_gate"]["route_bag_required"])
        self.assertTrue(created["task"]["field_evidence"]["route_root_seed_gate"]["route_bag_present"])
        self.assertFalse(created["task"]["field_evidence"]["route_root_seed_gate"]["safe_to_control"])
        self.assertFalse(created["task"]["field_evidence"]["route_root_seed_gate"]["delivery_success"])
        self.assertFalse(created["task"]["field_evidence"]["route_root_seed_gate"]["robot_control_executed"])
        self.assertIn(
            "allowlist_root_missing",
            created["task"]["field_evidence"]["artifact_access_probe"]["blocked_reasons"],
        )
        self.assertFalse(
            created["task"]["field_evidence"]["artifact_access_probe"]["proof_boundary"]["file_read_attempted"]
        )
        self.assertFalse(created["task"]["field_evidence"]["artifact_access_probe"]["allowlist_root_echoed"])
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_media_preflight"]["counts"]["route_ref_count"],
            1,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_media_preflight"]["counts"]["replay_ref_count"],
            1,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_media_preflight"]["counts"]["keyframe_ref_count"],
            1,
        )
        self.assertEqual(
            created["task"]["field_evidence"]["artifact_media_preflight"]["sample_refs"]["route_ref"],
            "route.csv",
        )
        self.assertEqual(created["task"]["trajectory_frames"][0]["frame_index"], 0)
        self.assertEqual(created["task"]["trajectory_frames"][0]["state"], "field_evidence_manifest_ingested")
        self.assertEqual(created["task"]["trajectory_frames"][1]["frame_index"], 1)
        self.assertEqual(created["task"]["events"][0]["event_type"], "operator.note")
        self.assertGreaterEqual(len(created["task"]["evidence_refs"]), 4)
        self.assertNotIn("/tmp/field_evidence", json.dumps(created, ensure_ascii=False))

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/field-evidence-field-run-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(detail["task"]["task_origin"], "field_evidence_manifest")
        self.assertEqual(detail["task"]["field_evidence"]["artifact_summary"]["present_count"], 4)
        self.assertEqual(detail["task"]["field_evidence"]["source"], "local_mock_field_evidence_archive")
        self.assertEqual(detail["task"]["field_evidence_manifest"]["source"], "local_mock_field_evidence_archive")
        self.assertEqual(detail["task"]["field_evidence_consumer_ingest"]["source"], "local_mock_field_evidence_archive")
        self.assertEqual(
            detail["task"]["field_motion_evidence_packet"]["schema"],
            relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_motion_evidence_packet"]["status"],
            "field_motion_packet_ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["delivery_result_evidence"]["source_schema"],
            "trashbot.delivery_result_record.v1",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["delivery_result_evidence"]["dropoff_confirmation_type"],
            "operator_button_confirmed",
        )
        self.assertEqual(
            detail["task"]["route_execution_result_delivery_readiness"]["source_schema"],
            relay_module.ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_execution_result_delivery_readiness"][
                "route_execution_result_source"
            ],
            "nav2_goal_execution_evidence",
        )
        self.assertEqual(
            detail["task"]["nav2_goal_execution_evidence"]["proof_scope"],
            relay_module.O6_NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["nav2_goal_execution_evidence"]["source"],
            "o11_nav2_goal_execution_proof",
        )
        self.assertEqual(
            detail["task"]["route_bag_evidence"]["schema"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_evidence"]["source_label"],
            "board_live_full_stack_route_bag",
        )
        self.assertEqual(
            detail["task"]["route_bag_payload_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_payload_replay"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
        )
        self.assertEqual(
            detail["task"]["route_bag_semantic_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["route_bag_pose_progress_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_semantic_replay"]["semantic_sample_count"],
            6,
        )
        self.assertEqual(
            detail["task"]["route_bag_full_semantic_decode_matrix"]["coverage_ratio"],
            0.8,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_full_semantic_decode_matrix"]["counts"][
                "unsupported_topic_type_count"
            ],
            1,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_full_semantic_decode_matrix"][
                "topic_type_matrix"
            ][3]["decoder_name"],
            "decode_diagnostic_array_payload",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["route_bag_pose_progress_replay"]["pose_sample_count"],
            6,
        )
        self.assertEqual(
            detail["task"]["same_task_field_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["same_task_field_material_packet"]["counts"][
                "keyframe_count"
            ],
            17,
        )
        self.assertEqual(
            detail["task"]["same_task_field_material_packet"]["material_sample_refs"]["route_bag_or_rosbag"][
                "basename"
            ],
            "route_001.db3",
        )
        self.assertEqual(
            detail["task"]["same_task_route_execution_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["same_task_route_execution_material_packet"][
                "same_task_field_material_packet_status"
            ],
            "ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["same_task_route_execution_material_packet"]["material_summaries"][
                "route_execution_result_delivery_readiness"
            ]["status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["phone_browser_terminal_material"]["status"],
            "phone_browser_terminal_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["phone_browser_terminal_material"][
                "terminal_result_type"
            ],
            "browser_terminal_material_summary",
        )
        self.assertFalse(detail["task"]["phone_browser_terminal_material"]["safe_to_control"])
        self.assertFalse(detail["task"]["phone_browser_terminal_material"]["delivery_success"])
        self.assertFalse(detail["task"]["phone_browser_terminal_material"]["route_execution_success"])
        self.assertFalse(detail["task"]["phone_browser_terminal_material"]["hil_pass"])
        self.assertEqual(
            detail["task"]["same_task_mission_evidence_gate"]["source_schema"],
            relay_module.SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["same_task_mission_evidence_gate"][
                "terminal_ref_count"
            ],
            2,
        )
        self.assertFalse(detail["task"]["same_task_mission_evidence_gate"]["okr_credit_allowed"])
        self.assertEqual(
            detail["task"]["same_task_mission_evidence_gate"]["support_only_reason"],
            "support_only_same_task_readback_without_live_command",
        )
        self.assertEqual(detail["task"]["artifact_access_probe"]["status"], "blocked_not_proven")
        self.assertEqual(detail["task"]["route_root_seed_gate"]["schema"], relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA)
        self.assertFalse(detail["task"]["route_root_seed_gate"]["route_bag_required"])
        self.assertTrue(detail["task"]["route_root_seed_gate"]["route_bag_present"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,trajectory,evidence,events",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["field_evidence"]["status"], "local_mock_field_evidence_ready")
        self.assertEqual(consumer["field_evidence"]["manifest"]["task_origin"], "field_evidence_manifest")
        self.assertEqual(consumer["field_evidence_manifest"]["source"], "local_mock_field_evidence_archive")
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["field_evidence_manifest"]["task_origin"],
            "field_evidence_manifest",
        )
        self.assertEqual(
            consumer["artifact_media_preflight"]["schema"],
            relay_module.O6_ARTIFACT_MEDIA_PREFLIGHT_SCHEMA,
        )
        self.assertEqual(
            consumer["artifact_media_preflight"]["consumer_section_names"],
            ["artifact_media_preflight", "route_replay_mvp", "labeling_mvp"],
        )
        self.assertTrue(consumer["artifact_media_preflight"]["proof_boundary"]["local_mock"])
        self.assertTrue(consumer["artifact_media_preflight"]["proof_boundary"]["not_proven"])
        self.assertFalse(consumer["artifact_media_preflight"]["proof_boundary"]["real_media_read_executed"])
        self.assertEqual(consumer["artifact_media_preflight"]["task_id"], "field-evidence-field-run-001")
        self.assertIn("local_mock_only", consumer["artifact_media_preflight"]["blocked_reasons"])
        self.assertIn("not_proven", consumer["artifact_media_preflight"]["blocked_reasons"])
        self.assertEqual(
            consumer["field_evidence"]["artifact_media_preflight"]["sample_refs"]["replay_ref"],
            "fixed_route_replay.jsonl",
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["artifact_media_preflight"]["sample_refs"]["keyframe_ref"],
            "keyframes",
        )
        self.assertEqual(
            consumer["field_motion_evidence_packet"]["schema"],
            relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA,
        )
        self.assertEqual(
            consumer["field_motion_evidence_packet"]["status"],
            "field_motion_packet_ready_not_delivery_proof",
        )
        self.assertEqual(
            consumer["field_motion_evidence_packet"]["motion_log_summary"]["evidence_sources"],
            ["remote_capture_motion_log"],
        )
        self.assertFalse(consumer["field_motion_evidence_packet"]["robot_control_executed"])
        self.assertEqual(
            consumer["delivery_result_evidence"]["schema"],
            relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            consumer["delivery_result_evidence"]["record_status"],
            "operator_confirmed_not_production_accepted",
        )
        self.assertTrue(consumer["delivery_result_evidence"]["linked_nav2_goal_execution_proven"])
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["delivery_result_evidence"]["source"],
            "field_delivery_result_record",
        )
        self.assertEqual(
            consumer["route_execution_result_delivery_readiness"]["schema"],
            relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        )
        self.assertEqual(
            consumer["route_execution_result_delivery_readiness"]["route_execution_result_status"],
            "nav2_result_summary_ready",
        )
        self.assertTrue(
            consumer["route_execution_result_delivery_readiness"][
                "linked_operator_confirmation_present"
            ]
        )
        self.assertEqual(
            consumer["route_delivery_closure_packet"]["schema"],
            relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
        )
        self.assertEqual(
            consumer["route_delivery_closure_packet"]["status"],
            "route_delivery_closure_ready_not_success_proof",
        )
        self.assertEqual(
            consumer["same_task_field_material_packet"]["status"],
            "ready_not_delivery_proof",
        )
        self.assertEqual(
            consumer["same_task_field_material_packet"]["sample_refs"],
            ["route.csv", "keyframe-0001.jpg", "route_001.db3", "fixed_route_replay.jsonl"],
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["same_task_field_material_packet"]["counts"][
                "route_bag_or_rosbag_count"
            ],
            1,
        )
        self.assertTrue(consumer["same_task_field_material_packet"]["live_or_field_material_consumed"])
        self.assertEqual(
            consumer["same_task_route_execution_material_packet"]["status"],
            "route_execution_material_ready_not_delivery_proof",
        )
        self.assertTrue(consumer["same_task_route_execution_material_packet"]["same_task_id_consumed"])
        self.assertFalse(consumer["same_task_route_execution_material_packet"]["route_execution_success"])
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["same_task_route_execution_material_packet"][
                "material_sample_refs"
            ]["route_delivery_closure_packet"]["basename"],
            "route_delivery_closure_packet.json",
        )
        self.assertEqual(
            consumer["phone_browser_terminal_material"]["proof_scope"],
            relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_PROOF_SCOPE,
        )
        self.assertTrue(consumer["phone_browser_terminal_material"]["phone_browser_terminal_material_written"])
        self.assertTrue(consumer["phone_browser_terminal_material"]["phone_browser_terminal_material_readback"])
        self.assertTrue(consumer["phone_browser_terminal_material"]["true_phone_browser_evidence"])
        self.assertTrue(consumer["phone_browser_terminal_material"]["diagnostics_mobile_safe_summary"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["safe_to_control"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["delivery_success"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["route_execution_success"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["hil_pass"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["connects_cloud_production"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["robot_control_executed"])
        self.assertTrue(
            consumer["route_delivery_closure_packet"][
                "linked_route_execution_result_delivery_readiness_ready"
            ]
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_execution_result_delivery_readiness"][
                "delivery_result_readiness_source"
            ],
            "delivery_result_evidence",
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_delivery_closure_packet"]["source"],
            "algorithm_route_delivery_closure_packet_summary",
        )
        self.assertEqual(
            consumer["same_task_mission_evidence_gate"]["schema"],
            relay_module.O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
        )
        self.assertEqual(
            consumer["same_task_mission_evidence_gate"]["status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertTrue(
            consumer["same_task_mission_evidence_gate"]["linked_readiness_flags"][
                "route_delivery_closure_packet_ready"
            ]
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["same_task_mission_evidence_gate"][
                "mission_artifact_delta"
            ],
            {
                "same_task_id_consumed": True,
                "cloud_terminal_result_source_consumed": True,
                "route_execution_readiness_consumed": True,
                "route_delivery_closure_consumed": True,
                "nonzero_pose_progress_consumed": True,
                "live_or_field_command_executed": False,
            },
        )
        self.assertFalse(consumer["same_task_mission_evidence_gate"]["okr_credit_allowed"])
        self.assertEqual(
            consumer["same_task_mission_evidence_gate"]["support_only_reason"],
            "support_only_same_task_readback_without_live_command",
        )
        self.assertEqual(
            consumer["cloud_external_probe"]["status"],
            "cloud_external_probe_ready_not_production_proof",
        )
        self.assertEqual(consumer["cloud_external_probe"]["endpoint_count"], 3)
        self.assertEqual(
            consumer["cloud_db_queue_external_probe"]["status"],
            "cloud_db_queue_external_probe_ready_not_production_proof",
        )
        self.assertEqual(consumer["cloud_db_queue_external_probe"]["probe_count"], 8)
        self.assertEqual(
            consumer["nav2_goal_execution_evidence"]["schema"],
            relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            consumer["nav2_goal_execution_evidence"]["goal_result_status"],
            "STATUS_SUCCEEDED",
        )
        self.assertTrue(consumer["nav2_goal_execution_evidence"]["base_motion_command_nonzero_proven"])
        self.assertFalse(consumer["nav2_goal_execution_evidence"]["robot_control_executed"])
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["nav2_goal_execution_evidence"]["proof_status"],
            "software_proof",
        )

    def test_o6_bounded_route_execution_gate_material_ingest_and_readback(self):
        task_id = relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_TASK_ID
        payload = self._field_evidence_archive_request_payload()
        payload["task_id"] = task_id
        payload["field_evidence_manifest"]["task_id"] = task_id
        payload["bounded_route_execution_gate_material"] = (
            self._bounded_route_execution_gate_material_payload(task_id)
        )

        status, created = self.client.request("POST", "/api/o6/archive/field-evidence", payload)

        self.assertEqual(status, 201)
        section = created["task"]["field_evidence"]["bounded_route_execution_gate_material"]
        self.assertEqual(section["schema"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_MATERIAL_SCHEMA)
        self.assertEqual(section["proof_scope"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_MATERIAL_PROOF_SCOPE)
        self.assertEqual(section["status"], "bounded_route_execution_gate_material_ready_not_route_execution_proof")
        self.assertEqual(section["packet_id"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_PACKET_ID)
        self.assertEqual(section["task_id"], task_id)
        self.assertEqual(section["route_intent_id"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_ROUTE_INTENT_ID)
        self.assertEqual(section["route_csv_row_count"], 28)
        self.assertEqual(section["path_structured_pose_count"], 28)
        self.assertEqual(section["segment_count"], 27)
        self.assertEqual(section["execution_plan_status"], "blocked_pending_live_safety_gate")
        self.assertEqual(section["global_abort_criteria_count"], 11)
        self.assertEqual(section["bounded_segment_plan_count"], 27)
        self.assertTrue(section["bounded_route_execution_gate_material_readback"])
        self.assertFalse(section["safe_to_control"])
        self.assertFalse(section["delivery_success"])
        self.assertFalse(section["route_execution_success"])
        self.assertFalse(section["hil_pass"])
        self.assertFalse(section["robot_control_executed"])
        self.assertFalse(section["connects_cloud_production"])
        self.assertFalse(section["fixed_false_fields"]["safe_to_control"])

        status, detail = self.client.request("GET", f"/api/o6/archive/tasks/{task_id}", token="")
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["bounded_route_execution_gate_material"]["execution_plan_status"],
            "blocked_pending_live_safety_gate",
        )
        self.assertFalse(detail["task"]["field_evidence_consumer_ingest"][
            "bounded_route_execution_gate_material"
        ]["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            f"/api/o6/consumer/tasks/{task_id}?include=bounded_route_execution_gate_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            consumer["bounded_route_execution_gate_material"]["status"],
            "bounded_route_execution_gate_material_ready_not_route_execution_proof",
        )
        self.assertEqual(consumer["bounded_route_execution_gate_material"]["segment_count"], 27)
        self.assertFalse(consumer["bounded_route_execution_gate_material"]["route_execution_success"])

    def test_o6_bounded_route_execution_gate_material_fail_closes_hostile_payload(self):
        task_id = relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_TASK_ID
        payload = self._field_evidence_archive_request_payload()
        payload["task_id"] = task_id
        payload["field_evidence_manifest"]["task_id"] = task_id
        hostile_material = self._bounded_route_execution_gate_material_payload(task_id)
        hostile_material["safe_to_control"] = True
        hostile_material["bounded_route_command_plan"]["raw_command_body"] = (
            "NavigateToPose /cmd_vel /api/base/manual WAVE ROVER serial UART"
        )
        hostile_material["bounded_route_command_plan"]["local_path"] = "/Users/m1/secrets/route.json"
        hostile_material["bounded_route_command_plan"]["route_execution_success"] = True
        payload["bounded_route_execution_gate_material"] = hostile_material

        status, created = self.client.request("POST", "/api/o6/archive/field-evidence", payload)

        self.assertEqual(status, 201)
        section = created["task"]["field_evidence"]["bounded_route_execution_gate_material"]
        self.assertEqual(section["status"], "blocked_not_proven")
        self.assertIn("bounded_route_execution_gate_material_dangerous_true", section["blocked_reasons"])
        self.assertFalse(section["safe_to_control"])
        self.assertFalse(section["delivery_success"])
        self.assertFalse(section["route_execution_success"])
        self.assertFalse(section["hil_pass"])
        self.assertFalse(section["robot_control_executed"])
        encoded = json.dumps(created, ensure_ascii=False).lower()
        self.assertNotIn("/users/m1/secrets", encoded)
        self.assertNotIn("raw_command_body", encoded)
        self.assertNotIn("navigatetopose /cmd_vel", encoded)

        status, consumer = self.client.request(
            "GET",
            f"/api/o6/consumer/tasks/{task_id}?include=bounded_route_execution_gate_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["bounded_route_execution_gate_material"]["status"], "blocked_not_proven")
        self.assertFalse(consumer["bounded_route_execution_gate_material"]["safe_to_control"])

    def test_o6_bounded_route_terminal_result_material_ingest_and_readback(self):
        task_id = relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_TASK_ID
        payload = self._field_evidence_archive_request_payload()
        payload["task_id"] = task_id
        payload["field_evidence_manifest"]["task_id"] = task_id
        payload["bounded_route_terminal_result_material"] = (
            self._bounded_route_terminal_result_material_payload(task_id)
        )

        status, created = self.client.request("POST", "/api/o6/archive/field-evidence", payload)

        self.assertEqual(status, 201)
        section = created["task"]["field_evidence"]["bounded_route_terminal_result_material"]
        self.assertEqual(section["schema"], relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_MATERIAL_SCHEMA)
        self.assertEqual(section["source_schema"], relay_module.O5_BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA)
        self.assertEqual(section["proof_scope"], relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_MATERIAL_PROOF_SCOPE)
        self.assertEqual(section["source_proof_boundary"], relay_module.O5_BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_SCOPE)
        self.assertEqual(section["status"], "bounded_route_terminal_result_material_ready_not_delivery_proof")
        self.assertEqual(section["packet_id"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_PACKET_ID)
        self.assertEqual(section["task_id"], task_id)
        self.assertEqual(section["route_intent_id"], relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_ROUTE_INTENT_ID)
        self.assertEqual(section["result_code"], relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_CODE)
        self.assertEqual(section["terminal_result_state"], relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_STATE)
        self.assertEqual(section["reconciliation_state"], relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_STATE)
        self.assertEqual(section["safe_evidence_ref"], "o5_bounded_route_terminal_result_bridge_summary.json")
        self.assertEqual(section["route_csv_row_count"], 28)
        self.assertEqual(section["path_structured_pose_count"], 28)
        self.assertEqual(section["segment_count"], 27)
        self.assertTrue(section["same_task_id_consumed"])
        self.assertTrue(section["bounded_route_terminal_result_material_written"])
        self.assertTrue(section["bounded_route_terminal_result_material_readback"])
        self.assertFalse(section["delivery_success"])
        self.assertFalse(section["route_execution_success"])
        self.assertFalse(section["safe_to_control"])
        self.assertFalse(section["hil_pass"])
        self.assertFalse(section["robot_control_executed"])
        self.assertFalse(section["connects_cloud_production"])
        self.assertFalse(section["fixed_false_fields"]["delivery_success"])

        status, detail = self.client.request("GET", f"/api/o6/archive/tasks/{task_id}", token="")
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["bounded_route_terminal_result_material"]["result_code"],
            relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_CODE,
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["bounded_route_terminal_result_material"][
                "status"
            ],
            "bounded_route_terminal_result_material_ready_not_delivery_proof",
        )
        self.assertFalse(detail["task"]["bounded_route_terminal_result_material"]["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            f"/api/o6/consumer/tasks/{task_id}?include=bounded_route_terminal_result_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            consumer["bounded_route_terminal_result_material"]["status"],
            "bounded_route_terminal_result_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            consumer["bounded_route_terminal_result_material"]["result_code"],
            relay_module.O6_BOUNDED_ROUTE_TERMINAL_RESULT_CODE,
        )
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["delivery_success"])
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["route_execution_success"])
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["safe_to_control"])
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["hil_pass"])
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["robot_control_executed"])

    def test_o6_bounded_route_terminal_result_material_fail_closes_hostile_payload(self):
        task_id = relay_module.O6_BOUNDED_ROUTE_EXECUTION_GATE_TASK_ID
        payload = self._field_evidence_archive_request_payload()
        payload["task_id"] = task_id
        payload["field_evidence_manifest"]["task_id"] = task_id
        hostile_material = self._bounded_route_terminal_result_material_payload(task_id)
        hostile_material["safe_to_control"] = True
        hostile_material["raw_command_body"] = "NavigateToPose /cmd_vel /api/base/manual"
        hostile_material["local_path"] = "/Users/m1/secrets/o5_terminal.json"
        hostile_material["route_execution_success"] = True
        payload["bounded_route_terminal_result_material"] = hostile_material

        status, created = self.client.request("POST", "/api/o6/archive/field-evidence", payload)

        self.assertEqual(status, 201)
        section = created["task"]["field_evidence"]["bounded_route_terminal_result_material"]
        self.assertEqual(section["status"], "blocked_not_proven")
        self.assertIn("bounded_route_terminal_result_material_dangerous_true", section["blocked_reasons"])
        self.assertFalse(section["delivery_success"])
        self.assertFalse(section["route_execution_success"])
        self.assertFalse(section["safe_to_control"])
        self.assertFalse(section["hil_pass"])
        self.assertFalse(section["robot_control_executed"])
        encoded = json.dumps(created, ensure_ascii=False).lower()
        self.assertNotIn("/users/m1/secrets", encoded)
        self.assertNotIn("raw_command_body", encoded)
        self.assertNotIn("navigatetopose /cmd_vel", encoded)

        status, consumer = self.client.request(
            "GET",
            f"/api/o6/consumer/tasks/{task_id}?include=bounded_route_terminal_result_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["bounded_route_terminal_result_material"]["status"], "blocked_not_proven")
        self.assertFalse(consumer["bounded_route_terminal_result_material"]["safe_to_control"])

    def test_o6_field_evidence_probe_readback_fail_closes_hostile_payload(self):
        payload = self._field_evidence_archive_request_payload()
        payload["cloud_external_probe"] = {
            **self._cloud_external_probe_payload("field-evidence-field-run-001"),
            "authorization": "Bearer should-never-leak",
        }
        payload["cloud_db_queue_external_probe"] = {
            **self._cloud_db_queue_external_probe_payload("field-evidence-field-run-001"),
            "delivery_success": True,
        }

        status, created = self.client.request("POST", "/api/o6/archive/field-evidence", payload)

        self.assertEqual(status, 201)
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_external_probe"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "cloud_external_probe_unsafe",
            created["task"]["field_evidence"]["cloud_external_probe"]["blocked_reasons"],
        )
        self.assertEqual(
            created["task"]["field_evidence"]["cloud_db_queue_external_probe"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "cloud_db_queue_external_probe_unsafe",
            created["task"]["field_evidence"]["cloud_db_queue_external_probe"]["blocked_reasons"],
        )
        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,trajectory,evidence,events",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            consumer["route_bag_evidence"]["schema"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA,
        )
        self.assertEqual(consumer["route_bag_evidence"]["topic_count"], 3)
        self.assertEqual(consumer["route_bag_evidence"]["message_count"], 42)
        self.assertEqual(
            consumer["field_evidence"]["route_bag_evidence"]["sample_topic_names"],
            ["tf", "odom", "scan"],
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_evidence"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
        )
        self.assertEqual(
            consumer["route_bag_payload_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        )
        self.assertEqual(
            consumer["field_evidence"]["route_bag_payload_replay"]["payload_sample_count"],
            3,
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_payload_replay"]["proof_scope"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
        )
        self.assertEqual(
            consumer["route_bag_semantic_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        )
        self.assertEqual(
            consumer["field_evidence"]["route_bag_semantic_replay"]["laser_scan_summary"]["range_sample_count"],
            1440,
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_semantic_replay"]["tf_summary"]["frame_id_samples"],
            ["map", "odom"],
        )
        self.assertIn(
            "nav_msgs.msg.Odometry",
            consumer["route_bag_semantic_replay"]["semantic_topic_types"],
        )
        self.assertEqual(
            consumer["route_bag_full_semantic_decode_matrix"]["schema"],
            relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        )
        self.assertEqual(
            consumer["field_evidence"]["route_bag_full_semantic_decode_matrix"]["counts"][
                "failed_topic_type_count"
            ],
            1,
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_full_semantic_decode_matrix"][
                "topic_type_matrix"
            ][2]["decoder"],
            "decode_odometry_payload",
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_full_semantic_decode_matrix"][
                "topic_type_matrix"
            ][3]["decoder_name"],
            "decode_diagnostic_array_payload",
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_full_semantic_decode_matrix"][
                "topic_type_matrix"
            ][3]["decoded_message_sample_count"],
            3,
        )
        self.assertFalse(consumer["route_bag_full_semantic_decode_matrix"]["safe_to_control"])
        self.assertFalse(consumer["route_bag_full_semantic_decode_matrix"]["delivery_success"])
        self.assertFalse(consumer["route_bag_full_semantic_decode_matrix"]["route_execution_success"])
        self.assertEqual(
            consumer["route_bag_pose_progress_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        )
        self.assertEqual(
            consumer["field_evidence"]["route_bag_pose_progress_replay"]["pose_time_span_ns"]["duration_ns"],
            187000000,
        )
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_bag_pose_progress_replay"]["pose_frame_pairs"],
            [
                {"parent_frame": "map", "child_frame": "base_link"},
                {"parent_frame": "odom", "child_frame": "base_link"},
            ],
        )
        self.assertFalse(consumer["route_bag_semantic_replay"]["robot_control_executed"])
        self.assertEqual(consumer["artifact_access_probe"]["schema"], relay_module.O6_ARTIFACT_ACCESS_PROBE_SCHEMA)
        self.assertIn("allowlist_root_missing", consumer["artifact_access_probe"]["blocked_reasons"])
        self.assertEqual(consumer["route_root_seed_gate"]["schema"], relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA)
        self.assertEqual(consumer["route_root_seed_gate"]["route_root_seed_status"], "local_mock_route_root_seed_ready")
        self.assertFalse(consumer["route_root_seed_gate"]["route_bag_required"])
        self.assertTrue(consumer["route_root_seed_gate"]["route_bag_present"])
        self.assertEqual(consumer["route_root_seed_gate"]["route_csv_summary"]["sample_ref"], "route.csv")
        self.assertEqual(consumer["field_evidence"]["route_root_seed_gate"]["schema"], relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA)
        self.assertEqual(
            consumer["field_evidence_consumer_ingest"]["route_root_seed_gate"]["proof_scope"],
            relay_module.O6_ROUTE_ROOT_SEED_GATE_PROOF_SCOPE,
        )
        self.assertEqual(consumer["trajectory"]["status"], "local_mock_archive_ready")
        self.assertEqual(consumer["trajectory"]["total_count"], 2)
        self.assertEqual(consumer["trajectory"]["frames"][0]["frame_index"], 0)
        self.assertEqual(consumer["evidence"]["status"], "local_mock_archive_ready")
        self.assertEqual(consumer["events"]["events"][0]["event_type"], "operator.note")
        self.assertFalse(consumer["proof_boundary"]["safe_to_control"])

        status, explicit_route_material = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=same_task_route_execution_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            explicit_route_material["same_task_route_execution_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            explicit_route_material["same_task_route_execution_material_packet"]["status"],
            "route_execution_material_ready_not_delivery_proof",
        )
        status, explicit_phone_browser = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=phone_browser_terminal_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            explicit_phone_browser["phone_browser_terminal_material"]["safe_evidence_ref"],
            "phone-browser-terminal-summary.json",
        )
        self.assertFalse(explicit_phone_browser["phone_browser_terminal_material"]["safe_to_control"])
        self.assertFalse(explicit_phone_browser["phone_browser_terminal_material"]["delivery_success"])
        self.assertFalse(explicit_phone_browser["phone_browser_terminal_material"]["route_execution_success"])
        self.assertFalse(explicit_phone_browser["phone_browser_terminal_material"]["hil_pass"])
        for forbidden_key in (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "connects_cloud_production",
            "robot_control_executed",
            "real_cloud_db_connected",
            "real_oss_connected",
        ):
            self.assertFalse(consumer[forbidden_key])
            self.assertFalse(consumer["field_evidence"][forbidden_key])
            self.assertFalse(consumer["field_evidence_consumer_ingest"][forbidden_key])

        status, duplicate = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            self._field_evidence_archive_request_payload(),
        )
        self.assertEqual(status, 200)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["write_status"], "updated")

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=route_execution_result_delivery_readiness,route_bag_evidence,route_bag_payload_replay,route_bag_semantic_replay,route_bag_full_semantic_decode_matrix,route_bag_pose_progress_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            explicit["route_execution_result_delivery_readiness"]["status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )
        self.assertEqual(explicit["route_bag_evidence"]["schema"], relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA)
        self.assertEqual(explicit["route_bag_evidence"]["status"], "ready_not_route_execution_proof")
        self.assertFalse(explicit["route_bag_evidence"]["robot_control_executed"])
        self.assertEqual(
            explicit["route_bag_payload_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        )
        self.assertEqual(
            explicit["route_bag_payload_replay"]["status"],
            "route_bag_payload_replay_ready_not_route_execution_proof",
        )
        self.assertEqual(
            explicit["route_bag_semantic_replay"]["status"],
            "route_bag_semantic_replay_ready_not_route_execution_proof",
        )
        self.assertEqual(
            explicit["route_bag_full_semantic_decode_matrix"]["status"],
            "route_bag_full_semantic_decode_matrix_ready_not_route_execution_proof",
        )
        self.assertEqual(
            explicit["route_bag_full_semantic_decode_matrix"]["counts"]["topic_type_count"],
            5,
        )
        self.assertEqual(
            explicit["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3]["type"],
            "diagnostic_msgs.msg.DiagnosticArray",
        )
        self.assertEqual(
            explicit["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3]["status"],
            "decoded",
        )
        self.assertEqual(
            explicit["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3]["decoder_name"],
            "decode_diagnostic_array_payload",
        )
        self.assertFalse(explicit["route_bag_full_semantic_decode_matrix"]["safe_to_control"])
        self.assertFalse(explicit["route_bag_full_semantic_decode_matrix"]["delivery_success"])
        self.assertEqual(
            explicit["route_bag_pose_progress_replay"]["status"],
            "ready_not_live_nav2_proof",
        )

    def test_o6_field_evidence_manifest_ingest_rejects_unsafe_gate_and_bad_artifacts(self):
        unsafe_manifest = self._field_evidence_manifest_payload()
        unsafe_manifest["safe_to_control"] = True
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": unsafe_manifest,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        real_claim = self._field_evidence_manifest_payload()
        real_claim["connects_cloud_production"] = True
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": real_claim,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            raw_body=b"{bad-json",
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "malformed_json")

        missing_schema = self._field_evidence_manifest_payload()
        missing_schema.pop("schema")
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": missing_schema,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("schema", body["error"]["message"].lower())

        bad_gate = self._field_evidence_manifest_payload()
        bad_gate["manifest_gate"]["gate_pass"] = False
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": bad_gate,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("gate", body["error"]["message"].lower())

        bad_artifact = self._field_evidence_manifest_payload()
        bad_artifact["artifacts"]["route_csv"]["sha256"] = ""
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": bad_artifact,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("checksum", body["error"]["message"].lower())

        unsafe_token = self._field_evidence_manifest_payload()
        unsafe_token["artifacts"]["route_csv"]["path"] = "https://example.test/route.csv?token=secret"
        status, body = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            {
                "robot_id": "trashbot-001",
                "task_id": "field-evidence-field-run-001",
                "field_evidence_manifest": unsafe_token,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        unsafe_raw = self._field_evidence_archive_request_payload()
        unsafe_raw["evidence_refs"] = [{"evidence_ref": "frame-001", "image_base64": "base64,raw"}]
        status, body = self.client.request("POST", "/api/o6/archive/field-evidence", unsafe_raw)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        dangerous_true = self._field_evidence_archive_request_payload()
        dangerous_true["real_oss_connected"] = True
        status, body = self.client.request("POST", "/api/o6/archive/field-evidence", dangerous_true)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        dangerous_route_gate = self._field_evidence_archive_request_payload()
        dangerous_route_gate["field_evidence_manifest"]["route_root_seed_gate"]["robot_control_executed"] = True
        status, body = self.client.request("POST", "/api/o6/archive/field-evidence", dangerous_route_gate)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        status, listing = self.client.request("GET", "/api/o6/archive/tasks", token="")
        self.assertEqual(status, 200)
        self.assertEqual(listing["task_list"]["total_tasks"], 0)

    def test_o6_route_bag_pose_progress_replay_missing_or_unsafe_returns_blocked_summary(self):
        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pose-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["route_bag_pose_progress_replay"]["schema"] = "trashbot.route_bag_pose_progress_replay.v0"
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_schema_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertTrue(
            any(
                reason in bad_schema_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["blocked_reasons"]
                for reason in (
                    "route_bag_pose_progress_replay_schema_unsupported",
                    "route_bag_pose_progress_replay_unsafe",
                )
            )
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pose-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_bag_pose_progress_replay"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_scope_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertTrue(
            any(
                reason in bad_scope_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["blocked_reasons"]
                for reason in (
                    "route_bag_pose_progress_replay_proof_scope_unsupported",
                    "route_bag_pose_progress_replay_unsafe",
                )
            )
        )

        unsafe_frame_payload = self._artifact_bundle_payload()
        unsafe_frame_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pose-unsafe-frame-001"
        unsafe_frame_payload["artifact_bundle"]["route_bag_pose_progress_replay"]["start_pose"]["frame"] = "/tmp/should-not-echo"
        status, unsafe_frame_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_frame_payload,
        )
        encoded = json.dumps(unsafe_frame_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_frame_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_bag_pose_progress_replay_unsafe",
            unsafe_frame_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["blocked_reasons"],
        )
        self.assertNotIn("/tmp/should-not-echo", encoded)

        missing_fields_payload = self._artifact_bundle_payload()
        missing_fields_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pose-missing-001"
        missing_fields_payload["artifact_bundle"]["route_bag_pose_progress_replay"].pop("pose_frame_pairs")
        status, missing_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_fields_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            missing_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_bag_pose_progress_replay_frame_pairs_invalid",
            missing_created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["blocked_reasons"],
        )

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-pose-unsafe-frame-001?include=route_bag_pose_progress_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_bag_pose_progress_replay"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_pose_progress_replay_unsafe",
            explicit["route_bag_pose_progress_replay"]["blocked_reasons"],
        )

    def test_o6_phone_browser_terminal_material_fail_closes_hostile_payload(self):
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"]["task_id"] = "artifact-bundle-phone-browser-hostile-001"
        payload["artifact_bundle"]["phone_browser_terminal_material"] = {
            **self._phone_browser_terminal_material_payload("artifact-bundle-phone-browser-hostile-001"),
            "raw_url": "https://example.test/result?token=should-never-leak",
            "cookie": "session=cookie-secret",
            "Authorization": "Bearer should-never-leak",
            "local_path": "/Users/m1/private/screenshot.png",
            "screenshot_body": "data:image/png;base64,abc123",
            "dom_dump": "<html>secret dom</html>",
            "traceback": "Traceback should never echo",
            "cmd_vel_topic": "/cmd_vel",
            "serial_device": "/dev/ttyUSB0",
            "wave_rover_note": "WAVE ROVER UART raw frame",
            "delivery_success": True,
        }

        status, created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)
        encoded = json.dumps(created, ensure_ascii=False)

        self.assertEqual(status, 201)
        section = created["task"]["artifact_bundle"]["phone_browser_terminal_material"]
        self.assertEqual(section["status"], "blocked_not_proven")
        self.assertFalse(section["phone_browser_terminal_material_written"])
        self.assertFalse(section["phone_browser_terminal_material_readback"])
        self.assertFalse(section["safe_to_control"])
        self.assertFalse(section["delivery_success"])
        self.assertFalse(section["route_execution_success"])
        self.assertFalse(section["hil_pass"])
        self.assertFalse(section["connects_cloud_production"])
        self.assertFalse(section["robot_control_executed"])
        self.assertTrue(
            any(
                reason in section["blocked_reasons"]
                for reason in (
                    "phone_browser_terminal_material_dangerous_true",
                    "phone_browser_terminal_material_raw_url_blocked",
                    "phone_browser_terminal_material_unsafe",
                )
            )
        )
        for forbidden in (
            "https://example.test",
            "should-never-leak",
            "cookie-secret",
            "/Users/m1/private",
            "data:image",
            "<html>",
            "Traceback should never echo",
            "/cmd_vel",
            "/dev/ttyUSB0",
            "WAVE ROVER UART",
        ):
            self.assertNotIn(forbidden, encoded)

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-phone-browser-hostile-001?include=phone_browser_terminal_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["phone_browser_terminal_material"]["status"], "blocked_not_proven")
        self.assertFalse(explicit["phone_browser_terminal_material"]["phone_browser_terminal_material_written"])
        self.assertFalse(explicit["phone_browser_terminal_material"]["safe_to_control"])
        self.assertFalse(explicit["phone_browser_terminal_material"]["delivery_success"])

    def test_o6_artifact_bundle_ingest_seeds_archive_and_consumer_aliases(self):
        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            self._artifact_bundle_payload(),
        )

        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], relay_module.O6_ARTIFACT_BUNDLE_ARCHIVE_SCHEMA)
        self.assertTrue(created["artifact_bundle_written"])
        self.assertEqual(created["task"]["task_origin"], "artifact_bundle")
        self.assertEqual(created["task"]["artifact_bundle"]["schema"], relay_module.O6_ARTIFACT_BUNDLE_SCHEMA)
        self.assertEqual(created["task"]["artifact_bundle"]["route_refs"], ["route.csv"])
        self.assertEqual(created["task"]["artifact_bundle"]["replay_refs"], ["fixed_route_replay.jsonl"])
        self.assertEqual(created["task"]["artifact_bundle"]["keyframe_refs"], ["keyframe-0001.jpg"])
        self.assertEqual(created["task"]["artifact_bundle"]["evidence_refs"], ["evidence-0001.json"])
        self.assertEqual(
            created["task"]["artifact_bundle"]["field_motion_evidence_packet"]["schema"],
            relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["field_motion_evidence_packet"]["status"],
            "field_motion_packet_ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["delivery_result_evidence"]["schema"],
            relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["delivery_result_evidence"]["status"],
            "delivery_result_evidence_ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]["schema"],
            relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]["status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_delivery_closure_packet"]["schema"],
            relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_delivery_closure_packet"]["status"],
            "route_delivery_closure_ready_not_success_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["schema"],
            relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["status"],
            "nav2_goal_execution_ready_not_delivery_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_evidence"]["schema"],
            relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_evidence"]["status"],
            "ready_not_route_execution_proof",
        )
        self.assertEqual(created["task"]["artifact_bundle"]["route_bag_evidence"]["sample_topic_names"], ["tf", "odom", "scan"])
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["schema"],
            relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["counts"][
                "decoded_message_sample_count"
            ],
            14,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][2][
                "decoder"
            ],
            "decode_odometry_payload",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3][
                "decoder_name"
            ],
            "decode_diagnostic_array_payload",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["status"],
            "ready_not_live_nav2_proof",
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["same_task_field_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["same_task_field_material_packet"]["counts"][
                "present_material_count"
            ],
            4,
        )
        self.assertFalse(
            created["task"]["artifact_bundle"]["same_task_field_material_packet"]["map_yaml_present"]
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"]["schema"],
            relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"]["status"],
            "route_execution_material_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "route_execution_material_consumed"
            ]
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["schema"],
            relay_module.O6_PHONE_BROWSER_TERMINAL_MATERIAL_SCHEMA,
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["status"],
            "phone_browser_terminal_material_ready_not_delivery_proof",
        )
        self.assertTrue(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"][
                "phone_browser_terminal_material_written"
            ]
        )
        self.assertFalse(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["safe_to_control"]
        )
        self.assertFalse(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["delivery_success"]
        )
        self.assertFalse(
            created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["route_execution_success"]
        )
        self.assertFalse(created["task"]["artifact_bundle"]["phone_browser_terminal_material"]["hil_pass"])
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["pose_topic_types"],
            ["tf2_msgs.msg.TFMessage", "nav_msgs.msg.Odometry"],
        )
        self.assertEqual(
            created["task"]["artifact_bundle"]["artifact_media_preflight"]["counts"]["route_ref_count"],
            1,
        )
        self.assertEqual(created["task"]["trajectory_frames"][0]["state"], "bundle_ingested")
        self.assertEqual(created["task"]["events"][0]["event_id"], "artifact-bundle-ingest")
        self.assertNotIn("captures/", json.dumps(created, ensure_ascii=False))

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/artifact-bundle-task-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(detail["task"]["artifact_bundle"]["task_origin"], "artifact_bundle")
        self.assertEqual(
            detail["task"]["field_motion_evidence_packet"]["proof_scope"],
            relay_module.O6_FIELD_MOTION_EVIDENCE_PACKET_PROOF_SCOPE,
        )
        self.assertEqual(
            detail["task"]["artifact_bundle_consumer_ingest"]["status"],
            "local_mock_artifact_bundle_ready",
        )
        self.assertTrue(detail["task"]["artifact_bundle"]["delivery_result_evidence"]["record_present"])
        self.assertTrue(
            detail["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"][
                "delivery_result_readiness_ready"
            ]
        )
        self.assertTrue(
            detail["task"]["artifact_bundle"]["route_delivery_closure_packet"][
                "linked_operator_confirmation_ready"
            ]
        )
        self.assertTrue(detail["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["goal_accepted"])
        self.assertTrue(detail["task"]["artifact_bundle"]["route_bag_evidence"]["db3_read_ok"])
        self.assertEqual(detail["task"]["route_bag_evidence"]["source_label"], "board_live_full_stack_route_bag")
        self.assertEqual(
            detail["task"]["route_bag_semantic_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["route_bag_pose_progress_replay"]["schema"],
            relay_module.O6_ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["route_bag_full_semantic_decode_matrix"]["schema"],
            relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        )
        self.assertEqual(
            detail["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["coverage_ratio"],
            0.8,
        )
        self.assertEqual(
            detail["task"]["artifact_bundle"]["route_bag_semantic_replay"]["semantic_decode_failed_count"],
            1,
        )
        self.assertEqual(
            detail["task"]["artifact_bundle"]["route_bag_pose_progress_replay"]["pose_decode_failed_count"],
            1,
        )
        self.assertEqual(
            detail["task"]["same_task_field_material_packet"]["material_sample_refs"]["route_bag_or_rosbag"]["basename"],
            "route_001.db3",
        )
        self.assertEqual(
            detail["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "material_sample_refs"
            ]["same_task_field_material_packet"]["basename"],
            "same_task_field_material_packet.json",
        )
        self.assertFalse(detail["task"]["same_task_route_execution_material_packet"]["hil_pass"])
        self.assertEqual(
            detail["task"]["artifact_bundle_consumer_ingest"]["phone_browser_terminal_material"][
                "safe_evidence_ref"
            ],
            "phone-browser-terminal-summary.json",
        )
        self.assertFalse(detail["task"]["phone_browser_terminal_material"]["robot_control_executed"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,trajectory,evidence,events",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["field_evidence"]["task_origin"], "artifact_bundle")
        self.assertEqual(consumer["artifact_bundle"]["route_refs"], ["route.csv"])
        self.assertEqual(
            consumer["artifact_bundle_consumer_ingest"]["status"],
            "local_mock_artifact_bundle_ready",
        )
        self.assertEqual(
            consumer["field_motion_evidence_packet"]["status"],
            "field_motion_packet_ready_not_delivery_proof",
        )
        self.assertEqual(
            consumer["route_delivery_closure_packet"]["status"],
            "route_delivery_closure_ready_not_success_proof",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["field_motion_evidence_packet"]["motion_log_summary"]["evidence_sources"],
            ["remote_capture_motion_log"],
        )
        self.assertEqual(
            consumer["delivery_result_evidence"]["completed_at_utc"],
            "2026-07-09T08:15:00Z",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["delivery_result_evidence"]["source_schema"],
            "trashbot.delivery_result_record.v1",
        )
        self.assertEqual(
            consumer["route_execution_result_delivery_readiness"]["operator_confirmation_readiness_status"],
            "operator_confirmation_summary_ready",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["route_execution_result_delivery_readiness"]["task_id_source"],
            "manifest_task_id",
        )
        self.assertEqual(
            consumer["nav2_goal_execution_evidence"]["source"],
            "o11_nav2_goal_execution_proof",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["nav2_goal_execution_evidence"]["base_command_mode"],
            "T1",
        )
        self.assertEqual(consumer["route_bag_evidence"]["db3_sha256_prefix"], "0123456789abcdef")
        self.assertTrue(consumer["artifact_bundle"]["route_bag_evidence"]["metadata_present"])
        self.assertEqual(
            consumer["route_bag_semantic_replay"]["semantic_decode_ok_count"],
            5,
        )
        self.assertEqual(
            consumer["route_bag_full_semantic_decode_matrix"]["counts"]["unsupported_message_sample_count"],
            2,
        )
        self.assertEqual(
            consumer["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][2]["type"],
            "nav_msgs.msg.Odometry",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3]["type"],
            "diagnostic_msgs.msg.DiagnosticArray",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["topic_type_matrix"][3][
                "decoder_name"
            ],
            "decode_diagnostic_array_payload",
        )
        self.assertEqual(
            consumer["route_bag_pose_progress_replay"]["displacement_m"],
            1.8,
        )
        self.assertEqual(
            consumer["same_task_field_material_packet"]["sample_refs"][-1],
            "fixed_route_replay.jsonl",
        )
        self.assertTrue(consumer["artifact_bundle"]["same_task_field_material_packet"]["same_task_id_consumed"])
        self.assertEqual(
            consumer["same_task_route_execution_material_packet"]["same_task_field_material_packet_status"],
            "ready_not_delivery_proof",
        )
        self.assertEqual(
            consumer["artifact_bundle"]["same_task_route_execution_material_packet"]["source_sections"][0],
            "same_task_field_material_packet",
        )
        self.assertEqual(
            consumer["phone_browser_terminal_material"]["status"],
            "phone_browser_terminal_material_ready_not_delivery_proof",
        )
        self.assertTrue(consumer["phone_browser_terminal_material"]["same_task_id_consumed"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["connects_cloud_production"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["route_execution_success"])
        self.assertFalse(consumer["phone_browser_terminal_material"]["hil_pass"])
        self.assertEqual(
            consumer["artifact_bundle"]["route_bag_semantic_replay"]["image_summary"]["width"],
            640,
        )
        self.assertEqual(consumer["artifact_media_preflight"]["sample_refs"]["replay_ref"], "fixed_route_replay.jsonl")
        self.assertIn("real_media_fetch_blocked", consumer["artifact_media_preflight"]["blocked_reasons"])
        self.assertFalse(consumer["artifact_bundle"]["safe_to_control"])

        status, alias = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            self._artifact_bundle_payload(),
        )
        self.assertEqual(status, 200)
        self.assertTrue(alias["artifact_bundle_written"])
        self.assertTrue(alias["duplicate"])

    def test_o6_live_camera_keyframe_annotation_material_fixture_lineage_and_hostile_fail_closed(self):
        # fixture 走既有 artifact-bundle 写入和 consumer detail；它只能获得 fixture badge。
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"]["live_camera_keyframe_annotation_material"] = (
            self._live_camera_keyframe_annotation_material_payload()
        )
        status, created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)
        self.assertEqual(status, 201)
        material = created["task"]["live_camera_keyframe_annotation_material"]
        self.assertEqual(material["schema"], relay_module.O6_LIVE_CAMERA_KEYFRAME_ANNOTATION_MATERIAL_SCHEMA)
        self.assertEqual(material["status"], "annotation_ready_fixture_contract_only")
        self.assertEqual(material["source_badge"], "fixture")
        self.assertTrue(material["annotation_ready"])
        self.assertTrue(material["lineage_verified"])
        self.assertEqual(material["task_id"], "artifact-bundle-task-001")
        self.assertEqual(material["sha256"], "9f" * 32)
        self.assertEqual(material["stamp_nanosec"], 123456789)
        self.assertFalse(material["current_run_artifact_delta"])
        self.assertFalse(material["external_artifact_delta"])
        self.assertFalse(material["live_control_delta"])
        self.assertFalse(material["user_action_delta"])
        self.assertFalse(material["safe_to_control"])
        self.assertFalse(material["route_execution_success"])
        self.assertFalse(material["delivery_success"])
        self.assertFalse(material["hil_pass"])
        # task detail 与 include readback 必须保持相同 task/hash/topic/stamp/dimensions/encoding。
        status, detail = self.client.request("GET", "/api/o6/archive/tasks/artifact-bundle-task-001")
        self.assertEqual(status, 200)
        detail_material = detail["task"]["live_camera_keyframe_annotation_material"]
        self.assertEqual(
            [detail_material[key] for key in ("task_id", "sha256", "topic", "stamp_sec", "stamp_nanosec", "width", "height", "encoding")],
            [material[key] for key in ("task_id", "sha256", "topic", "stamp_sec", "stamp_nanosec", "width", "height", "encoding")],
        )
        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=live_camera_keyframe_annotation_material",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["live_camera_keyframe_annotation_material"], material)

        # Algorithm 本轮 inventory blocked(1/0) 也走同一 section；保留来源计数，但绝不 annotation-ready。
        blocked_payload = self._artifact_bundle_payload()
        blocked_task_id = "task_o7_live_camera_keyframe_annotation_20260715_1158"
        blocked_payload["artifact_bundle"]["task_id"] = blocked_task_id
        blocked_manifest = self._live_camera_keyframe_annotation_material_payload(blocked_task_id)
        blocked_manifest.update(
            {
                "source_mode": "live_ros_graph_single_frame",
                "source_proof": "live_inventory_blocked",
                "topic": "",
                "publisher_count_at_inventory": 0,
                "stamp_sec": 0,
                "stamp_nanosec": 0,
                "width": 0,
                "height": 0,
                "step": 0,
                "encoding": "",
                "media_basename": "",
                "media_byte_size": 0,
                "sha256": "",
                "captured_at_utc": "",
                "inventory_ssh_invocation_count": 1,
                "single_frame_capture_invocation_count": 0,
                "redaction_boundary": {
                    **blocked_manifest["redaction_boundary"],
                    "classification": "metadata_only_pending_privacy_review",
                    "privacy_review_status": "pending_not_approved",
                },
                "annotation_ready": False,
                "blocked_reasons": ["inventory_ssh_or_payload_failed"],
                "not_proven": ["live_single_frame_captured", "privacy_approved"],
            }
        )
        blocked_payload["artifact_bundle"]["live_camera_keyframe_annotation_material"] = blocked_manifest
        status, blocked_created = self.client.request("POST", "/api/o6/archive/artifact-bundle", blocked_payload)
        self.assertEqual(status, 201)
        blocked_material = blocked_created["task"]["live_camera_keyframe_annotation_material"]
        self.assertEqual(blocked_material["status"], "blocked_not_proven")
        self.assertEqual(blocked_material["source_schema"], relay_module.LIVE_CAMERA_KEYFRAME_MANIFEST_SCHEMA)
        self.assertEqual(blocked_material["source_proof"], "live_inventory_blocked")
        self.assertEqual(blocked_material["task_id"], blocked_task_id)
        self.assertEqual(blocked_material["inventory_ssh_invocation_count"], 1)
        self.assertEqual(blocked_material["single_frame_capture_invocation_count"], 0)
        self.assertFalse(blocked_material["annotation_ready"])
        self.assertFalse(blocked_material["current_run_artifact_delta"])

        # hostile matrix 必须 section-local blocked，且响应不能回显原路径/URL/base64/raw pixels。
        hostile_cases = (
            ("absolute_path", lambda item: item.update({"media_path": "/tmp/private/frame.png"})),
            ("url_query", lambda item: item.update({"url": "https://example.test/frame.png?token=secret"})),
            ("data_url", lambda item: item.update({"data": "data:image/png;base64,AAAA"})),
            ("raw_pixels", lambda item: item.update({"pixels": [0, 1, 2, 3]})),
            ("hash", lambda item: item.update({"sha256": "bad"})),
            ("stamp", lambda item: item.update({"stamp_nanosec": 1_000_000_000})),
            ("task", lambda item: item.update({"task_id": "other-task"})),
            ("source_count", lambda item: item.update({"single_frame_capture_invocation_count": 1})),
            ("dangerous_true", lambda item: item.update({"delivery_success": True})),
        )
        for index, (name, mutate) in enumerate(hostile_cases):
            hostile = self._artifact_bundle_payload()
            hostile_task_id = f"camera-hostile-{name}-{index}"
            hostile["artifact_bundle"]["task_id"] = hostile_task_id
            section = self._live_camera_keyframe_annotation_material_payload(hostile_task_id)
            mutate(section)
            hostile["artifact_bundle"]["live_camera_keyframe_annotation_material"] = section
            status, blocked = self.client.request("POST", "/api/o6/archive/artifact-bundle", hostile)
            self.assertEqual(status, 201)
            blocked_material = blocked["task"]["live_camera_keyframe_annotation_material"]
            self.assertEqual(blocked_material["status"], "blocked_not_proven")
            self.assertEqual(blocked_material["source_badge"], "blocked")
            self.assertFalse(blocked_material["annotation_ready"])
            self.assertFalse(blocked_material["lineage_verified"])
            self.assertNotIn("/tmp/private", json.dumps(blocked, ensure_ascii=False))
            self.assertNotIn("example.test", json.dumps(blocked, ensure_ascii=False))
            self.assertNotIn("base64", json.dumps(blocked, ensure_ascii=False).lower())

    def test_o6_delivery_result_evidence_preserves_cloud_terminal_source_schema(self):
        # 云端终态结果是 Algorithm 转换后的 delivery_result_evidence 来源；O6 只能保留摘要，不能放宽控制边界。
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"]["task_id"] = "artifact-bundle-cloud-terminal-result-001"
        payload["artifact_bundle"]["delivery_result_evidence"].update(
            {
                "status": "ready_not_delivery_proof",
                "source": "cloud_command_terminal_result",
                "source_schema": "trashbot.cloud_command_terminal_result.v1",
                "record_status": "cloud_terminal_result_received_not_delivery_success",
                "dropoff_confirmation_type": "cloud_terminal_dropoff_terminal",
            }
        )

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            payload,
        )

        self.assertEqual(status, 201)

        def assert_cloud_terminal_evidence(section):
            # 这里集中校验三条读路径，防止以后某个 alias 漏掉 source_schema 或安全 false 字段。
            self.assertEqual(section["schema"], relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA)
            self.assertEqual(section["proof_scope"], relay_module.O6_DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE)
            self.assertEqual(section["source"], "cloud_command_terminal_result")
            self.assertEqual(section["source_schema"], "trashbot.cloud_command_terminal_result.v1")
            self.assertEqual(section["status"], "delivery_result_evidence_ready_not_delivery_proof")
            self.assertEqual(section["proof_scope"], "software_proof_delivery_result_evidence_only")
            self.assertEqual(section["record_status"], "cloud_terminal_result_received_not_delivery_success")
            self.assertTrue(section["record_present"])
            self.assertTrue(section["record_read_ok"])
            self.assertTrue(section["delivery_result_claimed"])
            self.assertTrue(section["operator_confirmation_present"])
            self.assertFalse(section["safe_to_control"])
            self.assertFalse(section["delivery_success"])
            self.assertFalse(section["primary_actions_enabled"])
            self.assertFalse(section["robot_control_executed"])

        assert_cloud_terminal_evidence(created["task"]["artifact_bundle"]["delivery_result_evidence"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/artifact-bundle-cloud-terminal-result-001",
            token="",
        )
        self.assertEqual(status, 200)
        assert_cloud_terminal_evidence(detail["task"]["delivery_result_evidence"])
        assert_cloud_terminal_evidence(detail["task"]["artifact_bundle"]["delivery_result_evidence"])
        assert_cloud_terminal_evidence(
            detail["task"]["artifact_bundle_consumer_ingest"]["delivery_result_evidence"]
        )

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-cloud-terminal-result-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        assert_cloud_terminal_evidence(consumer["delivery_result_evidence"])
        assert_cloud_terminal_evidence(consumer["artifact_bundle"]["delivery_result_evidence"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-cloud-terminal-result-001?include=delivery_result_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        assert_cloud_terminal_evidence(explicit["delivery_result_evidence"])

    def test_o6_field_motion_evidence_packet_missing_returns_blocked_summary(self):
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"].pop("field_motion_evidence_packet")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["field_motion_evidence_packet"]
        self.assertEqual(packet["schema"], relay_module.FIELD_MOTION_EVIDENCE_PACKET_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("field_motion_evidence_packet_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["field_motion_evidence_packet"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["field_motion_evidence_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "field_motion_evidence_packet_not_available",
            consumer["field_motion_evidence_packet"]["blocked_reasons"],
        )

    def test_o6_nav2_goal_execution_evidence_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("nav2_goal_execution_evidence")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]
        self.assertEqual(packet["schema"], relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("nav2_goal_execution_evidence_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["nav2_goal_execution_evidence"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["nav2_goal_execution_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "nav2_goal_execution_evidence_not_available",
            consumer["nav2_goal_execution_evidence"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-nav2-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["nav2_goal_execution_evidence"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_scope_created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "nav2_goal_execution_evidence_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["blocked_reasons"],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-nav2-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["nav2_goal_execution_evidence"]["source"] = "/tmp/root/nav2.log"
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "nav2_goal_execution_evidence_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]["blocked_reasons"],
        )
        self.assertNotIn("/tmp/root", json.dumps(unsafe_text_created, ensure_ascii=False))

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-nav2-unsafe-001"
        unsafe_payload["artifact_bundle"]["nav2_goal_execution_evidence"]["source"] = "/tmp/root/nav2.log?token=secret"
        unsafe_payload["artifact_bundle"]["nav2_goal_execution_evidence"]["robot_control_executed"] = True
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )

        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["nav2_goal_execution_evidence"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("nav2_goal_execution_evidence_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("/tmp/root", encoded)
        self.assertNotIn("token=secret", encoded)
        self.assertFalse(unsafe_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-nav2-unsafe-001?include=nav2_goal_execution_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["nav2_goal_execution_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "nav2_goal_execution_evidence_dangerous_true",
            explicit["nav2_goal_execution_evidence"]["blocked_reasons"],
        )

    def test_o6_delivery_result_evidence_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("delivery_result_evidence")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["delivery_result_evidence"]
        self.assertEqual(packet["schema"], relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("delivery_result_evidence_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["delivery_result_evidence"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["delivery_result_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "delivery_result_evidence_not_available",
            consumer["delivery_result_evidence"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-delivery-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["delivery_result_evidence"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_scope_created["task"]["artifact_bundle"]["delivery_result_evidence"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "delivery_result_evidence_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["delivery_result_evidence"]["blocked_reasons"],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-delivery-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["delivery_result_evidence"]["source"] = "/tmp/root/delivery.json"
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["delivery_result_evidence"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "delivery_result_evidence_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["delivery_result_evidence"]["blocked_reasons"],
        )
        self.assertNotIn("/tmp/root", json.dumps(unsafe_text_created, ensure_ascii=False))

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-delivery-unsafe-001"
        unsafe_payload["artifact_bundle"]["delivery_result_evidence"]["source_schema"] = (
            "https://example.test/delivery?token=secret"
        )
        unsafe_payload["artifact_bundle"]["delivery_result_evidence"]["robot_control_executed"] = True
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )

        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["delivery_result_evidence"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("delivery_result_evidence_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("token=secret", encoded)
        self.assertFalse(unsafe_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-delivery-unsafe-001?include=delivery_result_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["delivery_result_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "delivery_result_evidence_dangerous_true",
            explicit["delivery_result_evidence"]["blocked_reasons"],
        )

    def test_o6_route_execution_result_delivery_readiness_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_execution_result_delivery_readiness")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn(
            "route_execution_result_delivery_readiness_not_available",
            packet["blocked_reasons"],
        )
        self.assertEqual(packet["next_required_evidence"], ["route_execution_result_delivery_readiness"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_execution_result_delivery_readiness"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_execution_result_delivery_readiness_not_available",
            consumer["route_execution_result_delivery_readiness"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-result-readiness-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_execution_result_delivery_readiness"][
            "proof_scope"
        ] = "wrong_scope"
        bad_scope_payload["artifact_bundle"]["route_execution_result_delivery_readiness"]["task_id"] = (
            "artifact-bundle-result-readiness-bad-scope-001"
        )
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_scope_created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_execution_result_delivery_readiness_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-result-readiness-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["route_execution_result_delivery_readiness"]["task_id"] = (
            "artifact-bundle-result-readiness-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["route_execution_result_delivery_readiness"][
            "route_execution_result_source"
        ] = "/tmp/root/nav2-result.json"
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"][
                "status"
            ],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_execution_result_delivery_readiness_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/root", json.dumps(unsafe_text_created, ensure_ascii=False))

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-result-readiness-unsafe-001"
        unsafe_payload["artifact_bundle"]["route_execution_result_delivery_readiness"]["task_id"] = (
            "artifact-bundle-result-readiness-unsafe-001"
        )
        unsafe_payload["artifact_bundle"]["route_execution_result_delivery_readiness"][
            "route_execution_success"
        ] = True
        unsafe_payload["artifact_bundle"]["route_execution_result_delivery_readiness"][
            "robot_control_executed"
        ] = True
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )

        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn(
            "route_execution_result_delivery_readiness_dangerous_true",
            unsafe_packet["blocked_reasons"],
        )
        self.assertNotIn("route_execution_success\": true", encoded)
        self.assertFalse(unsafe_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-result-readiness-unsafe-001?include=route_execution_result_delivery_readiness",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            explicit["route_execution_result_delivery_readiness"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_execution_result_delivery_readiness_dangerous_true",
            explicit["route_execution_result_delivery_readiness"]["blocked_reasons"],
        )

    def test_o6_route_delivery_closure_packet_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_delivery_closure_packet")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_delivery_closure_packet"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("route_delivery_closure_packet_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["route_delivery_closure_packet"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=route_delivery_closure_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_delivery_closure_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_delivery_closure_packet_not_available",
            consumer["route_delivery_closure_packet"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-closure-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_delivery_closure_packet"]["task_id"] = (
            "artifact-bundle-closure-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["route_delivery_closure_packet"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_scope_created["task"]["artifact_bundle"]["route_delivery_closure_packet"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_delivery_closure_packet_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["route_delivery_closure_packet"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-closure-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["route_delivery_closure_packet"]["task_id"] = (
            "artifact-bundle-closure-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["route_delivery_closure_packet"]["source"] = (
            "/tmp/root/closure.json"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["route_delivery_closure_packet"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_delivery_closure_packet_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["route_delivery_closure_packet"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/root", json.dumps(unsafe_text_created, ensure_ascii=False))

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-closure-unsafe-001"
        unsafe_payload["artifact_bundle"]["route_delivery_closure_packet"]["task_id"] = (
            "artifact-bundle-closure-unsafe-001"
        )
        unsafe_payload["artifact_bundle"]["route_delivery_closure_packet"]["delivery_success"] = True
        unsafe_payload["artifact_bundle"]["route_delivery_closure_packet"]["robot_control_executed"] = True
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )

        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["route_delivery_closure_packet"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn(
            "route_delivery_closure_packet_dangerous_true",
            unsafe_packet["blocked_reasons"],
        )
        self.assertNotIn("delivery_success\": true", encoded)
        self.assertFalse(unsafe_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-closure-unsafe-001?include=route_delivery_closure_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_delivery_closure_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_delivery_closure_packet_dangerous_true",
            explicit["route_delivery_closure_packet"]["blocked_reasons"],
        )

    def test_o6_same_task_mission_evidence_gate_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("same_task_mission_evidence_gate")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]
        self.assertEqual(packet["schema"], relay_module.O6_SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("same_task_mission_evidence_gate_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["same_task_mission_evidence_gate"])
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=same_task_mission_evidence_gate",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["same_task_mission_evidence_gate"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_mission_evidence_gate_not_available",
            consumer["same_task_mission_evidence_gate"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = (
            "artifact-bundle-same-task-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["schema"] = (
            "trashbot.bad_same_task_gate.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            bad_schema_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "same_task_mission_evidence_gate_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = (
            "artifact-bundle-same-task-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_mission_evidence_gate_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"][
                "blocked_reasons"
            ],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            task_mismatch_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "same_task_mission_evidence_gate_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = (
            "artifact-bundle-same-task-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["source"] = (
            "/tmp/root/same-task-gate.json"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_mission_evidence_gate"][
            "raw_payload_base64"
        ] = "QUJDREVGRw=="
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "same_task_mission_evidence_gate_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"][
                "blocked_reasons"
            ],
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertNotIn("/tmp/root", encoded_unsafe_text)
        self.assertNotIn("QUJDREVGRw==", encoded_unsafe_text)

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-unsafe-001"
        unsafe_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = (
            "artifact-bundle-same-task-unsafe-001"
        )
        unsafe_payload["artifact_bundle"]["same_task_mission_evidence_gate"][
            "terminal_refs"
        ] = ["https://example.test/gate.json?token=secret"]
        unsafe_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["delivery_success"] = True
        unsafe_payload["artifact_bundle"]["same_task_mission_evidence_gate"]["robot_control_executed"] = True
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )

        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("same_task_mission_evidence_gate_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("token=secret", encoded)
        self.assertNotIn("delivery_success\": true", encoded)
        self.assertFalse(unsafe_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-same-task-unsafe-001?include=same_task_mission_evidence_gate",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["same_task_mission_evidence_gate"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_mission_evidence_gate_dangerous_true",
            explicit["same_task_mission_evidence_gate"]["blocked_reasons"],
        )

    def test_o6_same_task_mission_evidence_gate_allows_credit_only_for_live_or_field_same_task_input(self):
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"]["task_id"] = "artifact-bundle-same-task-credit-001"
        payload["artifact_bundle"]["same_task_mission_evidence_gate"]["task_id"] = (
            "artifact-bundle-same-task-credit-001"
        )
        payload["artifact_bundle"]["same_task_mission_evidence_gate"]["mission_artifact_delta"] = {
            "same_task_id_consumed": True,
            "cloud_terminal_result_source_consumed": True,
            "route_execution_readiness_consumed": True,
            "route_delivery_closure_consumed": True,
            "nonzero_pose_progress_consumed": True,
            "live_or_field_command_executed": True,
            "okr_credit_allowed": True,
        }
        payload["artifact_bundle"]["same_task_mission_evidence_gate"]["live_or_field_command_executed"] = True
        payload["artifact_bundle"]["same_task_mission_evidence_gate"]["okr_credit_allowed"] = True
        payload["artifact_bundle"]["same_task_mission_evidence_gate"].pop("support_only_reason", None)

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            payload,
        )

        self.assertEqual(status, 201)
        gate = created["task"]["artifact_bundle"]["same_task_mission_evidence_gate"]
        self.assertEqual(gate["status"], "same_task_mission_gate_ready_not_success_proof")
        self.assertTrue(gate["same_task_id_consumed"])
        self.assertTrue(gate["live_or_field_command_executed"])
        self.assertTrue(gate["okr_credit_allowed"])
        self.assertEqual(gate["support_only_reason"], "")

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-same-task-credit-001?include=same_task_mission_evidence_gate",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertTrue(explicit["same_task_mission_evidence_gate"]["okr_credit_allowed"])
        self.assertTrue(explicit["same_task_mission_evidence_gate"]["live_or_field_command_executed"])

    def test_o6_same_task_field_material_packet_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("same_task_field_material_packet")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_field_material_packet"]
        self.assertEqual(packet["schema"], relay_module.O6_SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("same_task_field_material_packet_not_available", packet["blocked_reasons"])
        self.assertEqual(
            packet["next_required_evidence"],
            ["same_task_field_material_packet", "map_yaml_material_optional"],
        )
        self.assertFalse(packet["safe_to_control"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=same_task_field_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["same_task_field_material_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_field_material_packet_not_available",
            consumer["same_task_field_material_packet"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-material-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-material-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["same_task_field_material_packet"]["schema"] = (
            "trashbot.bad_same_task_field_material_packet.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_field_material_packet_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["same_task_field_material_packet"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-material-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-material-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["same_task_field_material_packet"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_field_material_packet_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["same_task_field_material_packet"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-material-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-material-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_field_material_packet"]["source"] = (
            "/tmp/field_material_packet.json"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_field_material_packet"]["raw_payload_base64"] = (
            "QUJDREVGRw=="
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_field_material_packet_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["same_task_field_material_packet"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/field_material_packet.json", encoded_unsafe_text)
        self.assertNotIn("QUJDREVGRw==", encoded_unsafe_text)

        unsafe_ref_payload = self._artifact_bundle_payload()
        unsafe_ref_payload["artifact_bundle"]["task_id"] = "artifact-bundle-material-unsafe-ref-001"
        unsafe_ref_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-material-unsafe-ref-001"
        )
        unsafe_ref_payload["artifact_bundle"]["same_task_field_material_packet"]["sample_refs"][0] = (
            "https://example.test/route.csv?token=secret"
        )
        unsafe_ref_payload["artifact_bundle"]["same_task_field_material_packet"]["delivery_success"] = True
        status, unsafe_ref_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_ref_payload,
        )
        encoded = json.dumps(unsafe_ref_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_ref_created["task"]["artifact_bundle"]["same_task_field_material_packet"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("same_task_field_material_packet_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("token=secret", encoded)
        self.assertFalse(unsafe_packet["delivery_success"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-material-unsafe-ref-001?include=same_task_field_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["same_task_field_material_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_field_material_packet_dangerous_true",
            explicit["same_task_field_material_packet"]["blocked_reasons"],
        )

    def test_o6_same_task_field_material_packet_accepts_algorithm_material_summaries_shape(self):
        payload = self._artifact_bundle_payload()
        payload["artifact_bundle"]["task_id"] = "artifact-bundle-material-actual-shape-001"
        payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-material-actual-shape-001"
        )
        payload["artifact_bundle"]["same_task_field_material_packet"]["present_materials"] = [
            "route_csv",
            "keyframes",
            "route_bag_or_rosbag",
            "replay_jsonl",
        ]
        payload["artifact_bundle"]["same_task_field_material_packet"]["missing_materials"] = ["map_yaml"]
        payload["artifact_bundle"]["same_task_field_material_packet"]["sample_refs"] = [
            "captures/route.csv",
            "captures/keyframes/keyframe-0001.jpg",
            "captures/route_001.db3",
            "captures/fixed_route_replay.jsonl",
        ]
        payload["artifact_bundle"]["same_task_field_material_packet"]["material_summaries"] = {
            "map_yaml": {"present": False, "count": 0, "sample_refs": []},
            "route_csv": {
                "present": True,
                "basename": "route.csv",
                "size_bytes": 128,
                "sha256_prefix": "1234567890abcdef",
                "count": 1,
                "sample_refs": ["captures/route.csv"],
            },
            "keyframes": {
                "present": True,
                "basename": "keyframe-0001.jpg",
                "size_bytes": 2048,
                "sha256_prefix": "abcdef1234567890",
                "count": 17,
                "sample_refs": ["captures/keyframes/keyframe-0001.jpg"],
            },
            "route_bag_or_rosbag": {
                "present": True,
                "basename": "route_001.db3",
                "size_bytes": 4096,
                "sha256_prefix": "1122334455667788",
                "count": 1,
                "sample_refs": ["captures/route_001.db3"],
            },
            "replay_jsonl": {
                "present": True,
                "basename": "fixed_route_replay.jsonl",
                "size_bytes": 512,
                "sha256_prefix": "aabbccddeeff0011",
                "count": 1,
                "sample_refs": ["captures/fixed_route_replay.jsonl"],
            },
        }

        status, created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_field_material_packet"]
        self.assertEqual(packet["status"], "ready_not_delivery_proof")
        self.assertFalse(packet["map_yaml_present"])
        self.assertEqual(packet["counts"]["missing_material_count"], 1)
        self.assertEqual(packet["sample_refs"], ["route.csv", "keyframe-0001.jpg", "route_001.db3", "fixed_route_replay.jsonl"])
        self.assertEqual(packet["material_sample_refs"]["route_csv"]["basename"], "route.csv")
        self.assertEqual(packet["material_sample_refs"]["keyframes"]["count"], 17)
        self.assertIn("same_task_field_material_map_yaml_missing_optional", packet["blocked_reasons"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-material-actual-shape-001?include=same_task_field_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["same_task_field_material_packet"]["status"], "ready_not_delivery_proof")
        self.assertEqual(
            explicit["same_task_field_material_packet"]["material_sample_refs"]["route_bag_or_rosbag"][
                "basename"
            ],
            "route_001.db3",
        )

    def test_o6_current_field_evidence_material_in_field_and_bundle_readback(self):
        field_payload = self._field_evidence_archive_request_payload()
        status, field_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            field_payload,
        )

        self.assertEqual(status, 201)
        field_section = field_created["task"]["field_evidence"]["current_field_evidence_material"]
        self.assertEqual(field_section["schema"], relay_module.O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA)
        self.assertEqual(field_section["status"], "current_field_evidence_ready_not_route_execution_proof")
        self.assertEqual(field_section["present_materials"], ["camera_frame", "radar_scan", "nav2_no_motion_path", "manual_gate"])
        self.assertEqual(field_section["missing_materials"], ["map_material"])
        self.assertTrue(field_section["camera_frame_observed"])
        self.assertTrue(field_section["radar_scan_observed"])
        self.assertFalse(field_section["map_material_observed"])
        self.assertTrue(field_section["nav2_no_motion_path_generated"])
        self.assertTrue(field_section["manual_gate_blocked_expected"])
        self.assertTrue(field_section["live_or_field_material_consumed"])
        self.assertTrue(field_section["current_field_evidence_ready_not_route_execution_proof"])
        self.assertIn("real_route_execution_trace_missing", field_section["blocked_reasons"])

        legacy_payload = self._field_evidence_archive_request_payload()
        legacy_payload["task_id"] = "field-evidence-field-run-legacy-001"
        legacy_payload["field_evidence_manifest"]["task_id"] = "field-evidence-field-run-legacy-001"
        legacy_payload["current_field_evidence_material"]["task_id"] = "field-evidence-field-run-legacy-001"
        legacy_payload["current_field_evidence_material"]["status"] = (
            "current_field_evidence_material_ready_not_route_execution_proof"
        )
        status, legacy_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            legacy_payload,
        )
        self.assertEqual(status, 201)
        legacy_section = legacy_created["task"]["field_evidence"]["current_field_evidence_material"]
        self.assertEqual(legacy_section["status"], "current_field_evidence_ready_not_route_execution_proof")
        self.assertTrue(legacy_section["current_field_evidence_ready_not_route_execution_proof"])

        status, field_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,current_field_evidence_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            field_consumer["current_field_evidence_material"]["status"],
            "current_field_evidence_ready_not_route_execution_proof",
        )
        self.assertEqual(
            field_consumer["current_field_evidence_material"]["missing_materials"],
            ["map_material"],
        )
        self.assertEqual(
            field_consumer["field_evidence_consumer_ingest"]["current_field_evidence_material"]["status"],
            "current_field_evidence_ready_not_route_execution_proof",
        )

        bundle_payload = self._artifact_bundle_payload()
        bundle_payload["artifact_bundle"]["pc_live_nav2_execution_material"] = (
            self._pc_live_nav2_execution_material_legacy_payload("artifact-bundle-task-001")
        )
        bundle_status, bundle_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bundle_payload,
        )

        self.assertEqual(bundle_status, 201)
        bundle_section = bundle_created["task"]["artifact_bundle"]["current_field_evidence_material"]
        self.assertEqual(bundle_section["schema"], relay_module.O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA)
        self.assertEqual(bundle_section["status"], "current_field_evidence_ready_not_route_execution_proof")
        self.assertTrue(bundle_section["manual_gate_blocked_expected"])

        status, bundle_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,current_field_evidence_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            bundle_consumer["current_field_evidence_material"]["status"],
            "current_field_evidence_ready_not_route_execution_proof",
        )
        self.assertEqual(
            bundle_consumer["current_field_evidence_material"]["present_materials"],
            ["camera_frame", "radar_scan", "nav2_no_motion_path", "manual_gate"],
        )
        self.assertEqual(
            bundle_consumer["artifact_bundle_consumer_ingest"]["current_field_evidence_material"]["status"],
            "current_field_evidence_ready_not_route_execution_proof",
        )

    def test_o6_current_field_evidence_material_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("current_field_evidence_material")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["current_field_evidence_material"]
        self.assertEqual(packet["schema"], relay_module.O6_CURRENT_FIELD_EVIDENCE_MATERIAL_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("current_field_evidence_material_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["current_field_evidence_material"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])
        self.assertFalse(packet["robot_control_executed"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,current_field_evidence_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["current_field_evidence_material"]["status"], "blocked_not_proven")
        self.assertIn(
            "current_field_evidence_material_not_available",
            consumer["current_field_evidence_material"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-current-material-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["current_field_evidence_material"]["task_id"] = (
            "artifact-bundle-current-material-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["current_field_evidence_material"]["schema"] = (
            "trashbot.bad_current_field_evidence_material.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "current_field_evidence_material_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["current_field_evidence_material"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-current-material-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["current_field_evidence_material"]["task_id"] = (
            "artifact-bundle-current-material-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["current_field_evidence_material"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "current_field_evidence_material_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["current_field_evidence_material"]["blocked_reasons"],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-current-material-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["current_field_evidence_material"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            task_mismatch_created["task"]["artifact_bundle"]["current_field_evidence_material"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "current_field_evidence_material_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["current_field_evidence_material"]["blocked_reasons"],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-current-material-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["current_field_evidence_material"]["task_id"] = (
            "artifact-bundle-current-material-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["current_field_evidence_material"]["source"] = (
            "/tmp/current_field_evidence_material.json"
        )
        unsafe_text_payload["artifact_bundle"]["current_field_evidence_material"]["response_body"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "current_field_evidence_material_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["current_field_evidence_material"]["blocked_reasons"],
        )
        self.assertNotIn("/tmp/current_field_evidence_material.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-current-material-dangerous-001"
        dangerous_payload["artifact_bundle"]["current_field_evidence_material"]["task_id"] = (
            "artifact-bundle-current-material-dangerous-001"
        )
        dangerous_payload["artifact_bundle"]["current_field_evidence_material"]["delivery_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["current_field_evidence_material"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("current_field_evidence_material_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["delivery_success"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-current-material-dangerous-001?include=field_evidence,current_field_evidence_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["current_field_evidence_material"]["status"], "blocked_not_proven")
        self.assertIn(
            "current_field_evidence_material_dangerous_true",
            explicit["current_field_evidence_material"]["blocked_reasons"],
        )

    def test_o6_field_operator_confirmation_material_in_field_and_bundle_readback(self):
        field_payload = self._field_evidence_archive_request_payload()
        status, field_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            field_payload,
        )

        self.assertEqual(status, 201)
        field_section = field_created["task"]["field_evidence"]["field_operator_confirmation_material"]
        self.assertEqual(field_section["schema"], relay_module.O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA)
        self.assertEqual(
            field_section["status"],
            "field_operator_confirmation_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            field_section["proof_scope"],
            relay_module.O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_PROOF_SCOPE,
        )
        self.assertTrue(field_section["operator_report_present"])
        self.assertEqual(field_section["operator_report_status"], "operator_report_ready")
        self.assertTrue(field_section["operator_confirmation_present"])
        self.assertEqual(field_section["operator_confirmation_status"], "operator_confirmation_ready")
        self.assertTrue(field_section["operator_present"])
        self.assertTrue(field_section["physical_clearance_confirmed"])
        self.assertTrue(field_section["emergency_stop_ready"])
        self.assertTrue(field_section["observed_motion"])
        self.assertTrue(field_section["observed_stop"])
        self.assertTrue(field_section["same_task_id_consumed"])
        self.assertTrue(field_section["linked_route_material_present"])
        self.assertTrue(field_section["linked_delivery_material_present"])
        self.assertTrue(field_section["operator_material_consumed"])
        self.assertEqual(field_section["material_summaries"]["operator_report"]["basename"], "operator_report.json")
        self.assertFalse(field_section["delivery_success"])
        self.assertFalse(field_section["safe_to_control"])
        self.assertFalse(field_section["route_execution_success"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/field-evidence-field-run-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["field_operator_confirmation_material"]["status"],
            "field_operator_confirmation_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["field_operator_confirmation_material"][
                "reported_at"
            ],
            "2026-07-10T07:22:00Z",
        )

        status, field_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,field_operator_confirmation_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            field_consumer["field_operator_confirmation_material"]["status"],
            "field_operator_confirmation_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            field_consumer["field_operator_confirmation_material"]["material_summaries"][
                "operator_confirmation"
            ]["basename"],
            "operator_confirmation.json",
        )
        self.assertEqual(
            field_consumer["field_evidence_consumer_ingest"]["field_operator_confirmation_material"]["status"],
            "field_operator_confirmation_material_ready_not_delivery_proof",
        )

        bundle_payload = self._artifact_bundle_payload()
        bundle_status, bundle_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bundle_payload,
        )

        self.assertEqual(bundle_status, 201)
        bundle_section = bundle_created["task"]["artifact_bundle"]["field_operator_confirmation_material"]
        self.assertEqual(bundle_section["schema"], relay_module.O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA)
        self.assertTrue(bundle_section["linked_delivery_material_present"])

        status, bundle_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,field_operator_confirmation_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            bundle_consumer["field_operator_confirmation_material"]["status"],
            "field_operator_confirmation_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            bundle_consumer["artifact_bundle_consumer_ingest"]["field_operator_confirmation_material"][
                "material_summaries"
            ]["delivery_material"]["basename"],
            "delivery_result_evidence.json",
        )

    def test_o6_field_operator_confirmation_material_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("field_operator_confirmation_material")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["field_operator_confirmation_material"]
        self.assertEqual(packet["schema"], relay_module.O6_FIELD_OPERATOR_CONFIRMATION_MATERIAL_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("field_operator_confirmation_material_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["field_operator_confirmation_material"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_operator_confirmation_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["field_operator_confirmation_material"]["status"], "blocked_not_proven")
        self.assertIn(
            "field_operator_confirmation_material_not_available",
            consumer["field_operator_confirmation_material"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = (
            "artifact-bundle-operator-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["field_operator_confirmation_material"]["schema"] = (
            "trashbot.bad_field_operator_confirmation_material.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "field_operator_confirmation_material_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["field_operator_confirmation_material"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = (
            "artifact-bundle-operator-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["field_operator_confirmation_material"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "field_operator_confirmation_material_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["field_operator_confirmation_material"][
                "blocked_reasons"
            ],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "field_operator_confirmation_material_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["field_operator_confirmation_material"][
                "blocked_reasons"
            ],
        )

        missing_field_payload = self._artifact_bundle_payload()
        missing_field_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-missing-field-001"
        missing_field_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = (
            "artifact-bundle-operator-missing-field-001"
        )
        missing_field_payload["artifact_bundle"]["field_operator_confirmation_material"].pop("reported_at")
        status, missing_field_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_field_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "field_operator_confirmation_material_reported_at_missing",
            missing_field_created["task"]["artifact_bundle"]["field_operator_confirmation_material"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = (
            "artifact-bundle-operator-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["field_operator_confirmation_material"]["source"] = (
            "/tmp/operator_confirmation_material.json"
        )
        unsafe_text_payload["artifact_bundle"]["field_operator_confirmation_material"]["raw_report"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "field_operator_confirmation_material_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["field_operator_confirmation_material"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/operator_confirmation_material.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-operator-dangerous-001"
        dangerous_payload["artifact_bundle"]["field_operator_confirmation_material"]["task_id"] = (
            "artifact-bundle-operator-dangerous-001"
        )
        dangerous_payload["artifact_bundle"]["field_operator_confirmation_material"]["delivery_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["field_operator_confirmation_material"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("field_operator_confirmation_material_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["delivery_success"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-operator-dangerous-001?include=field_operator_confirmation_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["field_operator_confirmation_material"]["status"], "blocked_not_proven")
        self.assertIn(
            "field_operator_confirmation_material_dangerous_true",
            explicit["field_operator_confirmation_material"]["blocked_reasons"],
        )

    def test_o6_clean_baseline_nav2_path_material_in_field_and_bundle_readback(self):
        field_payload = self._field_evidence_archive_request_payload()
        status, field_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            field_payload,
        )

        self.assertEqual(status, 201)
        field_section = field_created["task"]["field_evidence"]["clean_baseline_nav2_path_material"]
        self.assertEqual(field_section["schema"], relay_module.O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA)
        self.assertEqual(
            field_section["status"],
            "clean_baseline_nav2_path_material_ready_not_route_execution_proof",
        )
        self.assertEqual(field_section["first_attempt_status"], "tf_root_cause_blocked")
        self.assertEqual(field_section["retry_status"], "path_generated_after_retry")
        self.assertEqual(field_section["path_point_count"], 31)
        self.assertTrue(field_section["cleanup_readback_clean"])
        self.assertEqual(
            field_section["material_sample_refs"]["refresh_summary"]["basename"],
            "clean_baseline_nav2_refresh_summary.json",
        )
        self.assertIn("real_route_execution_trace_missing", field_section["blocked_reasons"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/field-evidence-field-run-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["clean_baseline_nav2_path_material"]["status"],
            "clean_baseline_nav2_path_material_ready_not_route_execution_proof",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["clean_baseline_nav2_path_material"]["path_point_count"],
            31,
        )

        status, field_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,clean_baseline_nav2_path_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            field_consumer["clean_baseline_nav2_path_material"]["status"],
            "clean_baseline_nav2_path_material_ready_not_route_execution_proof",
        )
        self.assertEqual(
            field_consumer["field_evidence_consumer_ingest"]["clean_baseline_nav2_path_material"]["retry_status"],
            "path_generated_after_retry",
        )

        bundle_payload = self._artifact_bundle_payload()
        bundle_status, bundle_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bundle_payload,
        )

        self.assertEqual(bundle_status, 201)
        bundle_section = bundle_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]
        self.assertEqual(bundle_section["schema"], relay_module.O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA)
        self.assertTrue(bundle_section["path_generated"])
        self.assertTrue(bundle_section["managed_runtime_cleanup_ok"])

        status, bundle_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,clean_baseline_nav2_path_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            bundle_consumer["clean_baseline_nav2_path_material"]["path_point_count"],
            31,
        )
        self.assertEqual(
            bundle_consumer["artifact_bundle_consumer_ingest"]["clean_baseline_nav2_path_material"]["material_sample_refs"]["status_artifact"]["basename"],
            "clean_baseline_nav2_status.json",
        )

    def test_o6_clean_baseline_nav2_path_material_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("clean_baseline_nav2_path_material")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]
        self.assertEqual(packet["schema"], relay_module.O6_CLEAN_BASELINE_NAV2_PATH_MATERIAL_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("clean_baseline_nav2_path_material_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["clean_baseline_nav2_path_material"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=clean_baseline_nav2_path_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["clean_baseline_nav2_path_material"]["status"], "blocked_not_proven")

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-clean-baseline-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["task_id"] = (
            "artifact-bundle-clean-baseline-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["schema"] = (
            "trashbot.bad_clean_baseline_nav2_path_material.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "clean_baseline_nav2_path_material_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-clean-baseline-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["task_id"] = (
            "artifact-bundle-clean-baseline-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "clean_baseline_nav2_path_material_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]["blocked_reasons"],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-clean-baseline-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "clean_baseline_nav2_path_material_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]["blocked_reasons"],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-clean-baseline-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["task_id"] = (
            "artifact-bundle-clean-baseline-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["source"] = (
            "/tmp/clean_baseline_nav2_path_material.json"
        )
        unsafe_text_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["response_body"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "clean_baseline_nav2_path_material_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]["blocked_reasons"],
        )
        self.assertNotIn("/tmp/clean_baseline_nav2_path_material.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-clean-baseline-dangerous-001"
        dangerous_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["task_id"] = (
            "artifact-bundle-clean-baseline-dangerous-001"
        )
        dangerous_payload["artifact_bundle"]["clean_baseline_nav2_path_material"]["delivery_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["clean_baseline_nav2_path_material"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("clean_baseline_nav2_path_material_dangerous_true", dangerous_packet["blocked_reasons"])

    def test_o6_pc_live_nav2_execution_material_in_field_and_bundle_readback(self):
        field_payload = self._field_evidence_archive_request_payload()
        status, field_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            field_payload,
        )

        self.assertEqual(status, 201)
        field_section = field_created["task"]["field_evidence"]["pc_live_nav2_execution_material"]
        self.assertEqual(field_section["schema"], relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA)
        self.assertEqual(
            field_section["proof_scope"],
            relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_PROOF_SCOPE,
        )
        self.assertEqual(
            field_section["status"],
            "pc_live_nav2_execution_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            field_section["source_sprint"],
            "2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias",
        )
        self.assertTrue(field_section["goal_accepted"])
        self.assertTrue(field_section["cancel_accepted"])
        self.assertTrue(field_section["uses_base_uart"])
        self.assertTrue(field_section["base_command_nonzero_observed"])
        self.assertEqual(field_section["base_command_nonzero_count"], 733)
        self.assertEqual(field_section["base_feedback_sample_count"], 5941)
        self.assertFalse(field_section["base_feedback_lr_nonzero_proven"])
        self.assertTrue(field_section["base_feedback_imu_attitude_delta_observed"])
        self.assertEqual(field_section["goal_result_status"], "goal_timeout_cancel_requested")
        self.assertEqual(field_section["result_status"], "goal_timeout_cancel_requested")
        self.assertFalse(field_section["delivery_success"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/field-evidence-field-run-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["pc_live_nav2_execution_material"]["status"],
            "pc_live_nav2_execution_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["pc_live_nav2_execution_material"][
                "base_feedback_sample_count"
            ],
            5941,
        )

        status, field_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,pc_live_nav2_execution_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            field_consumer["pc_live_nav2_execution_material"]["status"],
            "pc_live_nav2_execution_material_ready_not_delivery_proof",
        )
        self.assertEqual(
            field_consumer["field_evidence_consumer_ingest"]["pc_live_nav2_execution_material"][
                "base_command_nonzero_count"
            ],
            733,
        )

        bundle_payload = self._artifact_bundle_payload()
        bundle_status, bundle_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bundle_payload,
        )

        self.assertEqual(bundle_status, 201)
        bundle_section = bundle_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"]
        self.assertEqual(bundle_section["schema"], relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA)
        self.assertTrue(bundle_section["goal_accepted"])
        self.assertEqual(bundle_section["goal_result_status"], "goal_timeout_cancel_requested")
        self.assertEqual(bundle_section["result_status"], "goal_timeout_cancel_requested")
        self.assertFalse(bundle_section["base_feedback_lr_nonzero_proven"])

        status, bundle_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,pc_live_nav2_execution_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            bundle_consumer["pc_live_nav2_execution_material"]["base_feedback_sample_count"],
            5941,
        )
        self.assertEqual(
            bundle_consumer["pc_live_nav2_execution_material"]["goal_result_status"],
            "goal_timeout_cancel_requested",
        )
        self.assertEqual(
            bundle_consumer["artifact_bundle_consumer_ingest"]["pc_live_nav2_execution_material"][
                "result_status"
            ],
            "goal_timeout_cancel_requested",
        )

    def test_o6_pc_live_nav2_execution_material_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("pc_live_nav2_execution_material")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"]
        self.assertEqual(packet["schema"], relay_module.O6_PC_LIVE_NAV2_EXECUTION_MATERIAL_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("pc_live_nav2_execution_material_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["pc_live_nav2_execution_material"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=pc_live_nav2_execution_material",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["pc_live_nav2_execution_material"]["status"], "blocked_not_proven")

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pc-live-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["task_id"] = (
            "artifact-bundle-pc-live-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["schema"] = (
            "trashbot.bad_pc_live_nav2_execution_material.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "pc_live_nav2_execution_material_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pc-live-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["task_id"] = (
            "artifact-bundle-pc-live-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "pc_live_nav2_execution_material_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"][
                "blocked_reasons"
            ],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pc-live-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "pc_live_nav2_execution_material_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pc-live-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["task_id"] = (
            "artifact-bundle-pc-live-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["source"] = (
            "/tmp/pc_live_nav2_execution_material.json"
        )
        unsafe_text_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["response_body"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "pc_live_nav2_execution_material_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/pc_live_nav2_execution_material.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-pc-live-dangerous-001"
        dangerous_payload["artifact_bundle"]["pc_live_nav2_execution_material"]["task_id"] = (
            "artifact-bundle-pc-live-dangerous-001"
        )
        dangerous_payload["artifact_bundle"]["pc_live_nav2_execution_material"][
            "base_feedback_lr_nonzero_proven"
        ] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["pc_live_nav2_execution_material"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn(
            "pc_live_nav2_execution_material_wheel_lr_nonzero_claimed",
            dangerous_packet["blocked_reasons"],
        )
        self.assertFalse(dangerous_packet["base_feedback_lr_nonzero_proven"])

    def test_o6_localization_path_material_readback_in_field_and_bundle_readback(self):
        field_payload = self._field_evidence_archive_request_payload()
        status, field_created = self.client.request(
            "POST",
            "/api/o6/archive/field-evidence",
            field_payload,
        )

        self.assertEqual(status, 201)
        field_section = field_created["task"]["field_evidence"]["localization_path_material_readback"]
        self.assertEqual(field_section["schema"], relay_module.O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA)
        self.assertEqual(
            field_section["proof_scope"],
            relay_module.O6_LOCALIZATION_PATH_MATERIAL_READBACK_PROOF_SCOPE,
        )
        self.assertEqual(
            field_section["status"],
            "localization_path_material_readback_ready_not_route_execution_proof",
        )
        self.assertTrue(field_section["localization_path_material_bridge_present"])
        self.assertTrue(field_section["same_run_localization_material_present"])
        self.assertTrue(field_section["same_run_map_once_observed"])
        self.assertTrue(field_section["same_run_amcl_pose_observed"])
        self.assertTrue(field_section["same_run_localization_tf_map_to_odom"])
        self.assertTrue(field_section["same_run_localization_tf_map_to_base_link"])
        self.assertTrue(field_section["same_run_tf_map_to_odom_observed"])
        self.assertTrue(field_section["same_run_tf_map_to_base_link_observed"])
        self.assertTrue(field_section["same_run_path_generation_requested"])
        self.assertFalse(field_section["same_run_path_generation_succeeded"])
        self.assertFalse(field_section["same_run_path_generated"])
        self.assertEqual(field_section["same_run_path_point_count"], 0)
        self.assertFalse(field_section["same_run_path_proven"])
        self.assertFalse(field_section["cross_run_clean_baseline_path_comparator_present"])
        self.assertEqual(field_section["cross_run_clean_baseline_path_summary"], {"present": False})
        self.assertFalse(field_section["cross_run_clean_baseline_same_run_override_allowed"])
        self.assertIn("current_same_run_path_generation_failed", field_section["blocked_reasons"])
        self.assertFalse(field_section["delivery_success"])
        self.assertFalse(field_section["safe_to_control"])
        self.assertFalse(field_section["nav2_route_execution_success"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/field-evidence-field-run-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["task"]["localization_path_material_readback"]["status"],
            "localization_path_material_readback_ready_not_route_execution_proof",
        )
        self.assertEqual(
            detail["task"]["field_evidence_consumer_ingest"]["localization_path_material_readback"][
                "same_run_path_point_count"
            ],
            0,
        )

        status, field_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/field-evidence-field-run-001?include=field_evidence,localization_path_material_readback",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            field_consumer["localization_path_material_readback"]["status"],
            "localization_path_material_readback_ready_not_route_execution_proof",
        )
        self.assertEqual(
            field_consumer["field_evidence_consumer_ingest"]["localization_path_material_readback"][
                "same_run_path_point_count"
            ],
            0,
        )

        bundle_payload = self._artifact_bundle_payload()
        bundle_payload["artifact_bundle"]["localization_path_material_readback"][
            "cross_run_clean_baseline_path_comparator_present"
        ] = True
        bundle_payload["artifact_bundle"]["localization_path_material_readback"][
            "cross_run_clean_baseline_path_summary"
        ] = {
            "map_once_observed": True,
            "amcl_pose_observed": True,
            "path_generation_requested": True,
            "path_generation_succeeded": True,
            "path_generated": True,
            "path_point_count": 31,
            "same_run_override_allowed": False,
        }
        bundle_status, bundle_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bundle_payload,
        )

        self.assertEqual(bundle_status, 201)
        bundle_section = bundle_created["task"]["artifact_bundle"]["localization_path_material_readback"]
        self.assertEqual(
            bundle_section["schema"],
            relay_module.O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA,
        )
        self.assertTrue(bundle_section["same_run_localization_material_present"])
        self.assertTrue(bundle_section["same_run_localization_tf_map_to_odom"])
        self.assertTrue(bundle_section["cross_run_clean_baseline_path_comparator_present"])
        self.assertEqual(
            bundle_section["cross_run_clean_baseline_path_summary"]["path_point_count"],
            31,
        )

        status, bundle_consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence,localization_path_material_readback",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertFalse(bundle_consumer["localization_path_material_readback"]["same_run_path_generated"])
        self.assertEqual(
            bundle_consumer["artifact_bundle_consumer_ingest"]["localization_path_material_readback"][
                "same_run_path_point_count"
            ],
            0,
        )

    def test_o6_localization_path_material_readback_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("localization_path_material_readback")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["localization_path_material_readback"]
        self.assertEqual(packet["schema"], relay_module.O6_LOCALIZATION_PATH_MATERIAL_READBACK_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("localization_path_material_readback_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["localization_path_material_readback"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["nav2_route_execution_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=localization_path_material_readback",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["localization_path_material_readback"]["status"], "blocked_not_proven")

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-localization-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["localization_path_material_readback"]["task_id"] = (
            "artifact-bundle-localization-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["localization_path_material_readback"]["schema"] = (
            "trashbot.bad_localization_path_material_readback.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "localization_path_material_readback_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["localization_path_material_readback"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-localization-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["localization_path_material_readback"]["task_id"] = (
            "artifact-bundle-localization-bad-scope-001"
        )
        bad_scope_payload["artifact_bundle"]["localization_path_material_readback"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "localization_path_material_readback_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["localization_path_material_readback"][
                "blocked_reasons"
            ],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-localization-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["localization_path_material_readback"]["task_id"] = "other-task"
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "localization_path_material_readback_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["localization_path_material_readback"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-localization-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["localization_path_material_readback"]["task_id"] = (
            "artifact-bundle-localization-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["localization_path_material_readback"]["source"] = (
            "/tmp/localization_path_material_readback.json"
        )
        unsafe_text_payload["artifact_bundle"]["localization_path_material_readback"]["response_body"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "localization_path_material_readback_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["localization_path_material_readback"][
                "blocked_reasons"
            ],
        )
        self.assertNotIn("/tmp/localization_path_material_readback.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-localization-dangerous-001"
        dangerous_payload["artifact_bundle"]["localization_path_material_readback"]["task_id"] = (
            "artifact-bundle-localization-dangerous-001"
        )
        dangerous_payload["artifact_bundle"]["localization_path_material_readback"][
            "same_run_path_generation_succeeded"
        ] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["localization_path_material_readback"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn(
            "localization_path_material_readback_same_run_path_success_claimed",
            dangerous_packet["blocked_reasons"],
        )
        self.assertFalse(dangerous_packet["same_run_path_generation_succeeded"])

    def test_o6_same_task_replay_packet_readback_consumes_exact_identity_counts_and_false_fields(self):
        task_id = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
        payload = {
            "artifact_bundle": {
                "schema": relay_module.O6_ARTIFACT_BUNDLE_SCHEMA,
                "robot_id": "trashbot-001",
                "task_id": task_id,
                "status": "same_task_replay_packet_readback_ready",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "same_task_replay_packet_readback": self._same_task_replay_packet_readback_payload(task_id),
                "route_refs": ["captures/fixed_route_28_pose_route.csv"],
                "replay_refs": ["captures/same_task_route_replay_packet.jsonl"],
                "keyframe_refs": [],
                "evidence_refs": [],
            }
        }

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_replay_packet_readback"]
        self.assertEqual(packet["schema"], relay_module.O6_SAME_TASK_REPLAY_PACKET_READBACK_SCHEMA)
        self.assertEqual(packet["source_schema"], relay_module.SAME_TASK_REPLAY_PACKET_SOURCE_SCHEMA)
        self.assertEqual(
            packet["proof_scope"],
            relay_module.O6_SAME_TASK_REPLAY_PACKET_READBACK_PROOF_SCOPE,
        )
        self.assertEqual(packet["status"], "same_task_replay_packet_ready_not_route_execution_proof")
        self.assertEqual(packet["packet_id"], "packet_o3_28_pose_same_task_replay_7d57826142b0c79c")
        self.assertEqual(packet["task_id"], task_id)
        self.assertEqual(
            packet["route_intent_id"],
            "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        )
        self.assertEqual(packet["route_csv_row_count"], 28)
        self.assertEqual(packet["replay_jsonl_event_count"], 28)
        self.assertEqual(packet["path_structured_pose_count"], 28)
        self.assertTrue(packet["same_task_identity_verified"])
        self.assertTrue(packet["same_task_replay_packet_ready"])
        self.assertEqual(packet["source_refs"]["route_csv_ref"], "fixed_route_28_pose_route.csv")
        self.assertEqual(packet["source_refs"]["packet_jsonl_ref"], "same_task_route_replay_packet.jsonl")
        self.assertEqual(packet["sha256_prefixes"]["summary"], "9948414e1a46b6e7")
        for false_key in (
            "route_execution_success",
            "delivery_success",
            "hil_pass",
            "safe_to_control",
            "robot_control_executed",
            "primary_actions_enabled",
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "connects_cloud_production",
        ):
            self.assertFalse(packet[false_key], false_key)

        status, consumer = self.client.request(
            "GET",
            f"/api/o6/consumer/tasks/{task_id}?include=same_task_replay_packet_readback",
            token="",
        )
        self.assertEqual(status, 200)
        readback = consumer["same_task_replay_packet_readback"]
        self.assertEqual(readback["packet_id"], "packet_o3_28_pose_same_task_replay_7d57826142b0c79c")
        self.assertEqual(readback["route_csv_row_count"], 28)
        self.assertFalse(readback["route_execution_success"])
        self.assertFalse(readback["calls_base_manual"])
        self.assertFalse(readback["uses_base_uart"])

    def test_o6_same_task_replay_packet_readback_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("same_task_replay_packet_readback", None)

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_replay_packet_readback"]
        self.assertEqual(packet["schema"], relay_module.O6_SAME_TASK_REPLAY_PACKET_READBACK_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("same_task_replay_packet_readback_not_available", packet["blocked_reasons"])
        self.assertFalse(packet["safe_to_control"])

        unsafe_payload = self._artifact_bundle_payload()
        unsafe_payload["artifact_bundle"]["task_id"] = "artifact-bundle-replay-readback-unsafe-001"
        unsafe_payload["artifact_bundle"]["same_task_replay_packet_readback"] = (
            self._same_task_replay_packet_readback_payload("artifact-bundle-replay-readback-unsafe-001")
        )
        unsafe_payload["artifact_bundle"]["same_task_replay_packet_readback"]["safe_to_control"] = True
        unsafe_payload["artifact_bundle"]["same_task_replay_packet_readback"]["source_refs"][
            "route_csv_ref"
        ] = "https://example.test/route.csv?token=secret"
        status, unsafe_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_payload,
        )
        encoded = json.dumps(unsafe_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_created["task"]["artifact_bundle"]["same_task_replay_packet_readback"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("same_task_replay_packet_readback_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("token=secret", encoded)
        self.assertFalse(unsafe_packet["safe_to_control"])

    def test_o6_same_task_route_execution_material_packet_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("same_task_route_execution_material_packet")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"]
        self.assertEqual(packet["schema"], relay_module.O6_SAME_TASK_ROUTE_EXECUTION_MATERIAL_PACKET_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("same_task_route_execution_material_packet_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["same_task_route_execution_material_packet"])
        self.assertFalse(packet["safe_to_control"])
        self.assertEqual(
            created["task"]["artifact_bundle"]["route_execution_result_delivery_readiness"]["status"],
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
        )

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=same_task_route_execution_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["same_task_route_execution_material_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_route_execution_material_packet_not_available",
            consumer["same_task_route_execution_material_packet"]["blocked_reasons"],
        )
        self.assertFalse(consumer["same_task_route_execution_material_packet"]["route_execution_credit_candidate"])

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-material-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-bad-schema-001"
        )
        bad_schema_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["schema"] = (
            "trashbot.bad_same_task_route_execution_material_packet.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_route_execution_material_packet_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "blocked_reasons"
            ],
        )

        task_mismatch_payload = self._artifact_bundle_payload()
        task_mismatch_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-material-task-mismatch-001"
        task_mismatch_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-task-mismatch-001"
        )
        task_mismatch_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["task_id"] = (
            "other-task"
        )
        status, task_mismatch_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            task_mismatch_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_route_execution_material_packet_task_mismatch",
            task_mismatch_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "blocked_reasons"
            ],
        )

        missing_credit_payload = self._artifact_bundle_payload()
        missing_credit_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-material-missing-credit-001"
        missing_credit_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-missing-credit-001"
        )
        missing_credit_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-missing-credit-001"
        )
        missing_credit_payload["artifact_bundle"]["same_task_route_execution_material_packet"].pop(
            "credit_required_evidence"
        )
        status, missing_credit_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_credit_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_route_execution_material_packet_credit_fields_missing",
            missing_credit_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "blocked_reasons"
            ],
        )
        self.assertIn(
            "same_task_route_execution_material_packet_credit_fields_invalid",
            missing_credit_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "blocked_reasons"
            ],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-material-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-unsafe-text-001"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["source"] = (
            "/tmp/route_execution_material_packet.json"
        )
        unsafe_text_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["response_body"] = (
            "Traceback: Authorization Bearer secret"
        )
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded_unsafe_text = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "same_task_route_execution_material_packet_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"][
                "blocked_reasons"
            ],
        )
        self.assertEqual(
            unsafe_text_created["task"]["artifact_bundle"]["same_task_field_material_packet"]["status"],
            "ready_not_delivery_proof",
        )
        self.assertNotIn("/tmp/route_execution_material_packet.json", encoded_unsafe_text)
        self.assertNotIn("Authorization Bearer secret", encoded_unsafe_text)

        unsafe_ref_payload = self._artifact_bundle_payload()
        unsafe_ref_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-material-unsafe-ref-001"
        unsafe_ref_payload["artifact_bundle"]["same_task_field_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-unsafe-ref-001"
        )
        unsafe_ref_payload["artifact_bundle"]["same_task_route_execution_material_packet"]["task_id"] = (
            "artifact-bundle-route-material-unsafe-ref-001"
        )
        unsafe_ref_payload["artifact_bundle"]["same_task_route_execution_material_packet"][
            "material_summaries"
        ]["route_bag_pose_progress_replay"]["sample_refs"][0] = (
            "https://example.test/pose-progress.json?token=secret"
        )
        unsafe_ref_payload["artifact_bundle"]["same_task_route_execution_material_packet"][
            "safe_to_control"
        ] = True
        status, unsafe_ref_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_ref_payload,
        )
        encoded = json.dumps(unsafe_ref_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        unsafe_packet = unsafe_ref_created["task"]["artifact_bundle"]["same_task_route_execution_material_packet"]
        self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
        self.assertIn("same_task_route_execution_material_packet_dangerous_true", unsafe_packet["blocked_reasons"])
        self.assertNotIn("token=secret", encoded)
        self.assertFalse(unsafe_packet["safe_to_control"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-route-material-unsafe-ref-001?include=same_task_route_execution_material_packet",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["same_task_route_execution_material_packet"]["status"], "blocked_not_proven")
        self.assertIn(
            "same_task_route_execution_material_packet_dangerous_true",
            explicit["same_task_route_execution_material_packet"]["blocked_reasons"],
        )

    def test_o6_route_bag_evidence_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_bag_evidence")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_bag_evidence"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_BAG_EVIDENCE_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_evidence_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["route_bag_evidence"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=field_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_bag_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_evidence_not_available",
            consumer["route_bag_evidence"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["route_bag_evidence"]["schema"] = "trashbot.bad_route_bag.v1"
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_evidence_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["route_bag_evidence"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_bag_evidence"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_evidence_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["route_bag_evidence"]["blocked_reasons"],
        )

        unsafe_cases = [
            (
                "path",
                lambda evidence: evidence.update({"db3_path": "/tmp/route_bag_0.db3"}),
                ["/tmp/route_bag_0.db3"],
            ),
            (
                "root",
                lambda evidence: evidence.update({"artifact_root": "/tmp/route_bag"}),
                ["/tmp/route_bag"],
            ),
            (
                "token",
                lambda evidence: evidence.update({"token": "secret-token"}),
                ["secret-token"],
            ),
            (
                "raw",
                lambda evidence: evidence.update({"raw_payload": {"topic": "/tf"}}),
                ["raw_payload"],
            ),
            (
                "base64",
                lambda evidence: evidence.update({"db3_base64": "data:application/octet-stream;base64,AAAA"}),
                ["base64,AAAA"],
            ),
            (
                "credential-url",
                lambda evidence: evidence.update({"source_label": "https://user:pass@example.test/db3"}),
                ["user:pass@example.test"],
            ),
            (
                "unsafe-topic",
                lambda evidence: evidence.update({"sample_topic_names": ["/cmd_vel"]}),
                ["/cmd_vel"],
            ),
        ]
        for case_index, (case_name, mutate, forbidden_texts) in enumerate(unsafe_cases):
            payload = self._artifact_bundle_payload()
            payload["artifact_bundle"]["task_id"] = f"artifact-bundle-route-bag-unsafe-case-{case_index:02d}"
            mutate(payload["artifact_bundle"]["route_bag_evidence"])
            status, unsafe_created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)
            encoded = json.dumps(unsafe_created, ensure_ascii=False)
            self.assertEqual(status, 201)
            unsafe_packet = unsafe_created["task"]["artifact_bundle"]["route_bag_evidence"]
            self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
            self.assertIn("route_bag_evidence_unsafe", unsafe_packet["blocked_reasons"])
            self.assertFalse(unsafe_packet["robot_control_executed"])
            for forbidden_text in forbidden_texts:
                self.assertNotIn(forbidden_text, encoded)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-dangerous-001"
        dangerous_payload["artifact_bundle"]["route_bag_evidence"]["route_execution_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["route_bag_evidence"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_evidence_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["delivery_success"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-route-bag-dangerous-001?include=route_bag_evidence",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_bag_evidence"]["status"], "blocked_not_proven")
        self.assertIn("route_bag_evidence_dangerous_true", explicit["route_bag_evidence"]["blocked_reasons"])

    def test_o6_route_bag_payload_replay_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_bag_payload_replay")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_bag_payload_replay"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_payload_replay_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["route_bag_payload_replay"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=route_bag_payload_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_bag_payload_replay"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_payload_replay_not_available",
            consumer["route_bag_payload_replay"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-payload-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["route_bag_payload_replay"]["schema"] = "trashbot.bad_route_bag_payload_replay.v1"
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_payload_replay_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["route_bag_payload_replay"]["blocked_reasons"],
        )

        unsafe_topic_payload = self._artifact_bundle_payload()
        unsafe_topic_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-payload-unsafe-topic-001"
        unsafe_topic_payload["artifact_bundle"]["route_bag_payload_replay"]["sample_topic_names"] = ["/cmd_vel"]
        status, unsafe_topic_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_topic_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_topic_created["task"]["artifact_bundle"]["route_bag_payload_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_bag_payload_replay_unsafe",
            unsafe_topic_created["task"]["artifact_bundle"]["route_bag_payload_replay"]["blocked_reasons"],
        )

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-payload-dangerous-001"
        dangerous_payload["artifact_bundle"]["route_bag_payload_replay"]["payload_replay_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["route_bag_payload_replay"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_payload_replay_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-route-bag-payload-dangerous-001?include=route_bag_payload_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_bag_payload_replay"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_payload_replay_dangerous_true",
            explicit["route_bag_payload_replay"]["blocked_reasons"],
        )

    def test_o6_route_bag_semantic_replay_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_bag_semantic_replay")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_bag_semantic_replay"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_semantic_replay_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["route_bag_semantic_replay"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=route_bag_semantic_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_bag_semantic_replay"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_semantic_replay_not_available",
            consumer["route_bag_semantic_replay"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-semantic-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["route_bag_semantic_replay"]["schema"] = (
            "trashbot.bad_route_bag_semantic_replay.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_semantic_replay_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]["blocked_reasons"],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-semantic-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_bag_semantic_replay"]["proof_scope"] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_semantic_replay_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]["blocked_reasons"],
        )

        unsafe_topic_payload = self._artifact_bundle_payload()
        unsafe_topic_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-semantic-unsafe-topic-001"
        unsafe_topic_payload["artifact_bundle"]["route_bag_semantic_replay"]["sample_topic_names"] = ["/cmd_vel"]
        status, unsafe_topic_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_topic_payload,
        )
        self.assertEqual(status, 201)
        self.assertEqual(
            unsafe_topic_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_bag_semantic_replay_unsafe",
            unsafe_topic_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]["blocked_reasons"],
        )

        unsafe_text_payload = self._artifact_bundle_payload()
        unsafe_text_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-semantic-unsafe-text-001"
        unsafe_text_payload["artifact_bundle"]["route_bag_semantic_replay"]["tf_summary"] = {
            "sample_count": 1,
            "transform_count": 2,
            "frame_id_samples": ["map"],
            "child_frame_id_samples": ["https://example.test/token=secret"],
        }
        status, unsafe_text_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            unsafe_text_payload,
        )
        encoded = json.dumps(unsafe_text_created, ensure_ascii=False)
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_semantic_replay_unsafe",
            unsafe_text_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]["blocked_reasons"],
        )
        self.assertNotIn("token=secret", encoded)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-semantic-dangerous-001"
        dangerous_payload["artifact_bundle"]["route_bag_semantic_replay"]["semantic_replay_success"] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["route_bag_semantic_replay"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_semantic_replay_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["robot_control_executed"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-route-bag-semantic-dangerous-001?include=route_bag_semantic_replay",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_bag_semantic_replay"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_semantic_replay_dangerous_true",
            explicit["route_bag_semantic_replay"]["blocked_reasons"],
        )

    def test_o6_route_bag_full_semantic_decode_matrix_missing_or_unsafe_returns_blocked_summary(self):
        missing_payload = self._artifact_bundle_payload()
        missing_payload["artifact_bundle"].pop("route_bag_full_semantic_decode_matrix")

        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            missing_payload,
        )

        self.assertEqual(status, 201)
        packet = created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]
        self.assertEqual(packet["schema"], relay_module.O6_ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA)
        self.assertEqual(packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_full_semantic_decode_matrix_not_available", packet["blocked_reasons"])
        self.assertEqual(packet["next_required_evidence"], ["route_bag_full_semantic_decode_matrix"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["route_execution_success"])

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=route_bag_full_semantic_decode_matrix",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["route_bag_full_semantic_decode_matrix"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_full_semantic_decode_matrix_not_available",
            consumer["route_bag_full_semantic_decode_matrix"]["blocked_reasons"],
        )

        bad_schema_payload = self._artifact_bundle_payload()
        bad_schema_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-matrix-bad-schema-001"
        bad_schema_payload["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]["schema"] = (
            "trashbot.bad_route_bag_full_semantic_decode_matrix.v1"
        )
        status, bad_schema_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_schema_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_full_semantic_decode_matrix_schema_unsupported",
            bad_schema_created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"][
                "blocked_reasons"
            ],
        )

        bad_scope_payload = self._artifact_bundle_payload()
        bad_scope_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-matrix-bad-scope-001"
        bad_scope_payload["artifact_bundle"]["route_bag_full_semantic_decode_matrix"][
            "proof_scope"
        ] = "wrong_scope"
        status, bad_scope_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            bad_scope_payload,
        )
        self.assertEqual(status, 201)
        self.assertIn(
            "route_bag_full_semantic_decode_matrix_proof_scope_unsupported",
            bad_scope_created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"][
                "blocked_reasons"
            ],
        )

        unsafe_cases = [
            (
                "unsafe-topic",
                lambda matrix: matrix["topic_type_matrix"][0].update({"topic": "/cmd_vel"}),
                ["/cmd_vel"],
                "route_bag_full_semantic_decode_matrix_unsafe",
            ),
            (
                "unsafe-text",
                lambda matrix: matrix.update({"operator_text": "https://example.test/route?token=secret"}),
                ["token=secret"],
                "route_bag_full_semantic_decode_matrix_unsafe",
            ),
            (
                "raw",
                lambda matrix: matrix.update({"raw_payload": "raw bytes should not echo"}),
                ["raw bytes should not echo"],
                "route_bag_full_semantic_decode_matrix_unsafe",
            ),
            (
                "base64",
                lambda matrix: matrix.update({"sample_base64": "data:application/octet-stream;base64,AAAA"}),
                ["base64,AAAA"],
                "route_bag_full_semantic_decode_matrix_unsafe",
            ),
            (
                "missing-count",
                lambda matrix: matrix.pop("decoded_message_sample_count"),
                [],
                "route_bag_full_semantic_decode_matrix_decoded_message_sample_count_invalid",
            ),
            (
                "negative-count",
                lambda matrix: matrix.update({"failed_topic_type_count": -1}),
                ["failed_topic_type_count\": -1"],
                "route_bag_full_semantic_decode_matrix_failed_topic_type_count_invalid",
            ),
        ]
        for case_index, (case_name, mutate, forbidden_texts, expected_reason) in enumerate(unsafe_cases):
            payload = self._artifact_bundle_payload()
            payload["artifact_bundle"]["task_id"] = f"artifact-bundle-route-bag-matrix-{case_name}-{case_index:02d}"
            mutate(payload["artifact_bundle"]["route_bag_full_semantic_decode_matrix"])
            status, unsafe_created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)
            encoded = json.dumps(unsafe_created, ensure_ascii=False)
            self.assertEqual(status, 201)
            unsafe_packet = unsafe_created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]
            self.assertEqual(unsafe_packet["status"], "blocked_not_proven")
            self.assertIn(expected_reason, unsafe_packet["blocked_reasons"])
            self.assertFalse(unsafe_packet["robot_control_executed"])
            self.assertFalse(unsafe_packet["connects_cloud_production"])
            for forbidden_text in forbidden_texts:
                self.assertNotIn(forbidden_text, encoded)

        dangerous_payload = self._artifact_bundle_payload()
        dangerous_payload["artifact_bundle"]["task_id"] = "artifact-bundle-route-bag-matrix-dangerous-001"
        dangerous_payload["artifact_bundle"]["route_bag_full_semantic_decode_matrix"][
            "route_execution_success"
        ] = True
        dangerous_payload["artifact_bundle"]["route_bag_full_semantic_decode_matrix"][
            "connects_cloud_production"
        ] = True
        status, dangerous_created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            dangerous_payload,
        )
        self.assertEqual(status, 201)
        dangerous_packet = dangerous_created["task"]["artifact_bundle"]["route_bag_full_semantic_decode_matrix"]
        self.assertEqual(dangerous_packet["status"], "blocked_not_proven")
        self.assertIn("route_bag_full_semantic_decode_matrix_dangerous_true", dangerous_packet["blocked_reasons"])
        self.assertFalse(dangerous_packet["route_execution_success"])
        self.assertFalse(dangerous_packet["connects_cloud_production"])

        status, explicit = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-route-bag-matrix-dangerous-001?include=route_bag_full_semantic_decode_matrix",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(explicit["route_bag_full_semantic_decode_matrix"]["status"], "blocked_not_proven")
        self.assertIn(
            "route_bag_full_semantic_decode_matrix_dangerous_true",
            explicit["route_bag_full_semantic_decode_matrix"]["blocked_reasons"],
        )

    def test_o6_artifact_access_probe_reads_allowlisted_artifact_bundle_refs(self):
        artifact_root = pathlib.Path(self.tmp.name) / "artifact-access-root"
        captures_dir = artifact_root / "captures"
        captures_dir.mkdir(parents=True)
        route_bytes = b"x,y,yaw\n0,0,0\n"
        replay_bytes = b'{"frame_index":0,"state":"mock"}\n'
        keyframe_bytes = b"\x89PNG\r\n\x1a\nmock"
        evidence_bytes = b'{"ok": false}\n'
        (captures_dir / "route.csv").write_bytes(route_bytes)
        (captures_dir / "fixed_route_replay.jsonl").write_bytes(replay_bytes)
        (captures_dir / "keyframe-0001.jpg").write_bytes(keyframe_bytes)
        (captures_dir / "evidence-0001.json").write_bytes(evidence_bytes)
        payload = self._artifact_bundle_payload()
        payload["artifact_access_root"] = str(artifact_root)

        status, created = self.client.request("POST", "/api/o6/archive/artifact-bundle", payload)

        self.assertEqual(status, 201)
        probe = created["task"]["artifact_bundle"]["artifact_access_probe"]
        encoded = json.dumps(created, ensure_ascii=False)
        self.assertEqual(probe["schema"], relay_module.O6_ARTIFACT_ACCESS_PROBE_SCHEMA)
        self.assertEqual(probe["proof_scope"], relay_module.O6_ARTIFACT_ACCESS_PROBE_PROOF_SCOPE)
        self.assertEqual(probe["status"], "local_mock_artifact_access_probe_ready")
        self.assertTrue(probe["allowlist_root_configured"])
        self.assertFalse(probe["allowlist_root_echoed"])
        self.assertNotIn(str(artifact_root), encoded)
        self.assertNotIn("captures/", encoded)
        by_ref = {item["ref"]: item for item in probe["probes"]}
        self.assertEqual(by_ref["route.csv"]["exists"], True)
        self.assertEqual(by_ref["route.csv"]["size_bytes"], len(route_bytes))
        self.assertEqual(by_ref["route.csv"]["sha256"], hashlib.sha256(route_bytes).hexdigest())
        self.assertEqual(by_ref["route.csv"]["detected_type"], "text/csv")
        self.assertEqual(by_ref["route.csv"]["blocked_reason"], "")
        self.assertEqual(by_ref["fixed_route_replay.jsonl"]["sha256"], hashlib.sha256(replay_bytes).hexdigest())
        self.assertEqual(probe["counts"]["readable_ref_count"], 4)
        self.assertFalse(probe["safe_to_control"])
        self.assertFalse(probe["delivery_success"])
        self.assertFalse(probe["primary_actions_enabled"])
        self.assertFalse(probe["robot_control_executed"])
        self.assertFalse(probe["real_oss_connected"])

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/artifact-bundle-task-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(detail["task"]["artifact_access_probe"]["counts"]["readable_ref_count"], 4)

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/artifact-bundle-task-001?include=artifact_access_probe",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["artifact_access_probe"]["status"], "local_mock_artifact_access_probe_ready")
        self.assertEqual(consumer["artifact_access_probe"]["counts"]["readable_ref_count"], 4)

    def test_o6_offline_artifact_seed_smoke_uses_repo_fixtures_and_surfaces_in_consumer_detail(self):
        status, created = self.client.request(
            "POST",
            "/api/o6/archive/artifact-bundle",
            self._offline_artifact_seed_smoke_payload(),
        )

        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], relay_module.O6_ARTIFACT_BUNDLE_ARCHIVE_SCHEMA)
        self.assertEqual(created["task"]["task_origin"], "artifact_bundle")
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["schema"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["source"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SOURCE)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["proof_scope"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["counts"]["route_ref_count"], 1)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["counts"]["replay_ref_count"], 1)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["counts"]["keyframe_ref_count"], 1)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["counts"]["evidence_ref_count"], 1)
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["counts"]["readable_ref_count"], 4)
        self.assertFalse(created["task"]["offline_artifact_seed_smoke"]["safe_to_control"])
        self.assertFalse(created["task"]["offline_artifact_seed_smoke"]["delivery_success"])
        self.assertFalse(created["task"]["offline_artifact_seed_smoke"]["primary_actions_enabled"])
        self.assertFalse(created["task"]["offline_artifact_seed_smoke"]["connects_cloud_production"])
        self.assertFalse(created["task"]["offline_artifact_seed_smoke"]["robot_control_executed"])
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["sample_refs"]["route_ref"]["basename"], "route.csv")
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["sample_refs"]["replay_ref"]["basename"], "derived_replay.jsonl")
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["sample_refs"]["keyframe_ref"]["basename"], "001.jpg")
        self.assertEqual(created["task"]["offline_artifact_seed_smoke"]["sample_refs"]["evidence_ref"]["basename"], "manifest.json")
        self.assertTrue(created["task"]["offline_artifact_seed_smoke"]["sample_refs"]["route_ref"]["sha256_prefix"])
        self.assertIn("local_mock_only", created["task"]["offline_artifact_seed_smoke"]["blocked_reasons"])
        self.assertIn("not_proven", created["task"]["offline_artifact_seed_smoke"]["blocked_reasons"])
        self.assertIn("real_media_fetch_blocked", created["task"]["offline_artifact_seed_smoke"]["blocked_reasons"])
        self.assertIn("real_cloud_archive_readback", created["task"]["offline_artifact_seed_smoke"]["next_required_evidence"])
        self.assertEqual(created["task"]["route_root_seed_gate"]["schema"], relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA)
        self.assertEqual(
            created["task"]["route_root_seed_gate"]["route_root_seed_status"],
            "local_mock_route_root_seed_ready",
        )
        self.assertFalse(created["task"]["route_root_seed_gate"]["route_bag_required"])
        self.assertFalse(created["task"]["route_root_seed_gate"]["route_bag_present"])
        self.assertEqual(created["task"]["route_root_seed_gate"]["manifest_summary"]["sample_ref"], "manifest.json")
        self.assertIn("route_bag_missing_optional", created["task"]["route_root_seed_gate"]["blocked_reasons"])
        self.assertIn("route_bag_optional_evidence", created["task"]["route_root_seed_gate"]["next_required_evidence"])
        self.assertFalse(created["task"]["route_root_seed_gate"]["safe_to_control"])
        self.assertFalse(created["task"]["route_root_seed_gate"]["delivery_success"])
        self.assertNotIn(str(REPO_ROOT), json.dumps(created, ensure_ascii=False))
        self.assertNotIn("https://", json.dumps(created, ensure_ascii=False))
        self.assertNotIn("/cmd_vel", json.dumps(created, ensure_ascii=False))

        status, detail = self.client.request(
            "GET",
            "/api/o6/archive/tasks/offline-artifact-seed-smoke-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(detail["task"]["offline_artifact_seed_smoke"]["schema"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA)
        self.assertEqual(detail["task"]["artifact_bundle"]["offline_artifact_seed_smoke"]["proof_scope"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE)
        self.assertEqual(detail["task"]["route_root_seed_gate"]["proof_scope"], relay_module.O6_ROUTE_ROOT_SEED_GATE_PROOF_SCOPE)

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/offline-artifact-seed-smoke-001?include=offline_artifact_seed_smoke,route_root_seed_gate",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["offline_artifact_seed_smoke"]["schema"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA)
        self.assertEqual(consumer["offline_artifact_seed_smoke"]["sample_refs"]["route_ref"]["basename"], "route.csv")
        self.assertEqual(consumer["offline_artifact_seed_smoke"]["counts"]["requested_ref_count"], 4)
        self.assertFalse(consumer["offline_artifact_seed_smoke"]["safe_to_control"])
        self.assertEqual(consumer["route_root_seed_gate"]["schema"], relay_module.O6_ROUTE_ROOT_SEED_GATE_SCHEMA)
        self.assertFalse(consumer["route_root_seed_gate"]["route_bag_required"])
        self.assertFalse(consumer["route_root_seed_gate"]["route_bag_present"])

        status, consumer_default = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/offline-artifact-seed-smoke-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertIn("offline_artifact_seed_smoke", consumer_default)
        self.assertEqual(consumer_default["offline_artifact_seed_smoke"]["schema"], relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SCHEMA)
        self.assertEqual(
            consumer_default["field_evidence_consumer_ingest"]["offline_artifact_seed_smoke"]["source"],
            relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_SOURCE,
        )
        self.assertEqual(
            consumer_default["field_evidence"]["offline_artifact_seed_smoke"]["proof_scope"],
            relay_module.O6_OFFLINE_ARTIFACT_SEED_SMOKE_PROOF_SCOPE,
        )
        self.assertEqual(
            consumer_default["field_evidence"]["route_root_seed_gate"]["route_root_seed_status"],
            "local_mock_route_root_seed_ready",
        )

    def test_o6_artifact_access_probe_blocks_unsafe_and_large_refs_without_reading(self):
        artifact_root = pathlib.Path(self.tmp.name) / "artifact-access-large"
        artifact_root.mkdir()
        (artifact_root / "route.csv").write_bytes(b"x" * (relay_module.O6_ARTIFACT_ACCESS_PROBE_MAX_FILE_BYTES + 1))

        probe = relay_module._o6_artifact_access_probe_from_refs(
            [
                {"ref_kind": "route", "ref": "route.csv"},
                {"ref_kind": "route", "ref": "../secret.csv"},
                {"ref_kind": "evidence", "ref": "https://example.test/evidence.json?token=secret"},
                {"ref_kind": "evidence", "ref": "credential.json"},
                {"ref_kind": "evidence", "ref": "/cmd_vel"},
            ],
            task_id="probe-task",
            artifact_access_root=str(artifact_root),
        )

        self.assertEqual(probe["status"], "blocked_not_proven")
        by_ref = {item["ref"]: item for item in probe["probes"] if item["ref"]}
        self.assertEqual(by_ref["route.csv"]["exists"], True)
        self.assertEqual(by_ref["route.csv"]["blocked_reason"], "file_too_large")
        self.assertEqual(by_ref["route.csv"]["sha256"], "")
        self.assertIn("file_too_large", probe["blocked_reasons"])
        self.assertIn("path_traversal_ref_blocked", probe["blocked_reasons"])
        self.assertIn("credential_ref_blocked", probe["blocked_reasons"])
        self.assertIn("unsafe_ref", probe["blocked_reasons"])
        self.assertFalse(probe["proof_boundary"]["file_read_attempted"])
        self.assertFalse(probe["safe_to_control"])

    def test_o6_artifact_bundle_ingest_rejects_unsafe_or_empty_refs(self):
        empty_refs = self._artifact_bundle_payload()
        empty_refs["artifact_bundle"]["route_refs"] = []
        empty_refs["artifact_bundle"]["replay_refs"] = []
        empty_refs["artifact_bundle"]["keyframe_refs"] = []
        empty_refs["artifact_bundle"]["evidence_refs"] = []
        status, body = self.client.request("POST", "/api/o6/archive/artifact-bundle", empty_refs)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")

        dangerous = self._artifact_bundle_payload()
        dangerous["artifact_bundle"]["delivery_success"] = True
        status, body = self.client.request("POST", "/api/o6/archive/artifact-bundle", dangerous)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

        unsafe_ref = self._artifact_bundle_payload()
        unsafe_ref["artifact_bundle"]["route_refs"] = ["https://example.test/route.csv?token=secret"]
        status, body = self.client.request("POST", "/api/o6/archive/artifact-bundle", unsafe_ref)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "bad_request")
        self.assertIn("unsafe", body["error"]["message"].lower())

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

    def test_o6_archive_events_endpoint_accepts_safe_voice_tts_draft_and_rejects_runtime_claims(self):
        # voice.tts_draft 只记录文字草稿事件；真实 TTS、喇叭、语音 API 和控制能力继续由 O6 拒绝。
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-voice-tts-draft"),
        )
        self.assertEqual(status, 201)

        payload = self._o6_event_archive_payload(
            task_id="task-o6-voice-tts-draft",
            event_id="evt-voice-tts-draft-0001",
            event_type="voice.tts_draft",
        )
        payload["events"][0].update(
            {
                "summary": "请帮我按电梯到一楼",
                "evidence_refs": ["voice-tts-draft.json"],
                "metadata": {
                    "proof_boundary": "software_proof_o6_o7_voice_tts_draft_event_write_only",
                    "draft_text": "请帮我按电梯到一楼",
                    "locale": "zh-CN",
                    "voice_profile": "operator-soft",
                    "tts_send_enabled": False,
                    "speaker_dispatch_enabled": False,
                    "real_voice_api_connected": False,
                    "real_asr_tts_runtime_connected": False,
                    "safe_to_control": False,
                    "delivery_success": False,
                    "robot_control_executed": False,
                    "connects_cloud_production": False,
                },
            }
        )
        status, created = self.client.request("POST", "/api/o6/archive/events", payload)

        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], "trashbot.o6.archive_events.v1")
        self.assertTrue(created["archive_event_written"])
        self.assertEqual(created["events_written"][0]["event_type"], "voice.tts_draft")
        self.assertEqual(created["events_written"][0]["evidence_refs"], ["voice-tts-draft.json"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["robot_control_executed"])

        status, listing = self.client.request(
            "GET",
            "/api/o6/archive/events?task_id=task-o6-voice-tts-draft&event_type=voice.tts_draft&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(listing["event_summary"]["event_type_counts"]["voice.tts_draft"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-voice-tts-draft", token="")
        self.assertEqual(status, 200)
        event_by_id = {event.get("event_id"): event for event in detail["task"]["events"] if event.get("event_id")}
        self.assertEqual(
            event_by_id["evt-voice-tts-draft-0001"]["metadata"]["proof_boundary"],
            "software_proof_o6_o7_voice_tts_draft_event_write_only",
        )
        self.assertFalse(event_by_id["evt-voice-tts-draft-0001"]["metadata"]["tts_send_enabled"])
        self.assertFalse(event_by_id["evt-voice-tts-draft-0001"]["metadata"]["real_voice_api_connected"])

        dangerous = self._o6_event_archive_payload(
            task_id="task-o6-voice-tts-draft",
            event_id="evt-voice-tts-draft-dangerous",
            event_type="voice.tts_draft",
        )
        dangerous["events"][0]["metadata"] = {"real_voice_api_connected": True}
        status, dangerous_body = self.client.request("POST", "/api/o6/archive/events", dangerous)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", dangerous_body["error"]["message"].lower())

        tts_send_claim = self._o6_event_archive_payload(
            task_id="task-o6-voice-tts-draft",
            event_id="evt-voice-tts-send-dangerous",
            event_type="voice.tts_draft",
        )
        tts_send_claim["events"][0]["tts_send_enabled"] = True
        status, tts_send_body = self.client.request("POST", "/api/o6/archive/events", tts_send_claim)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", tts_send_body["error"]["message"].lower())

    def test_o6_archive_events_endpoint_accepts_voice_speaker_ack_failure_and_rejects_true_ack_claims(self):
        # speaker ACK/failure 只记录 O7 selected-task 本地事件；真实喇叭回执仍必须保持未证明。
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-voice-speaker-ack"),
        )
        self.assertEqual(status, 201)

        ack = self._o6_event_archive_payload(
            task_id="task-o6-voice-speaker-ack",
            event_id="evt-voice-speaker-ack-0001",
            event_type="voice.speaker_ack",
        )
        ack["events"][0].update(
            {
                "summary": "local mock speaker ack event recorded",
                "evidence_refs": ["voice-speaker-ack.json"],
                "metadata": {
                    "proof_boundary": "software_proof_o6_o7_voice_speaker_ack_event_write_only",
                    "ack_status": "ack",
                    "speaker_dispatch_enabled": False,
                    "real_speaker_ack_proven": False,
                    "tts_send_enabled": False,
                    "real_voice_api_connected": False,
                    "real_asr_tts_runtime_connected": False,
                    "safe_to_control": False,
                    "delivery_success": False,
                    "robot_control_executed": False,
                    "connects_cloud_production": False,
                },
            }
        )
        failure = self._o6_event_archive_payload(
            task_id="task-o6-voice-speaker-ack",
            event_id="evt-voice-speaker-failure-0001",
            event_type="voice.speaker_failure",
        )
        failure["events"][0].update(
            {
                "summary": "local mock speaker failure event recorded",
                "evidence_refs": ["voice-speaker-failure.json"],
                "metadata": {
                    "proof_boundary": "software_proof_o6_o7_voice_speaker_ack_event_write_only",
                    "ack_status": "failure",
                    "failure_reason_code": "speaker_ack_missing_not_real_runtime",
                    "speaker_dispatch_enabled": False,
                    "real_speaker_ack_proven": False,
                    "tts_send_enabled": False,
                    "real_voice_api_connected": False,
                    "real_asr_tts_runtime_connected": False,
                    "safe_to_control": False,
                    "delivery_success": False,
                    "robot_control_executed": False,
                    "connects_cloud_production": False,
                },
            }
        )
        ack["events"].append(failure["events"][0])
        status, created = self.client.request("POST", "/api/o6/archive/events", ack)

        self.assertEqual(status, 201)
        self.assertTrue(created["archive_event_written"])
        self.assertEqual(created["event_summary"]["event_type_counts"]["voice.speaker_ack"], 1)
        self.assertEqual(created["event_summary"]["event_type_counts"]["voice.speaker_failure"], 1)
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["robot_control_executed"])
        written_types = {event["event_id"]: event["event_type"] for event in created["events_written"]}
        self.assertEqual(written_types["evt-voice-speaker-ack-0001"], "voice.speaker_ack")
        self.assertEqual(written_types["evt-voice-speaker-failure-0001"], "voice.speaker_failure")

        status, listing = self.client.request(
            "GET",
            "/api/o6/archive/events?task_id=task-o6-voice-speaker-ack&event_type=voice.speaker_ack&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(listing["event_summary"]["event_type_counts"]["voice.speaker_ack"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-voice-speaker-ack", token="")
        self.assertEqual(status, 200)
        event_by_id = {event.get("event_id"): event for event in detail["task"]["events"] if event.get("event_id")}
        self.assertEqual(
            event_by_id["evt-voice-speaker-ack-0001"]["metadata"]["proof_boundary"],
            "software_proof_o6_o7_voice_speaker_ack_event_write_only",
        )
        self.assertFalse(event_by_id["evt-voice-speaker-ack-0001"]["metadata"]["real_speaker_ack_proven"])
        self.assertFalse(event_by_id["evt-voice-speaker-failure-0001"]["metadata"]["speaker_dispatch_enabled"])

        dangerous = self._o6_event_archive_payload(
            task_id="task-o6-voice-speaker-ack",
            event_id="evt-voice-speaker-ack-dangerous",
            event_type="voice.speaker_ack",
        )
        dangerous["events"][0]["metadata"] = {"real_speaker_ack_proven": True}
        status, dangerous_body = self.client.request("POST", "/api/o6/archive/events", dangerous)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", dangerous_body["error"]["message"].lower())

    def test_o6_archive_events_endpoint_accepts_operator_dropoff_acceptance_and_rejects_real_claims(self):
        # operator.dropoff_acceptance 只记录本地 action capture 请求，不能升级成真实投放或控制证明。
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-operator-dropoff"),
        )
        self.assertEqual(status, 201)

        payload = self._o6_event_archive_payload(
            task_id="task-o6-operator-dropoff",
            event_id="evt-operator-dropoff-0001",
            event_type="operator.dropoff_acceptance",
        )
        payload["events"][0].update(
            {
                "summary": "operator requested local/mock dropoff acceptance capture",
                "evidence_refs": ["operator-dropoff-acceptance.json"],
                "metadata": {
                    "proof_boundary": "software_proof_o6_o7_operator_dropoff_action_capture_only",
                    "operator_action_id": "dropoff-action-0001",
                    "operator_display_name": "pc-o7-operator",
                    "real_operator_action_proven": False,
                    "delivery_success": False,
                    "route_execution_success": False,
                    "safe_to_control": False,
                    "hil_pass": False,
                    "robot_control_executed": False,
                    "connects_cloud_production": False,
                },
            }
        )
        status, created = self.client.request("POST", "/api/o6/archive/events", payload)

        self.assertEqual(status, 201)
        self.assertEqual(created["schema"], "trashbot.o6.archive_events.v1")
        self.assertEqual(created["source"], "local_mock_event_archive")
        self.assertTrue(created["archive_event_written"])
        self.assertEqual(created["events_written"][0]["event_type"], "operator.dropoff_acceptance")
        self.assertEqual(created["events_written"][0]["evidence_refs"], ["operator-dropoff-acceptance.json"])
        self.assertFalse(created["safe_to_control"])
        self.assertFalse(created["delivery_success"])
        self.assertFalse(created["robot_control_executed"])

        status, listing = self.client.request(
            "GET",
            "/api/o6/archive/events?task_id=task-o6-operator-dropoff&event_type=operator.dropoff_acceptance&limit=10",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(listing["event_summary"]["event_type_counts"]["operator.dropoff_acceptance"], 1)

        status, detail = self.client.request("GET", "/api/o6/archive/tasks/task-o6-operator-dropoff", token="")
        self.assertEqual(status, 200)
        event_by_id = {event.get("event_id"): event for event in detail["task"]["events"] if event.get("event_id")}
        self.assertEqual(
            event_by_id["evt-operator-dropoff-0001"]["metadata"]["proof_boundary"],
            "software_proof_o6_o7_operator_dropoff_action_capture_only",
        )
        self.assertFalse(event_by_id["evt-operator-dropoff-0001"]["metadata"]["real_operator_action_proven"])

        dangerous = self._o6_event_archive_payload(
            task_id="task-o6-operator-dropoff",
            event_id="evt-operator-dropoff-dangerous",
            event_type="operator.dropoff_acceptance",
        )
        dangerous["events"][0]["metadata"] = {"real_operator_action_proven": True}
        status, dangerous_body = self.client.request("POST", "/api/o6/archive/events", dangerous)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", dangerous_body["error"]["message"].lower())

        route_claim = self._o6_event_archive_payload(
            task_id="task-o6-operator-dropoff",
            event_id="evt-operator-dropoff-route-claim",
            event_type="operator.dropoff_acceptance",
        )
        route_claim["events"][0]["metadata"] = {"route_execution_success": True}
        status, route_claim_body = self.client.request("POST", "/api/o6/archive/events", route_claim)
        self.assertEqual(status, 400)
        self.assertIn("unsafe", route_claim_body["error"]["message"].lower())

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
        self.assertTrue(created["local_mock_annotation_submit_written"])
        self.assertEqual(created["submit_receipt"]["status"], "local_mock_annotation_written")
        self.assertTrue(created["submit_receipt"]["receipt_id"].startswith("o6-label-receipt-"))
        self.assertEqual(created["submit_receipt"]["task_id"], "task-o6-001")
        self.assertEqual(created["submit_receipt"]["label_count"], 2)
        for key in (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "connects_cloud_production",
            "real_annotation_api_connected",
            "real_dataset_export_connected",
            "submit_enabled",
            "dataset_export_available",
        ):
            self.assertFalse(created["submit_receipt"][key])
        self.assertEqual(created["dataset_export"]["export_status"], "local_mock_export_ready")
        self.assertTrue(created["dataset_export"]["local_mock_dataset_export_ready"])
        self.assertFalse(created["dataset_export"]["dataset_export_available"])

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
        self.assertEqual(detail["submit_receipt"]["status"], "local_mock_annotation_written")
        self.assertEqual(detail["dataset_export"]["export_status"], "local_mock_export_ready")
        self.assertFalse(detail["dataset_export_available"])
        self.assertEqual(len(detail["itemized_labels"]), 2)
        self.assertEqual(detail["itemized_labels"][0]["item_type"], "trajectory_frame")
        self.assertEqual(detail["itemized_labels"][0]["label_type"], "elevator_door_state")
        self.assertIn("real_annotation_submit_success", detail["not_proven"])

    def test_o6_cloud_archive_labels_list_filters_robot_task_date_status_and_limit(self):
        def create_task(task_id, robot_id, started_at_ms, finished_at_ms):
            payload = self._o6_archive_task_payload(task_id=task_id, robot_id=robot_id, finished_at=finished_at_ms)
            payload["started_at_ms"] = started_at_ms
            status, _ = self.client.request("POST", "/api/o6/archive/tasks", payload)
            self.assertEqual(status, 201)

        def post_label(task_id, robot_id, now_seconds, *, confidence=None):
            label = {
                "item_id": f"item-{task_id}",
                "item_type": "trajectory_frame",
                "label_type": "elevator_door_state",
                "value": "open",
                "evidence_ref": f"labels/{task_id}.json",
            }
            if confidence is not None:
                label["confidence"] = confidence
            with mock.patch.object(relay_module, "_now", return_value=now_seconds):
                status, body = self.client.request(
                    "POST",
                    "/api/o6/archive/labels",
                    {"robot_id": robot_id, "task_id": task_id, "labels": [label]},
                )
            self.assertIn(status, (200, 201))
            return body

        create_task("task-label-filter-a", "trashbot-alpha", 1000, 2000)
        create_task("task-label-filter-b", "trashbot-beta", 1000, 2000)
        create_task("task-label-filter-c", "trashbot-alpha", 1000, 2000)
        create_task("task-label-filter-d", "trashbot-alpha", 259200000, 259201000)
        post_label("task-label-filter-a", "trashbot-alpha", 86400.0, confidence=0.91)
        post_label("task-label-filter-b", "trashbot-beta", 172800.0)
        post_label("task-label-filter-c", "trashbot-alpha", 172800.0, confidence=0.82)

        status, by_robot_limited = self.client.request(
            "GET",
            "/api/o6/archive/labels?robot_id=trashbot-alpha&limit=1",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertTrue(by_robot_limited["label_query_filters_ready_not_production_proof"])
        self.assertEqual(by_robot_limited["filter_semantics"], "and")
        self.assertEqual(by_robot_limited["filtered_result_count"], 3)
        self.assertEqual(len(by_robot_limited["task_summary"]), 1)
        self.assertEqual(by_robot_limited["applied_filters"]["robot_id"], "trashbot-alpha")
        self.assertEqual(by_robot_limited["applied_filters"]["limit"], 1)
        for key in (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "submit_enabled",
            "rollback_enabled",
            "dataset_export_available",
            "real_annotation_api_connected",
            "real_dataset_export_connected",
            "connects_cloud_production",
            "robot_control_executed",
        ):
            self.assertFalse(by_robot_limited[key])

        status, by_task = self.client.request(
            "GET",
            "/api/o6/archive/labels?task_id=task-label-filter-b",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(by_task["filtered_result_count"], 1)
        self.assertEqual(by_task["task_summary"][0]["task_id"], "task-label-filter-b")
        self.assertEqual(by_task["task_summary"][0]["robot_id"], "trashbot-beta")

        status, by_label_date = self.client.request(
            "GET",
            "/api/o6/archive/labels?date=1970-01-02",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(by_label_date["filtered_result_count"], 1)
        self.assertEqual(by_label_date["date_filter_source"], "label.updated_at_ms")
        self.assertEqual(by_label_date["task_summary"][0]["task_id"], "task-label-filter-a")
        self.assertEqual(by_label_date["task_summary"][0]["date_filter_source"], "label.updated_at_ms")

        status, combined = self.client.request(
            "GET",
            "/api/o6/archive/labels?robot_id=trashbot-alpha&task_id=task-label-filter-c&date=1970-01-03&status=labeled&limit=1",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(combined["filtered_result_count"], 1)
        self.assertEqual(combined["label_summary"]["labeled_task_count"], 1)
        self.assertEqual(combined["task_summary"][0]["task_id"], "task-label-filter-c")
        self.assertEqual(
            combined["applied_filters"],
            {
                "robot_id": "trashbot-alpha",
                "task_id": "task-label-filter-c",
                "date": "1970-01-03",
                "status": "labeled",
                "limit": 1,
            },
        )

        status, fallback_date = self.client.request(
            "GET",
            "/api/o6/archive/labels?robot_id=trashbot-alpha&date=1970-01-04&status=pending",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(fallback_date["filtered_result_count"], 1)
        self.assertEqual(fallback_date["date_filter_source"], "task.finished_at_ms")
        self.assertEqual(fallback_date["task_summary"][0]["task_id"], "task-label-filter-d")

        status, unknown = self.client.request(
            "GET",
            "/api/o6/archive/labels?robot_id=trashbot-missing",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(unknown["filtered_result_count"], 0)
        self.assertEqual(unknown["task_summary"], [])
        self.assertEqual(unknown["blocked_reasons"], ["label_query_filter_no_matches"])

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
        self.assertTrue(updated["local_mock_annotation_submit_written"])
        self.assertEqual(updated["submit_receipt"]["status"], "local_mock_annotation_written")
        self.assertEqual(updated["submit_receipt"]["label_count"], 2)
        self.assertFalse(updated["submit_receipt"]["robot_control_executed"])

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

    def test_o6_cloud_archive_labels_task_export_returns_safe_manifest_and_consumer_summary(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-export"),
        )
        self.assertEqual(status, 201)
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-export",
                "labels": [
                    {
                        "item_id": "traj-export-0001",
                        "item_type": "trajectory_frame",
                        "label_type": "elevator_door_state",
                        "value": "open",
                        "confidence": 0.91,
                        "annotator_id": "labeler-export",
                        "evidence_ref": "labels/export-evidence-0001.json",
                    },
                    {
                        "item_id": "traj-export-0002",
                        "item_type": "trajectory_frame",
                        "label_type": "trajectory_gate",
                        "value": "valid",
                        "confidence": 0.86,
                        "evidence_ref": "labels/export-evidence-0002.json",
                    },
                ],
            },
        )
        self.assertEqual(status, 201)

        status, exported = self.client.request(
            "GET",
            "/api/o6/archive/labels/task-o6-export/export?format=jsonl&robot_id=trashbot-001",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(exported["schema"], relay_module.O6_ANNOTATION_DATASET_EXPORT_SCHEMA)
        self.assertEqual(exported["export_status"], "local_mock_export_ready")
        self.assertEqual(exported["format"], "jsonl")
        self.assertEqual(exported["label_count"], 2)
        self.assertEqual(exported["item_count"], 2)
        self.assertTrue(exported["local_mock_dataset_export_ready"])
        self.assertTrue(exported["local_mock_dataset_export_written"])
        self.assertFalse(exported["dataset_export_available"])
        self.assertFalse(exported["real_dataset_export_connected"])
        self.assertFalse(exported["real_annotation_api_connected"])
        self.assertFalse(exported["connects_cloud_production"])
        self.assertFalse(exported["robot_control_executed"])
        self.assertEqual(exported["submit_receipt"]["status"], "local_mock_annotation_written")
        self.assertEqual(len(exported["sample_rows"]), 2)
        self.assertEqual(exported["sample_rows"][0]["evidence_ref"], "export-evidence-0001.json")
        self.assertFalse(exported["export_manifest"]["contains_raw_media"])
        self.assertFalse(exported["export_manifest"]["contains_base64"])
        self.assertFalse(exported["export_manifest"]["contains_credentials"])
        self.assertFalse(exported["export_manifest"]["contains_absolute_paths"])
        exported_text = json.dumps(exported, ensure_ascii=False)
        for forbidden in ("base64,", "/cmd_vel", "Authorization", "Bearer", "secret=", "/tmp/"):
            self.assertNotIn(forbidden, exported_text)

        status, consumer = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-export?include=labeling",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(consumer["labeling"]["submit_receipt"]["status"], "local_mock_annotation_written")
        self.assertEqual(consumer["labeling"]["dataset_export"]["export_status"], "local_mock_export_ready")
        self.assertTrue(consumer["labeling"]["local_mock_annotation_submit_written"])
        self.assertFalse(consumer["labeling"]["dataset_export"]["real_dataset_export_connected"])

    def test_o6_cloud_archive_labels_export_fail_closed_paths(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-export-empty"),
        )
        self.assertEqual(status, 201)

        status, missing = self.client.request(
            "GET",
            "/api/o6/archive/labels/missing-task/export?format=jsonl",
            token="",
        )
        self.assertEqual(status, 404)
        self.assertEqual(missing["error"]["code"], "unknown_task")

        status, mismatch = self.client.request(
            "GET",
            "/api/o6/archive/labels/task-o6-export-empty/export?format=jsonl&robot_id=trashbot-other",
            token="",
        )
        self.assertEqual(status, 403)
        self.assertEqual(mismatch["error"]["code"], "unauthorized_task")

        status, bad_format = self.client.request(
            "GET",
            "/api/o6/archive/labels/task-o6-export-empty/export?format=csv",
            token="",
        )
        self.assertEqual(status, 400)
        self.assertEqual(bad_format["error"]["code"], "bad_request")

        status, dangerous_query = self.client.request(
            "GET",
            "/api/o6/archive/labels/task-o6-export-empty/export?format=jsonl&safe_to_control=true",
            token="",
        )
        self.assertEqual(status, 400)
        self.assertEqual(dangerous_query["error"]["code"], "bad_request")

        status, blocked = self.client.request(
            "GET",
            "/api/o6/archive/labels/task-o6-export-empty/export?format=jsonl",
            token="",
        )
        self.assertEqual(status, 409)
        self.assertEqual(blocked["schema"], relay_module.O6_ANNOTATION_DATASET_EXPORT_SCHEMA)
        self.assertEqual(blocked["export_status"], "blocked_not_proven")
        self.assertFalse(blocked["local_mock_dataset_export_ready"])
        self.assertFalse(blocked["dataset_export_available"])
        self.assertEqual(blocked["blocked_reasons"], ["local_mock_labels_not_available"])

        status, detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-export-empty", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["label_summary"]["itemized_label_count"], 0)

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

        status, empty_labels = self.client.request(
            "POST",
            "/api/o6/archive/labels",
            {
                "robot_id": "trashbot-001",
                "task_id": "task-o6-003",
                "labels": [],
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(empty_labels["error"]["code"], "bad_request")

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

        dangerous_true = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-003",
            "real_annotation_api_connected": True,
            "labels": [
                {
                    "item_id": "traj-0302",
                    "item_type": "trajectory_frame",
                    "label_type": "elevator_door_state",
                    "value": "open",
                }
            ],
        }
        status, dangerous = self.client.request("POST", "/api/o6/archive/labels", dangerous_true)
        self.assertEqual(status, 400)
        self.assertEqual(dangerous["error"]["code"], "bad_request")
        self.assertIn("unsafe", dangerous["error"]["message"].lower())

        unsafe_ref = {
            "robot_id": "trashbot-001",
            "task_id": "task-o6-003",
            "labels": [
                {
                    "item_id": "traj-0303",
                    "item_type": "trajectory_frame",
                    "label_type": "trajectory_gate",
                    "value": "valid",
                    "evidence_ref": "https://example.test/evidence.json?token=secret",
                }
            ],
        }
        status, unsafe_ref_body = self.client.request("POST", "/api/o6/archive/labels", unsafe_ref)
        self.assertEqual(status, 400)
        self.assertEqual(unsafe_ref_body["error"]["code"], "bad_request")
        self.assertIn("unsafe", unsafe_ref_body["error"]["message"].lower())

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
        self.assertIn("invalid_label_query_filter", invalid_status["error"]["message"])

        status, invalid_limit = self.client.request("GET", "/api/o6/archive/labels?limit=-1", token="")
        self.assertEqual(status, 400)
        self.assertEqual(invalid_limit["error"]["code"], "bad_request")
        self.assertIn("invalid_label_query_filter", invalid_limit["error"]["message"])

        status, capped_listing = self.client.request("GET", "/api/o6/archive/labels?limit=99999", token="")
        self.assertEqual(status, 200)
        self.assertLessEqual(capped_listing["limit"], relay_module.O6_CLOUD_LABELING_MAX_LIST_LIMIT)
        self.assertEqual(capped_listing["status_filter"], "all")

        status, detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-003", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["label_summary"]["itemized_label_count"], 0)
        self.assertEqual(detail["submit_receipt"]["status"], "blocked_not_proven")

    def test_o6_cloud_archive_labels_list_query_filters_fail_closed_without_store_mutation(self):
        status, _ = self.client.request(
            "POST",
            "/api/o6/archive/tasks",
            self._o6_archive_task_payload(task_id="task-o6-query-filter-safe"),
        )
        self.assertEqual(status, 201)

        invalid_paths = [
            "/api/o6/archive/labels?date=2026-02-30",
            f"/api/o6/archive/labels?robot_id={'a' * 81}",
            "/api/o6/archive/labels?robot_id=/tmp/labels.json",
            "/api/o6/archive/labels?robot_id=https%3A%2F%2Fexample.test%2Flabels%3Ftoken%3Dsecret",
            "/api/o6/archive/labels?task_id=QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0MTIzNDU2Nzg5MA",
            "/api/o6/archive/labels?robot_id=trashbot-001&robot_id=trashbot-002",
            "/api/o6/archive/labels?limit=1&limit=2",
            "/api/o6/archive/labels?status=pending&status=labeled",
        ]
        for path in invalid_paths:
            status, body = self.client.request("GET", path, token="")
            self.assertEqual(status, 400, path)
            self.assertEqual(body["error"]["code"], "bad_request")
            self.assertIn("invalid_label_query_filter", body["error"]["message"])
            encoded = json.dumps(body, ensure_ascii=False).lower()
            self.assertNotIn("secret", encoded)
            self.assertNotIn("/tmp/labels.json", encoded)
            self.assertNotIn("qujdrev", encoded)

        status, detail = self.client.request("GET", "/api/o6/archive/labels/task-o6-query-filter-safe", token="")
        self.assertEqual(status, 200)
        self.assertEqual(detail["label_summary"]["itemized_label_count"], 0)
        self.assertEqual(detail["submit_receipt"]["status"], "blocked_not_proven")

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
            "/api/o6/consumer/tasks/task-o6-consumer-empty?include=field_evidence,labeling,inference,tunnel",
            token="",
        )
        self.assertEqual(status, 200)
        self.assertEqual(empty_detail["labeling"]["labeling_status"], "pending")
        self.assertEqual(empty_detail["labeling"]["label_count"], 0)
        self.assertFalse(empty_detail["labeling"]["local_mock_annotation_submit_written"])
        self.assertEqual(empty_detail["labeling"]["submit_receipt"]["status"], "blocked_not_proven")
        self.assertEqual(empty_detail["labeling"]["dataset_export"]["export_status"], "blocked_not_proven")
        self.assertFalse(empty_detail["labeling"]["dataset_export"]["local_mock_dataset_export_ready"])
        self.assertEqual(empty_detail["inference"]["status"], "absent")
        self.assertEqual(empty_detail["inference"]["inference_status"], "absent")
        self.assertEqual(empty_detail["tunnel_status"]["status"], "blocked_not_proven")
        self.assertEqual(empty_detail["tunnel_status"]["tunnel_status_summary"], "unknown_not_proven")
        self.assertEqual(empty_detail["artifact_media_preflight"]["status"], "blocked_not_proven")
        self.assertEqual(
            empty_detail["artifact_media_preflight"]["consumer_section_names"],
            ["artifact_media_preflight", "route_replay_mvp", "labeling_mvp"],
        )
        self.assertIn(
            "field_evidence_manifest_not_available",
            empty_detail["artifact_media_preflight"]["blocked_reasons"],
        )
        self.assertFalse(empty_detail["artifact_media_preflight"]["real_oss_connected"])
        self.assertEqual(
            empty_detail["delivery_result_evidence"]["schema"],
            relay_module.DELIVERY_RESULT_EVIDENCE_SCHEMA,
        )
        self.assertEqual(empty_detail["delivery_result_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "delivery_result_evidence_not_available",
            empty_detail["delivery_result_evidence"]["blocked_reasons"],
        )
        self.assertEqual(
            empty_detail["route_execution_result_delivery_readiness"]["schema"],
            relay_module.O6_ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        )
        self.assertEqual(
            empty_detail["route_execution_result_delivery_readiness"]["status"],
            "blocked_not_proven",
        )
        self.assertIn(
            "route_execution_result_delivery_readiness_not_available",
            empty_detail["route_execution_result_delivery_readiness"]["blocked_reasons"],
        )
        self.assertEqual(empty_detail["nav2_goal_execution_evidence"]["schema"], relay_module.NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA)
        self.assertEqual(empty_detail["nav2_goal_execution_evidence"]["status"], "blocked_not_proven")
        self.assertIn(
            "nav2_goal_execution_evidence_not_available",
            empty_detail["nav2_goal_execution_evidence"]["blocked_reasons"],
        )

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

        status, unsafe_detail_query = self.client.request(
            "GET",
            "/api/o6/consumer/tasks/task-o6-consumer-empty?include=field_evidence&robot_id=%2Ftmp%2Ffield_evidence",
            token="",
        )
        self.assertEqual(status, 400)
        self.assertEqual(unsafe_detail_query["error"]["code"], "bad_request")

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
        self.assertEqual(reconciliation["terminal_result"]["schema"], "trashbot.cloud_command_terminal_result.v1")
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

    def test_cdn_tls_external_evidence_summary_consumes_1313_artifact_fail_closed(self):
        fixture_path = (
            WORKSPACE_ROOT
            / "sprints"
            / "2026.07.13_13-13_o5_cdn_tls_external_evidence_probe"
            / "artifacts"
            / "cdn_tls_external_evidence_summary.json"
        )

        summary = cdn_tls_external_evidence_artifact_summary(fixture_path)

        self.assertFalse(summary["ok"])
        self.assertEqual(summary["schema"], CDN_TLS_EXTERNAL_EVIDENCE_SCHEMA)
        self.assertEqual(summary["evidence_boundary"], CDN_TLS_EXTERNAL_EVIDENCE_EVIDENCE_BOUNDARY)
        self.assertEqual(summary["reason_code"], "blocked_http_status_not_success_class")
        self.assertTrue(summary["probe_attempted"])
        self.assertTrue(summary["external_request_attempted"])
        self.assertTrue(summary["tls_handshake_observed"])
        self.assertTrue(summary["certificate_valid_for_host"])
        self.assertEqual(summary["http_method"], "HEAD")
        self.assertEqual(summary["http_status_class"], "4xx")
        self.assertEqual(summary["accepted_claim"], "none")
        self.assertTrue(summary["target_host_hash_prefix_present"])
        self.assertFalse(summary["readiness_details"]["delivery_success"])
        self.assertFalse(summary["readiness_details"]["safe_to_control"])

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    CDN_TLS_EXTERNAL_EVIDENCE_ENV: str(fixture_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            cdn_check = checks["cdn_tls_external_evidence"]
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertEqual(cdn_check["status"], "blocked")
            self.assertIn("blocked_http_status_not_success_class", cdn_check["code"])
            self.assertEqual(
                cdn_check["details"]["reason_code"],
                "blocked_http_status_not_success_class",
            )
            self.assertTrue(cdn_check["details"]["readiness_details"]["tls_handshake_observed"])
            self.assertTrue(cdn_check["details"]["readiness_details"]["certificate_valid_for_host"])
            self.assertFalse(cdn_check["details"]["production_ready"])
            self.assertFalse(cdn_check["details"]["delivery_success"])
            self.assertFalse(cdn_check["details"]["safe_to_control"])
            for forbidden in (
                str(fixture_path),
                str(root / "preflight_state.sqlite"),
                "https://",
                "Authorization",
                "Bearer",
                "token=",
                "/tmp/",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_production_cutover_packet_consumes_cdn_tls_external_evidence_slot(self):
        fixture_path = (
            WORKSPACE_ROOT
            / "sprints"
            / "2026.07.13_13-13_o5_cdn_tls_external_evidence_probe"
            / "artifacts"
            / "cdn_tls_external_evidence_summary.json"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            packet_path = root / "cloud_production_cutover_readiness_packet.json"
            result = create_cloud_production_cutover_readiness_packet_artifact(
                packet_path,
                {CDN_TLS_EXTERNAL_EVIDENCE_ENV: str(fixture_path)},
            )
            artifact = json.loads(packet_path.read_text(encoding="utf-8"))
            summary = cloud_production_cutover_readiness_packet_summary(packet_path)
            section = artifact["artifact_statuses"]["cdn_tls_external_evidence"]
            encoded = json.dumps({"result": result, "artifact": artifact, "summary": summary}, ensure_ascii=False)

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["artifact_counts"]["artifact_slots"], 10)
            self.assertEqual(artifact["artifact_counts"]["artifact_present"], 1)
            self.assertEqual(artifact["artifact_counts"]["artifact_ready"], 0)
            self.assertEqual(section["status"], "blocked_not_proven")
            self.assertEqual(section["source_schema"], CDN_TLS_EXTERNAL_EVIDENCE_SCHEMA)
            self.assertEqual(section["evidence_boundary"], CDN_TLS_EXTERNAL_EVIDENCE_EVIDENCE_BOUNDARY)
            self.assertEqual(section["source_ref"]["basename"], "cdn_tls_external_evidence_summary.json")
            self.assertIn("blocked_http_status_not_success_class", section["blocked_reasons"])
            self.assertTrue(section["details"]["tls_handshake_observed"])
            self.assertTrue(section["details"]["certificate_valid_for_host"])
            self.assertEqual(section["details"]["http_status_class"], "4xx")
            self.assertFalse(section["details"]["okr_credit_allowed"])
            self.assertFalse(section["details"]["safe_to_control"])
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["okr_credit_allowed"])
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(artifact["safe_to_control"])
            self.assertEqual(artifact["proof_scope_class"], "software_proof_support_only")
            for forbidden in (
                str(fixture_path),
                str(packet_path),
                "https://",
                "Authorization",
                "Bearer",
                "token=",
                "/tmp/",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_external_evidence_review_decision_packet_and_preflight_are_fail_closed(self):
        tool = _load_cloud_external_evidence_review_decision_tool()
        fixture_root = (
            WORKSPACE_ROOT
            / "pc-tools"
            / "evidence"
            / "fixtures"
            / "cloud_external_evidence_review_decision"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            accepted_path = root / "cloud_external_evidence_review_decision.json"
            accepted_summary_path = root / "cloud_external_evidence_review_decision_summary.json"
            unsafe_path = root / "unsafe_cloud_external_evidence_review_decision.json"
            unsafe_summary_path = root / "unsafe_cloud_external_evidence_review_decision_summary.json"
            packet_path = root / "cloud_production_cutover_readiness_packet.json"

            with mock.patch("sys.stdout", new_callable=io.StringIO):
                accepted_exit = tool.main(
                    [
                        "--intake-json",
                        str(fixture_root / "accepted_intake.json"),
                        "--evidence-ref",
                        "external_evidence_ref_20260524_0001",
                        "--output",
                        str(accepted_path),
                        "--summary-output",
                        str(accepted_summary_path),
                    ]
                )
            self.assertEqual(accepted_exit, 0)
            result = create_cloud_production_cutover_readiness_packet_artifact(
                packet_path,
                {CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ENV: str(accepted_path)},
            )
            artifact = json.loads(packet_path.read_text(encoding="utf-8"))
            review_summary = cloud_external_evidence_review_decision_artifact_summary(accepted_path)
            section = artifact["artifact_statuses"]["cloud_external_evidence_review_decision"]
            preflight = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ENV: str(accepted_path),
                }
            )
            checks = {check["name"]: check for check in preflight["checks"]}

            self.assertTrue(result["ok"])
            self.assertTrue(review_summary["ok"])
            self.assertEqual(review_summary["review_decision"], "accepted_external_evidence_not_proven")
            self.assertEqual(artifact["artifact_counts"]["artifact_slots"], 10)
            self.assertEqual(artifact["artifact_counts"]["artifact_present"], 1)
            self.assertEqual(artifact["artifact_counts"]["artifact_ready"], 1)
            self.assertEqual(section["status"], "software_proof_ready")
            self.assertEqual(section["source_schema"], CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA)
            self.assertEqual(
                section["evidence_boundary"],
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_EVIDENCE_BOUNDARY,
            )
            self.assertEqual(
                section["details"]["review_decision"],
                "accepted_external_evidence_not_proven",
            )
            self.assertFalse(section["details"]["production_ready"])
            self.assertFalse(section["details"]["delivery_success"])
            self.assertFalse(section["details"]["safe_to_control"])
            self.assertEqual(checks["cloud_external_evidence_review_decision"]["status"], "pass")
            self.assertEqual(
                checks["cloud_external_evidence_review_decision"]["details"]["summary_schema"],
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
            )
            self.assertFalse(preflight["production_ready"])
            self.assertTrue(preflight["software_proof_ready"])
            self.assertEqual(
                preflight["evidence_boundary"],
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_EVIDENCE_BOUNDARY,
            )

            with mock.patch("sys.stdout", new_callable=io.StringIO):
                unsafe_exit = tool.main(
                    [
                        "--intake-json",
                        str(fixture_root / "unsafe_intake.json"),
                        "--evidence-ref",
                        "external_evidence_ref_20260524_0001",
                        "--output",
                        str(unsafe_path),
                        "--summary-output",
                        str(unsafe_summary_path),
                    ]
                )
            self.assertEqual(unsafe_exit, 0)
            unsafe_summary = cloud_external_evidence_review_decision_artifact_summary(unsafe_path)
            unsafe_packet = create_cloud_production_cutover_readiness_packet_artifact(
                packet_path,
                {CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ENV: str(unsafe_path)},
            )
            unsafe_artifact = json.loads(packet_path.read_text(encoding="utf-8"))
            unsafe_section = unsafe_artifact["artifact_statuses"]["cloud_external_evidence_review_decision"]
            unsafe_preflight = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "unsafe_preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ENV: str(unsafe_path),
                }
            )
            unsafe_checks = {check["name"]: check for check in unsafe_preflight["checks"]}
            encoded = json.dumps(
                {
                    "summary": unsafe_summary,
                    "packet": unsafe_packet,
                    "artifact": unsafe_artifact,
                    "preflight": unsafe_preflight,
                },
                ensure_ascii=False,
            )

            self.assertFalse(unsafe_summary["ok"])
            self.assertEqual(
                unsafe_summary["reason_code"],
                "rejected_unsafe_external_evidence_not_proven",
            )
            self.assertEqual(unsafe_section["status"], "blocked_not_proven")
            self.assertEqual(unsafe_artifact["artifact_counts"]["artifact_ready"], 0)
            self.assertEqual(unsafe_checks["cloud_external_evidence_review_decision"]["status"], "blocked")
            self.assertFalse(unsafe_preflight["production_ready"])
            for forbidden in (
                str(accepted_path),
                str(unsafe_path),
                str(root / "preflight_state.sqlite"),
                "https://example.invalid",
                "Authorization",
                "Bearer",
                "secret-token",
                "/tmp/",
                "/cmd_vel",
                "/api/base/manual",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cdn_tls_external_evidence_success_class_and_hostile_artifacts_stay_bounded(self):
        fixture_path = (
            WORKSPACE_ROOT
            / "sprints"
            / "2026.07.13_13-13_o5_cdn_tls_external_evidence_probe"
            / "artifacts"
            / "cdn_tls_external_evidence_summary.json"
        )
        base_artifact = json.loads(fixture_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            success_path = root / "cdn_tls_external_evidence_success.json"
            packet_path = root / "cloud_production_cutover_readiness_packet.json"
            success_artifact = json.loads(json.dumps(base_artifact))
            success_artifact.update(
                {
                    "accepted_claim": "o5_cdn_tls_external_evidence_delta",
                    "http_status_class": "2xx",
                    "cdn_tls_external_evidence_status": (
                        "cdn_tls_external_evidence_ready_not_production_proof"
                    ),
                    "blocked_reasons": [],
                }
            )
            success_path.write_text(json.dumps(success_artifact, ensure_ascii=False), encoding="utf-8")

            success_summary = cdn_tls_external_evidence_artifact_summary(success_path)
            result = create_cloud_production_cutover_readiness_packet_artifact(
                packet_path,
                {CDN_TLS_EXTERNAL_EVIDENCE_ENV: str(success_path)},
            )
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            section = packet["artifact_statuses"]["cdn_tls_external_evidence"]
            preflight = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    CDN_TLS_EXTERNAL_EVIDENCE_ENV: str(success_path),
                }
            )
            checks = {check["name"]: check for check in preflight["checks"]}

            self.assertTrue(success_summary["ok"])
            self.assertEqual(section["status"], "software_proof_ready")
            self.assertTrue(packet["software_proof_ready"])
            self.assertFalse(packet["production_ready"])
            self.assertFalse(packet["okr_credit_allowed"])
            self.assertFalse(packet["delivery_success"])
            self.assertFalse(packet["safe_to_control"])
            self.assertTrue(result["ok"])
            self.assertEqual(checks["cdn_tls_external_evidence"]["status"], "pass")
            self.assertFalse(preflight["production_ready"])

            hostile_path = root / "hostile_cdn_tls_external_evidence.json"
            hostile_artifact = json.loads(json.dumps(base_artifact))
            hostile_artifact["safe_to_control"] = True
            hostile_artifact["target_url"] = "https://cdn.example.test/rober/path?token=secret"
            hostile_artifact["response_body"] = "Authorization Bearer token raw response"
            hostile_path.write_text(json.dumps(hostile_artifact, ensure_ascii=False), encoding="utf-8")
            hostile_summary = cdn_tls_external_evidence_artifact_summary(hostile_path)
            hostile_preflight = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "hostile_preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    CDN_TLS_EXTERNAL_EVIDENCE_ENV: str(hostile_path),
                }
            )
            hostile_checks = {check["name"]: check for check in hostile_preflight["checks"]}
            encoded = json.dumps(
                {"summary": hostile_summary, "preflight": hostile_preflight},
                ensure_ascii=False,
            )

            self.assertFalse(hostile_summary["ok"])
            self.assertEqual(hostile_summary["reason_code"], "cdn_tls_external_evidence_invalid")
            self.assertEqual(hostile_checks["cdn_tls_external_evidence"]["status"], "blocked")
            self.assertFalse(hostile_checks["cdn_tls_external_evidence"]["details"]["safe_to_control"])
            for forbidden in (
                str(hostile_path),
                "https://cdn.example.test",
                "token=secret",
                "Authorization",
                "Bearer",
                "raw response",
                "safe_to_control\": true",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_production_cutover_readiness_packet_and_preflight_are_support_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            deployment_path = root / "cloud_deployment_readiness.json"
            ingress_tls_path = root / "cloud_public_ingress_tls.json"
            db_probe_path = root / "cloud_db_queue_external_probe.json"
            migration_path = root / "cloud_worker_migration_rehearsal.json"
            cutover_path = root / "cloud_worker_cutover_drain.json"
            manifest_path = root / "oss_cdn_manifest.json"
            oss_probe_path = root / "oss_cdn_live_probe.json"
            intake_path = root / "external_evidence_intake.json"
            packet_path = root / "cloud_production_cutover_readiness_packet.json"
            base_env = {
                "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN": "replace-with-local-dev-token",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL": "http://127.0.0.1:8088",
                "TRASHBOT_REMOTE_CLOUD_TLS_MODE": "future_reverse_proxy",
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS": "missing",
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
            }

            create_cloud_deployment_readiness_artifact(deployment_path, base_env)
            create_cloud_public_ingress_tls_artifact(ingress_tls_path, base_env)
            create_cloud_db_queue_external_probe_bundle_artifact(db_probe_path, base_env)
            create_cloud_worker_migration_rehearsal_artifact(
                migration_path,
                root / "worker_migration.sqlite",
            )
            create_cloud_worker_cutover_drain_artifact(
                cutover_path,
                root / "worker_cutover.sqlite",
                state_backend="sqlite",
            )
            create_external_evidence_intake_artifact(intake_path, base_env)
            manifest = build_oss_cdn_manifest_payload("robot-local-proof", "task-local-proof")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            oss_probe = build_oss_cdn_live_probe_payload(
                manifest_path,
                probe_fn=lambda _url, timeout_sec=2.0: {
                    "status": "passed",
                    "code": "http_head_observed",
                    "http_status": 200,
                    "reachable": True,
                    "method": "HEAD",
                    "latency_ms": 1,
                },
            )
            oss_probe_path.write_text(json.dumps(oss_probe, ensure_ascii=False), encoding="utf-8")
            packet_env = dict(base_env)
            packet_env.update(
                {
                    "TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT": str(deployment_path),
                    "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT": str(ingress_tls_path),
                    "TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT": str(db_probe_path),
                    "TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT": str(migration_path),
                    "TRASHBOT_REMOTE_CLOUD_WORKER_CUTOVER_DRAIN_ARTIFACT": str(cutover_path),
                    "TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT": str(oss_probe_path),
                    "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT": str(intake_path),
                }
            )

            result = create_cloud_production_cutover_readiness_packet_artifact(packet_path, packet_env)
            artifact = json.loads(packet_path.read_text(encoding="utf-8"))
            summary = cloud_production_cutover_readiness_packet_summary(packet_path)
            preflight_env = {
                "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                "TRASHBOT_REMOTE_CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_ARTIFACT": str(packet_path),
            }
            payload = production_preflight_payload(preflight_env)
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps(
                {"result": result, "artifact": artifact, "summary": summary, "preflight": payload},
                ensure_ascii=False,
            )

            self.assertTrue(result["ok"])
            self.assertTrue(summary["ok"])
            self.assertEqual(artifact["schema"], CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_SCHEMA)
            self.assertEqual(
                artifact["evidence_boundary"],
                CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_EVIDENCE_BOUNDARY,
            )
            self.assertEqual(artifact["status"], "blocked_not_production_ready")
            self.assertFalse(artifact["production_ready"])
            self.assertFalse(artifact["okr_credit_allowed"])
            self.assertEqual(artifact["proof_scope_class"], "software_proof_support_only")
            self.assertFalse(artifact["connects_cloud_production"])
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(artifact["safe_to_control"])
            self.assertFalse(artifact["primary_actions_enabled"])
            self.assertFalse(artifact["robot_control_executed"])
            self.assertEqual(artifact["artifact_counts"]["artifact_slots"], 10)
            self.assertGreaterEqual(artifact["artifact_counts"]["artifact_ready"], 7)
            self.assertEqual(
                artifact["artifact_statuses"]["cloud_external_probe"]["status"],
                "missing",
            )
            self.assertEqual(
                artifact["artifact_statuses"]["cdn_tls_external_evidence"]["status"],
                "missing",
            )
            self.assertIn("real_public_https_tls_probe", artifact["next_required_evidence"])
            self.assertIn("next_live_command", summary)
            self.assertFalse(payload["production_ready"])
            self.assertTrue(payload["software_proof_ready"])
            self.assertEqual(payload["evidence_boundary"], CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["cloud_production_cutover_readiness_packet"]["status"], "pass")
            self.assertFalse(
                checks["cloud_production_cutover_readiness_packet"]["details"]["production_ready"]
            )
            self.assertFalse(
                checks["cloud_production_cutover_readiness_packet"]["details"]["okr_credit_allowed"]
            )
            for basename in (
                "cloud_deployment_readiness.json",
                "cloud_worker_cutover_drain.json",
                "oss_cdn_live_probe.json",
            ):
                self.assertIn(basename, encoded)
            for forbidden in (
                str(packet_path),
                str(cutover_path),
                str(root / "preflight_state.sqlite"),
                "replace-with-local-dev-token",
                "Authorization",
                "Bearer",
                "token",
                "https://",
                "http://127.0.0.1",
                "postgres://",
                "queue URL",
                "raw payload",
                "/tmp/",
                "/dev/ttyUSB0",
                "UART",
                "WAVE ROVER",
                "ROS topic",
                "/cmd_vel",
            ):
                self.assertNotIn(forbidden, encoded)

    def test_cloud_production_cutover_readiness_packet_fails_closed_for_hostile_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            hostile_path = root / "hostile_cloud_production_cutover_readiness_packet.json"
            base_env = {"TRASHBOT_REMOTE_CLOUD_STATE": str(root / "relay_state.sqlite")}
            hostile = build_cloud_production_cutover_readiness_packet_payload(
                base_env,
                generated_at="2026-07-10T09:22:00Z",
            )
            hostile["connects_cloud_production"] = True
            hostile["artifact_statuses"]["cloud_external_probe"]["source_ref"]["basename"] = (
                "https://relay.example.invalid/token.json"
            )
            hostile["next_live_command"] = "Authorization Bearer token /dev/ttyUSB0 /cmd_vel traceback"
            hostile["checksum"] = _sha256_checksum({key: value for key, value in hostile.items() if key != "checksum"})
            hostile_path.write_text(json.dumps(hostile, ensure_ascii=False), encoding="utf-8")

            summary = cloud_production_cutover_readiness_packet_summary(hostile_path)
            payload = production_preflight_payload(
                {
                    "TRASHBOT_REMOTE_CLOUD_STATE": str(root / "preflight_state.sqlite"),
                    "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND": "sqlite",
                    "TRASHBOT_REMOTE_CLOUD_PRODUCTION_CUTOVER_READINESS_PACKET_ARTIFACT": str(hostile_path),
                }
            )
            checks = {check["name"]: check for check in payload["checks"]}
            encoded = json.dumps({"summary": summary, "preflight": payload}, ensure_ascii=False)

            self.assertFalse(summary["ok"])
            self.assertEqual(checks["cloud_production_cutover_readiness_packet"]["status"], "blocked")
            self.assertEqual(
                checks["cloud_production_cutover_readiness_packet"]["code"],
                "cloud_production_cutover_readiness_packet_invalid",
            )
            for forbidden in (
                str(hostile_path),
                str(root / "preflight_state.sqlite"),
                "Authorization",
                "Bearer",
                "token",
                "https://relay.example.invalid",
                "/dev/ttyUSB0",
                "/cmd_vel",
                "traceback",
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
