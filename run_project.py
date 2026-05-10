import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="启动多网络结构舆论传播仿真系统")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--migrate", action="store_true", help="启动前执行 Django 数据库迁移")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    frontend_dir = root / "environment" / "frontend_server"
    manage_py = frontend_dir / "manage.py"
    if not manage_py.exists():
        print(f"未找到 Django 入口: {manage_py}")
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("DJANGO_SETTINGS_MODULE", "frontend_server.settings")

    if args.migrate:
        rc = subprocess.call([sys.executable, "manage.py", "migrate"], cwd=str(frontend_dir), env=env)
        if rc != 0:
            sys.exit(rc)

    address = f"{args.host}:{args.port}"
    print(f"多网络结构舆论传播仿真系统已启动: http://{address}/")
    subprocess.call([sys.executable, "manage.py", "runserver", address], cwd=str(frontend_dir), env=env)


if __name__ == "__main__":
    main()
