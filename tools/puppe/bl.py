"""Kleiner Client für das MCP-for-Blender-Add-on (Socket 127.0.0.1:9876).
Aufruf: python bl.py <skript.py> [weiteres.py ...]  -> führt die Dateien nacheinander im offenen Blender aus."""
import json
import socket
import sys


def send(cmd, params=None, timeout=590):
    s = socket.create_connection(("127.0.0.1", 9876), timeout=10)
    s.settimeout(timeout)
    s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode("utf-8"))
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            r = json.loads(buf.decode("utf-8"))
            s.close()
            return r
        except ValueError:
            continue
    s.close()
    return json.loads(buf.decode("utf-8"))


if __name__ == "__main__":
    code = "\n\n".join(open(p, encoding="utf-8").read() for p in sys.argv[1:])
    r = send("execute_code", {"code": code})
    if r.get("status") != "success":
        msg = r.get("message", "")
        try:
            d = json.loads(msg)
            print("FEHLER", d.get("exception_type"), d.get("message"))
            print(d.get("traceback"))
        except ValueError:
            print("FEHLER", msg)
        sys.exit(1)
    print(r["result"].get("result", ""))
