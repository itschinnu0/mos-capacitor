import os
import sys
import subprocess


def main() -> None:
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--server.headless=false",
    ]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
