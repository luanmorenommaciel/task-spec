#!/usr/bin/env bash
set -euo pipefail

read_secret() {
  local path="$1"
  [[ -f "$path" ]] || { echo "missing capability file: $path" >&2; exit 70; }
  tr -d '\r\n' <"$path"
}

proxy() {
  exec python3 -u - <<'PY'
import datetime, http.server, json, os, pathlib, urllib.error, urllib.request

capability = pathlib.Path(os.environ["TASKMESH_CAPABILITY_FILE"]).read_text().strip()
upstream_token = pathlib.Path(os.environ["TASKMESH_UPSTREAM_TOKEN_FILE"]).read_text().strip()
upstream = os.environ["TASKMESH_UPSTREAM_URL"].rstrip("/")
allowed_model = os.environ["TASKMESH_ALLOWED_MODEL"]
expires_at = datetime.datetime.fromisoformat(os.environ["TASKMESH_EXPIRES_AT"].replace("Z", "+00:00"))
allowed_paths = {"/healthz", "/v1/models", "/v1/pi/stream"}

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "TaskMeshCredentialProxy/1.0"
    def log_message(self, *_):
        return
    def answer(self, status, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def authorized(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        return now < expires_at and self.headers.get("authorization") == "Bearer " + capability
    def dispatch(self):
        path = self.path.split("?", 1)[0]
        if path not in allowed_paths:
            return self.answer(404, {"error": "route_not_allowed"})
        if path != "/healthz" and not self.authorized():
            return self.answer(401, {"error": "attempt_capability_invalid_or_expired"})
        body = b""
        if self.command == "POST":
            length = int(self.headers.get("content-length", "0"))
            if length > 2 * 1024 * 1024:
                return self.answer(413, {"error": "request_too_large"})
            body = self.rfile.read(length)
            try:
                value = json.loads(body)
            except json.JSONDecodeError:
                return self.answer(400, {"error": "invalid_json"})
            if value.get("model") != allowed_model:
                return self.answer(403, {"error": "model_outside_dispatch_decision"})
        if path == "/healthz":
            return self.answer(200, {"status": "ok", "model": allowed_model})
        headers = {"authorization": "Bearer " + upstream_token, "content-type": self.headers.get("content-type", "application/json")}
        request = urllib.request.Request(upstream + path, data=body if self.command == "POST" else None, method=self.command, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
                if len(raw) > 4 * 1024 * 1024:
                    return self.answer(502, {"error": "upstream_response_too_large"})
                self.send_response(response.status)
                self.send_header("content-type", response.headers.get("content-type", "application/json"))
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        except urllib.error.HTTPError as error:
            raw = error.read(1024 * 1024)
            self.send_response(error.code)
            self.send_header("content-type", error.headers.get("content-type", "application/json"))
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except Exception:
            self.answer(502, {"error": "upstream_unavailable"})
    do_GET = dispatch
    do_POST = dispatch

http.server.ThreadingHTTPServer(("0.0.0.0", 4000), Handler).serve_forever()
PY
}

worker() {
  export TASKMESH_ATTEMPT_TOKEN="$(read_secret "$TASKMESH_CAPABILITY_FILE")"
  if [[ "${TASKMESH_FAKE_WORKER:-0}" == "1" ]]; then
    [[ -z "${TASKSPEC_SIGNING_KEY:-}" && -z "${TASKSPEC_MESH_GATEWAY_TOKEN:-}" ]]
    [[ ! -e /var/run/docker.sock && ! -e /host-home ]]
    [[ "$(omp --version)" == "omp/${TASKMESH_OMP_VERSION}" ]]
    if [[ -n "${TASKMESH_FAKE_WORKER_DELAY_SEC:-}" ]]; then sleep "$TASKMESH_FAKE_WORKER_DELAY_SEC"; fi
    python3 - <<'PY'
import json, os, pathlib, urllib.request
token = os.environ["TASKMESH_ATTEMPT_TOKEN"]
model = os.environ["TASKMESH_MODEL"]
request = urllib.request.Request(
    "http://credential-proxy:4000/v1/pi/stream",
    data=json.dumps({"model": model, "messages": [{"role": "user", "content": "TaskMesh isolation probe"}]}).encode(),
    headers={"authorization": "Bearer " + token, "content-type": "application/json"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    if response.status != 200:
        raise SystemExit("credential proxy rejected the fixed route")
handoff = json.loads(pathlib.Path(os.environ["TASKMESH_HANDOFF_PATH"]).read_text())
scope = handoff["write_scope"]
paths = scope.get("creates_paths") or scope.get("touches_paths") or []
if not paths:
    raise SystemExit("fake worker requires one authorized write path")
target = pathlib.Path("/workspace", paths[0]).resolve()
root = pathlib.Path("/workspace").resolve()
if root not in target.parents:
    raise SystemExit("authorized path escaped workspace")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("completed by autonomous TaskMesh\n", encoding="utf-8")
print(json.dumps({"type": "taskmesh.fake.completed", "path": str(target.relative_to(root)), "model": model}))
PY
    return
  fi

  mkdir -p /tmp/omp/agent /tmp/home
  cat >/tmp/omp/agent/models.yml <<EOF
providers:
  taskmesh:
    baseUrl: http://credential-proxy:4000
    apiKey: TASKMESH_ATTEMPT_TOKEN
    api: openai-responses
    transport: pi-native
    models:
      - id: ${TASKMESH_MODEL}
        name: TaskMesh ${TASKMESH_MODEL}
        api: openai-responses
        reasoning: true
        input: [text]
        cost: {input: 0, output: 0, cacheRead: 0, cacheWrite: 0}
        contextWindow: 200000
        maxTokens: 32768
EOF
  export HOME=/tmp/home PI_CONFIG_DIR=/tmp/omp PI_CODING_AGENT_DIR=/tmp/omp/agent
  exec omp --cwd /workspace --model "taskmesh/${TASKMESH_MODEL}" --mode json --no-session \
    --no-extensions --no-skills --no-rules --tools read,bash,edit,write,grep,glob,lsp \
    --approval-mode write --max-time "${TASKMESH_TIMEOUT_SEC}s" -p "$(cat "$TASKMESH_PROMPT_PATH")"
}

case "${1:-}" in
  proxy) proxy ;;
  worker) worker ;;
  *) echo "usage: worker-entrypoint.sh proxy|worker" >&2; exit 64 ;;
esac
