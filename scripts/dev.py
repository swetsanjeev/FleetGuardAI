import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
ENV_TEMPLATE = ROOT / ".env.example"
GENERATED_SECRETS = {
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_APP_USER",
    "POSTGRES_APP_PASSWORD",
    "POSTGRES_MIGRATION_USER",
    "POSTGRES_MIGRATION_PASSWORD",
    "MONGO_ROOT_USERNAME",
    "MONGO_ROOT_PASSWORD",
    "MONGODB_APP_USER",
    "MONGODB_APP_PASSWORD",
    "REDIS_PASSWORD",
    "OBJECT_STORAGE_ACCESS_KEY",
    "OBJECT_STORAGE_SECRET_KEY",
    "GRAFANA_ADMIN_USER",
    "GRAFANA_ADMIN_PASSWORD",
    "EMQX_NODE_COOKIE",
}


def ensure_environment() -> None:
    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    present_keys = {line.partition("=")[0] for line in lines if "=" in line}
    for template_line in ENV_TEMPLATE.read_text(encoding="utf-8").splitlines():
        key, separator, _ = template_line.partition("=")
        if separator and key not in present_keys:
            lines.append(template_line)
            present_keys.add(key)

    updated = []
    for line in lines:
        key, separator, value = line.partition("=")
        if separator and key in GENERATED_SECRETS and not value:
            value = secrets.token_urlsafe(32)
            line = f"{key}={value}"
        updated.append(line)

    values = {line.partition("=")[0]: line.partition("=")[2] for line in updated if "=" in line}
    if not values.get("DATABASE_URL"):
        values["DATABASE_URL"] = (
            f"postgresql+psycopg://{quote(values['POSTGRES_APP_USER'], safe='')}:{quote(values['POSTGRES_APP_PASSWORD'], safe='')}"
            f"@postgres:5432/{quote(values['POSTGRES_DB'], safe='')}"
        )
    if not values.get("DATABASE_ADMIN_URL"):
        values["DATABASE_ADMIN_URL"] = (
            f"postgresql+psycopg://{quote(values['POSTGRES_USER'], safe='')}:{quote(values['POSTGRES_PASSWORD'], safe='')}"
            f"@postgres:5432/{quote(values['POSTGRES_DB'], safe='')}"
        )
    if not values.get("DATABASE_MIGRATION_URL"):
        values["DATABASE_MIGRATION_URL"] = (
            f"postgresql+psycopg://{quote(values['POSTGRES_MIGRATION_USER'], safe='')}:{quote(values['POSTGRES_MIGRATION_PASSWORD'], safe='')}"
            f"@postgres:5432/{quote(values['POSTGRES_DB'], safe='')}"
        )
    if not values.get("MONGODB_URL"):
        values["MONGODB_URL"] = (
            f"mongodb://{quote(values['MONGODB_APP_USER'], safe='')}:{quote(values['MONGODB_APP_PASSWORD'], safe='')}"
            f"@mongodb:27017/{quote(values['MONGODB_DATABASE'], safe='')}?authSource={quote(values['MONGODB_DATABASE'], safe='')}"
        )
    if not values.get("MONGODB_ADMIN_URL"):
        values["MONGODB_ADMIN_URL"] = (
            f"mongodb://{quote(values['MONGO_ROOT_USERNAME'], safe='')}:{quote(values['MONGO_ROOT_PASSWORD'], safe='')}"
            "@mongodb:27017/?authSource=admin"
        )
    if not values.get("REDIS_URL") or values["REDIS_URL"] == "redis://redis:6379/0":
        values["REDIS_URL"] = f"redis://:{quote(values['REDIS_PASSWORD'], safe='')}@redis:6379/0"
    updated = [
        f"{key}={values[key]}" if "=" in line else line
        for line in updated
        for key in [line.partition("=")[0]]
    ]
    ENV_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "up"
    if command in {"up", "migrate", "seed", "verify"}:
        ensure_environment()
    if command == "up":
        docker_command = ["docker", "compose", "up", "--build", "-d", "--wait", "--wait-timeout", "300"]
    elif command == "down":
        docker_command = ["docker", "compose", "down"]
    elif command == "stop":
        docker_command = ["docker", "compose", "stop"]
    elif command == "logs":
        docker_command = ["docker", "compose", "logs", "-f"]
    elif command == "ps":
        docker_command = ["docker", "compose", "ps"]
    elif command == "migrate":
        docker_command = [
            "docker", "compose", "run", "--rm", "--no-deps", "database-init",
            "alembic", "-c", "alembic.ini", "upgrade", "head",
        ]
    elif command == "seed":
        vehicle_count = sys.argv[2] if len(sys.argv) > 2 else "10"
        if not vehicle_count.isdecimal() or not 1 <= int(vehicle_count) <= 10_000:
            print("Seed vehicle count must be an integer from 1 to 10000")
            return 2
        docker_command = [
            "docker", "compose", "run", "--rm", "--no-deps", "api",
            "python", "-m", "fleetguard_db.seed", "--vehicles", vehicle_count,
        ]
    elif command == "verify":
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "verify.py")], cwd=ROOT, check=False).returncode
    else:
        print("Usage: python scripts/dev.py [up|down|stop|logs|ps|verify|migrate|seed [count]]")
        return 2

    return subprocess.run(docker_command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())