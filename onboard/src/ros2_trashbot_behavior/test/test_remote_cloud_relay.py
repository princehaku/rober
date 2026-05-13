import json
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
    external_evidence_intake_artifact_summary,
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


class RemoteCloudRelayHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = pathlib.Path(self.tmp.name) / "relay_state.json"
        self.server = build_server("127.0.0.1", 0, self.state_path, "phone-token")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = RelayHttpClient(f"http://127.0.0.1:{self.server.server_address[1]}")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)
        self.tmp.cleanup()

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


if __name__ == "__main__":
    unittest.main()
