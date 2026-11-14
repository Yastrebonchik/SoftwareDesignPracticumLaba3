#!/usr/bin/env python3
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent


def compose(*args, capture=False):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT,
                            text=True, capture_output=capture, stdin=subprocess.DEVNULL)
    if result.returncode and capture:
        print(result.stdout, flush=True)
        print(result.stderr, flush=True)
    result.check_returncode()
    return result.stdout.strip() if capture else None


def request(path, method="GET", data=None, expected=200):
    port = compose("port", "nginx", "80", capture=True).splitlines()[0].rsplit(":", 1)[1]
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        content = response.read()
        assert response.status == expected, (method, path, response.status, content)
        return json.loads(content) if content else None


def wait_health():
    for attempt in range(60):
        try:
            if request("/health") == {"status": "UP"}:
                return
        except (AssertionError, urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise AssertionError("Application did not become healthy")


def wait_containers():
    subprocess.run(["bash", "scripts/wait-ready.sh"], cwd=ROOT, check=True)


def deploy():
    output = compose("exec", "-T", "ansible", "ansible-playbook", "site.yml", capture=True)
    (ROOT / "docs" / "checks" / "first-deploy.txt").write_text(output + "\n")
    print(output, flush=True)
    wait_containers()


def check_containers():
    ids = compose("ps", "-q", capture=True).split()
    containers = json.loads(subprocess.check_output(["docker", "inspect", *ids], text=True))
    assert len(containers) == 4
    networks = set()
    services = set()
    for container in containers:
        service = container["Config"]["Labels"]["com.docker.compose.service"]
        services.add(service)
        assert container["State"]["Health"]["Status"] == "healthy", service
        attached = set(container["NetworkSettings"]["Networks"])
        assert len(attached) == 1, (service, attached)
        networks.update(attached)
        bindings = container["HostConfig"]["PortBindings"] or {}
        assert set(bindings) == ({"80/tcp"} if service == "nginx" else set()), (service, bindings)
    assert services == {"ansible", "nginx", "app", "db"}
    assert len(networks) == 1
    count = compose("exec", "-T", "app", "pgrep", "-fc", "^java -jar /opt/notes/app.jar$", capture=True)
    assert count == "1", count
    owner = compose("exec", "-T", "app", "sh", "-c",
                    'ps -o user= -p "$(cat /opt/notes/run/app.pid)"', capture=True)
    assert owner == "notes", owner
    print("PASS: four healthy containers, one network, only Nginx publishes a port, one non-root JVM", flush=True)


def check_idempotence():
    before = compose("exec", "-T", "app", "cat", "/opt/notes/run/app.pid", capture=True)
    nginx_before = compose("exec", "-T", "nginx", "cat", "/run/nginx.pid", capture=True)
    output = compose("exec", "-T", "ansible", "ansible-playbook", "site.yml", capture=True)
    checks = ROOT / "docs" / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    (checks / "idempotence.txt").write_text(output + "\n")
    recap = output.split("PLAY RECAP")[-1]
    for host in ("app", "nginx"):
        pattern = rf"^{host}\s+:\s+ok=\d+\s+changed=0\s+unreachable=0\s+failed=0"
        assert re.search(pattern, recap, re.MULTILINE), recap
    assert before == compose("exec", "-T", "app", "cat", "/opt/notes/run/app.pid", capture=True)
    assert nginx_before == compose("exec", "-T", "nginx", "cat", "/run/nginx.pid", capture=True)
    print("PASS: second playbook run has changed=0; application and Nginx PIDs are unchanged", flush=True)


def main():
    compose("exec", "-T", "ansible", "ansible-playbook", "--syntax-check", "site.yml")
    wait_containers()
    check_containers()
    check_idempotence()
    marker = f"Lab 3 persistence {time.time_ns()}"
    note = request("/notes", "POST", {"text": marker}, 201)
    path = f"/notes/{int(note['id'])}"
    assert request(path)["text"] == marker
    assert any(item["id"] == note["id"] for item in request("/notes"))
    for invalid in ({}, {"text": "   "}, {"text": "x" * 1001}):
        request("/notes", "POST", invalid, 400)
    sql = f"SELECT text FROM notes WHERE id = {int(note['id'])}"
    stored = compose("exec", "-T", "db", "sh", "-c",
                     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc ' + shlex.quote(sql), capture=True)
    assert stored == marker
    print("PASS: CRUD, validation and actual storage in PostgreSQL", flush=True)

    compose("restart")
    wait_containers()
    assert request(path)["text"] == marker
    print("PASS: all services recover after container restart; note is preserved", flush=True)

    compose("down")
    compose("up", "-d")
    deploy()
    assert request(path)["text"] == marker
    print("PASS: deployment to recreated servers; PostgreSQL data survives", flush=True)

    compose("stop", "db")
    try:
        assert request("/health", expected=503) == {"status": "DOWN"}
    finally:
        compose("start", "db")
        wait_health()
    assert request(path)["text"] == marker
    print("PASS: database outage is detected; application recovers", flush=True)

    request(path, "DELETE", expected=204)
    request(path, expected=404)
    request(path, "DELETE", expected=404)
    wait_containers()
    check_containers()
    compose("ps")
    print("ALL CHECKS PASSED", flush=True)


if __name__ == "__main__":
    main()
