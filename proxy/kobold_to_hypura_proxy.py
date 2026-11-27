import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _read_json(request_handler: BaseHTTPRequestHandler):
    length = int(request_handler.headers.get("Content-Length", "0"))
    raw = request_handler.rfile.read(length) if length > 0 else b"{}"
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def _write_json(request_handler: BaseHTTPRequestHandler, status_code: int, body: dict) -> bool:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        request_handler.send_response(status_code)
        request_handler.send_header("Content-Type", "application/json; charset=utf-8")
        request_handler.send_header("Content-Length", str(len(encoded)))
        request_handler.end_headers()
        request_handler.wfile.write(encoded)
        return True
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
        # Client disconnected before response was fully written.
        return False


class KoboldToHypuraProxyHandler(BaseHTTPRequestHandler):
    hypura_base_url = "http://127.0.0.1:8080"
    last_result_text = ""
    timeout_sec = 120
    generation_in_progress = False
    result_lock = threading.Lock()

    @classmethod
    def _set_state(cls, *, text=None, in_progress=None):
        with cls.result_lock:
            if text is not None:
                cls.last_result_text = text
            if in_progress is not None:
                cls.generation_in_progress = in_progress

    @classmethod
    def _get_state(cls):
        with cls.result_lock:
            return cls.last_result_text, cls.generation_in_progress

    def log_message(self, fmt, *args):
        # Keep logs concise in console usage.
        print("[proxy] " + (fmt % args))

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/v1/model":
            self._handle_model()
            return

        if path == "/api/extra/generate/check":
            self._handle_check()
            return

        _write_json(self, 404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/v1/generate":
            self._handle_generate()
            return

        if path == "/api/extra/abort":
            self._handle_abort()
            return

        _write_json(self, 404, {"error": "not found"})

    def _hypura_get(self, path: str):
        req = Request(f"{self.hypura_base_url}{path}", method="GET")
        with urlopen(req, timeout=self.timeout_sec) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))

    def _hypura_post(self, path: str, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(
            f"{self.hypura_base_url}{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=self.timeout_sec) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))

    def _handle_model(self):
        status_code = 200
        response_body = {"result": "unknown"}
        try:
            _, tags = self._hypura_get("/api/tags")
            models = tags.get("models", [])
            if models:
                first = models[0]
                name = first.get("name") or first.get("model") or "unknown"
            else:
                name = "unknown"
            response_body = {"result": name}
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            status_code = 502
            response_body = {"error": f"failed to reach hypura: {exc}"}
        except Exception as exc:
            status_code = 500
            response_body = {"error": f"proxy error: {exc}"}

        _write_json(self, status_code, response_body)

    def _handle_generate(self):
        payload = _read_json(self)
        # `/api/extra/generate/stream` expects Kobold-style payload.
        stream_payload = {
            "prompt": payload.get("prompt", ""),
            "max_length": payload.get("max_length", 256),
            "temperature": payload.get("temperature", 1.0),
            "top_k": payload.get("top_k", 40),
            "top_p": payload.get("top_p", 0.9),
            "rep_pen": payload.get("rep_pen", 1.1),
            "rep_pen_range": payload.get("rep_pen_range", 64),
            "rep_pen_slope": payload.get("rep_pen_slope", 0.0),
            "tfs": payload.get("tfs", 1.0),
            "top_a": payload.get("top_a", 0.0),
            "typical": payload.get("typical", 1.0),
            "min_p": payload.get("min_p", 0.0),
            "sampler_order": payload.get("sampler_order", [6, 0, 1, 3, 4, 2, 5]),
            "stop_sequence": payload.get("stop_sequence", []),
        }

        status_code = 200
        response_body = {"results": [{"text": ""}]}
        try:
            type(self)._set_state(text="", in_progress=True)
            data = json.dumps(stream_payload, ensure_ascii=False).encode("utf-8")
            req = Request(
                f"{self.hypura_base_url}/api/extra/generate/stream",
                data=data,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            text_parts = []
            with urlopen(req, timeout=self.timeout_sec) as resp:
                while True:
                    raw = resp.readline()
                    if not raw:
                        break
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    token = obj.get("token")
                    if token:
                        text_parts.append(token)
                        type(self)._set_state(text="".join(text_parts))
            text = "".join(text_parts)
            type(self)._set_state(text=text)
            response_body = {"results": [{"text": text}]}
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            status_code = 502
            response_body = {"error": f"failed to reach hypura: {exc}"}
        except Exception as exc:
            status_code = 500
            response_body = {"error": f"proxy error: {exc}"}
        finally:
            type(self)._set_state(in_progress=False)

        _write_json(self, status_code, response_body)

    def _handle_check(self):
        status_code = 200
        text, in_progress = type(self)._get_state()
        response_body = {"results": [{"text": text}], "in_progress": in_progress}
        _write_json(self, status_code, response_body)

    def _handle_abort(self):
        status_code = 200
        response_body = {"success": True}
        try:
            _, response_data = self._hypura_post("/api/extra/abort", {})
            if isinstance(response_data, dict):
                response_body = {"success": bool(response_data.get("success", True))}
            type(self)._set_state(in_progress=False)
        except Exception as exc:
            status_code = 502
            response_body = {"error": f"failed to reach hypura abort: {exc}"}
        _write_json(self, status_code, response_body)


def parse_listen(listen: str):
    if ":" not in listen:
        raise ValueError("listen must be host:port")
    host, port_str = listen.rsplit(":", 1)
    return host, int(port_str)


def main():
    parser = argparse.ArgumentParser(description="Kobold API -> Hypura API proxy")
    parser.add_argument("--listen", default="127.0.0.1:5001", help="host:port to listen")
    parser.add_argument("--hypura", default="127.0.0.1:8080", help="hypura host:port")
    parser.add_argument("--timeout", type=int, default=120, help="request timeout seconds")
    args = parser.parse_args()

    host, port = parse_listen(args.listen)
    KoboldToHypuraProxyHandler.hypura_base_url = f"http://{args.hypura}"
    KoboldToHypuraProxyHandler.timeout_sec = args.timeout

    server = ThreadingHTTPServer((host, port), KoboldToHypuraProxyHandler)
    print(f"[proxy] listening on http://{host}:{port}")
    print(f"[proxy] forwarding to {KoboldToHypuraProxyHandler.hypura_base_url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
