import xml.etree.ElementTree as ET
from datetime import datetime

import gen

AT = datetime(2026, 11, 2, 14, 0, tzinfo=gen.PHT)


def test_all_passing():
    svg = gen.pipeline([("onehealth.my", True, "200 · 2.1s · https ok"), ("qa-portfolio", True, "200 · 0.4s · https ok")], AT)
    ET.fromstring(svg)
    assert "all checks passing" in svg and "2/2" in svg and "02 nov, 14:00 pht" in svg and "✗" not in svg


def test_site_down_shows_honestly():
    svg = gen.pipeline([("onehealth.my", False, "timed out"), ("qa-portfolio", True, "200 · 0.4s · https ok")], AT)
    assert "1 check failing" in svg and "1/2" in svg and "✗" in svg and "timed out" in svg


def test_unreachable_host():
    assert gen.check("https://nothing.invalid/", timeout=5) == (False, "unreachable")


# ---- QA additions: check() against local servers
import http.server, socket, threading


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redir":
            self.send_response(301); self.send_header("Location", "/ok"); self.end_headers()
        else:
            self.send_response({"/404": 404, "/500": 500}.get(self.path, 200)); self.end_headers()

    def log_message(self, *a):
        pass


def _serve():
    s = http.server.HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_port}"


def test_check_http_statuses():
    s, u = _serve()
    try:
        for code in (404, 500):
            ok, d = gen.check(f"{u}/{code}")
            assert ok is False and str(code) in d, d
        assert gen.check(u + "/redir")[0] is True
        assert gen.check(u + "/ok")[0] is True
    finally:
        s.shutdown()


def test_check_timeout_silent_socket():
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    try:
        assert gen.check(f"http://127.0.0.1:{srv.getsockname()[1]}/", timeout=1) == (False, "timed out")
    finally:
        srv.close()


def test_check_connection_refused():
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); p = srv.getsockname()[1]; srv.close()
    ok, d = gen.check(f"http://127.0.0.1:{p}/", timeout=2)
    assert ok is False and d in ("unreachable", "timed out")  # Windows retries refused connects -> timed out


def test_check_bad_cert():
    assert gen.check("https://expired.badssl.com/", timeout=10) == (False, "https cert invalid")


def test_check_garbage_url_does_not_raise():
    assert gen.check("not a url")[0] is False


def test_pipeline_plural_all_failing_escape_height():
    r = [("a&b", False, "<x>"), ("c", False, "unreachable")]
    svg = gen.pipeline(r, AT)
    ET.fromstring(svg)
    assert "2 checks failing" in svg and "0/2" in svg and "a&amp;b" in svg and "&lt;x&gt;" in svg
    import re
    h = int(re.search(r'height="(\d+)"', svg).group(1))
    assert max(int(y) for y in re.findall(r' y="(\d+)" font-size="14"', svg)) + 14 < h


def test_pipeline_empty_not_false_claim():
    svg = gen.pipeline([], AT)
    ET.fromstring(svg)
    assert "all checks passing" not in svg, "empty results claims all checks passing (0/0)"
