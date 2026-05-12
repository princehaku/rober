import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ros2_trashbot_behavior"))

from ros2_trashbot_behavior.remote_cloud_relay import (  # noqa: E402
    BACKUP_RESTORE_EVIDENCE_BOUNDARY,
    FileBackedRelayStore,
    OSS_CDN_BASE_URL,
    OSS_CDN_BUCKET,
    OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
    OSS_CDN_MANIFEST_SCHEMA,
    OSS_CDN_REGION,
    PREFLIGHT_EVIDENCE_BOUNDARY,
    PROTOCOL_VERSION,
    SQLITE_EVIDENCE_BOUNDARY,
    SQLiteRelayStore,
    backup_artifact_summary,
    backup_restore_drill_payload,
    build_oss_cdn_manifest_payload,
    build_server,
    create_oss_cdn_manifest_artifact,
    create_sqlite_backup_artifact,
    oss_cdn_manifest_summary,
    production_preflight_payload,
    restore_sqlite_backup_artifact,
)


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
        self.assertEqual(payload["evidence_boundary"], PREFLIGHT_EVIDENCE_BOUNDARY)
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
        store = SQLiteRelayStore("/dev/null/relay_state.sqlite")
        self.assertFalse(store.state_store_writable())
        with self.assertRaisesRegex(ValueError, "sqlite state store is not ready"):
            store.next_command("trashbot-001", "")


class RemoteCloudRelayPreflightTest(unittest.TestCase):
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
            self.assertEqual(payload["evidence_boundary"], PREFLIGHT_EVIDENCE_BOUNDARY)
            self.assertEqual(checks["credential_provisioning"]["status"], "blocked")
            self.assertEqual(checks["tls_public_ingress"]["status"], "blocked")
            self.assertEqual(checks["oss_cdn"]["status"], "blocked")
            self.assertEqual(checks["state_store"]["status"], "warning")
            self.assertEqual(checks["backup_restore_drill"]["status"], "warning")
            self.assertEqual(checks["phone_safe_output"]["status"], "pass")
            self.assertIn("software_proof_docker_preflight_gate", encoded)
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
            "TRASHBOT_REMOTE_CLOUD_STATE": "/dev/null/relay_state.json",
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
            self.assertEqual(payload["evidence_boundary"], SQLITE_EVIDENCE_BOUNDARY)
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


if __name__ == "__main__":
    unittest.main()
