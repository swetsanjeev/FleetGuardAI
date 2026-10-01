import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_SERVICES = {
    "postgres",
    "mongodb",
    "redis",
    "kafka",
    "mqtt",
    "kafka-ui",
    "flink-jobmanager",
    "flink-taskmanager",
    "api",
    "simulator",
    "ingestion",
    "ml-service",
    "ai-agent",
    "frontend",
    "prometheus",
    "loki",
    "tempo",
    "grafana",
    "object-storage",
    "database-init",
}


def run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)


def require(name: str, *command: str) -> bool:
    result = run(*command)
    if result.returncode == 0:
        print(f"PASS {name}")
        return True
    print(f"FAIL {name}: {(result.stderr or result.stdout).strip()}")
    return False


def main() -> int:
    ok = True
    ids_result = run("docker", "compose", "ps", "-q", "--all")
    if ids_result.returncode:
        print(ids_result.stderr.strip())
        return ids_result.returncode
    container_ids = ids_result.stdout.split()
    if not container_ids:
        print("No containers found. Start the stack with: python scripts/dev.py up")
        return 1

    inspect = run("docker", "inspect", *container_ids)
    if inspect.returncode:
        print(inspect.stderr.strip())
        return inspect.returncode
    containers = json.loads(inspect.stdout)
    found = set()
    for container in containers:
        labels = container["Config"].get("Labels") or {}
        service = labels.get("com.docker.compose.service", "unknown")
        found.add(service)
        state = container["State"]
        if service == "database-init":
            health = "completed" if state.get("ExitCode") == 0 else "failed"
            passed = state.get("Status") == "exited" and state.get("ExitCode") == 0
        else:
            health = state.get("Health", {}).get("Status", "missing")
            passed = state.get("Status") == "running" and health == "healthy"
        print(f"{'PASS' if passed else 'FAIL'} container {service}: {state.get('Status')} / {health}")
        ok = ok and passed
    for missing in sorted(ROOT_SERVICES - found):
        print(f"FAIL container {missing}: not found")
        ok = False

    checks = [
        ("PostgreSQL app connection", "docker", "compose", "exec", "-T", "api", "python", "-c", "from fleetguard_db.database import check_postgres; check_postgres()"),
        ("MongoDB app connection", "docker", "compose", "exec", "-T", "api", "python", "-c", "from fleetguard_db.mongo import check_mongodb; check_mongodb()"),
        ("Redis app connection", "docker", "compose", "exec", "-T", "redis", "sh", "-ec", "REDISCLI_AUTH=\"$REDIS_PASSWORD\" redis-cli ping"),
        ("Kafka broker", "docker", "compose", "exec", "-T", "kafka", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "kafka:9092", "--list"),
        ("MQTT broker", "docker", "compose", "exec", "-T", "mqtt", "sh", "-ec", "curl -fsS http://127.0.0.1:18083/status | grep -q 'is started'"),
        ("S3-compatible object storage", "docker", "compose", "exec", "-T", "object-storage", "curl", "--silent", "--fail", "http://127.0.0.1:9333/cluster/status"),
    ]
    for name, *command in checks:
        result = run(*command)
        passed = result.returncode == 0
        print(f"{'PASS' if passed else 'FAIL'} {name}" + (f": {(result.stderr or result.stdout).strip()}" if not passed else ""))
        ok = ok and passed

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())