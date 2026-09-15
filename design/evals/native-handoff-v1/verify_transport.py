"""Loopback endpoint counterexample; no physical-device or agent validation."""
import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import threading
from urllib.request import ProxyHandler, build_opener


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"candidate": self.server.candidate, "route": "review"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@contextmanager
def target(candidate):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.candidate = candidate
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive(), "fixture server did not terminate"


def verify():
    source = Path(__file__)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    opener = build_opener(ProxyHandler({}))  # Keep fixture traffic on loopback.

    def observe(endpoint):
        with opener.open(endpoint, timeout=5) as response:
            return {"status": response.status, **json.load(response)}

    with target("candidate-a") as expected, target("candidate-b") as stale:
        server_check = observe(expected)
        wrong_client_target = observe(stale)
        corrected_client_target = observe(expected)
        assert server_check == {"status": 200, "candidate": "candidate-a", "route": "review"}
        assert wrong_client_target["status"] == server_check["status"]
        assert wrong_client_target["route"] == server_check["route"]
        assert wrong_client_target["candidate"] != server_check["candidate"]
        assert corrected_client_target == server_check
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    return {"schema": 1, "python": platform.python_version(), "platform": platform.system(),
        "claim": "Healthy server checks and matching HTTP status/route do not identify a client's selected target.",
        "source_sha256": before, "source_unchanged": True, "fixture_servers_closed": True,
        "server_check": server_check, "wrong_client_target": wrong_client_target,
        "corrected_client_target": corrected_client_target,
        "physical_device_trials": 0, "agent_trials": 0, "complete": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("choose a new evidence file")
    result = verify()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("Loopback counterexample passed; 0 physical-device or agent trials.")
