import os
import sys

from streamlit.web import cli as stcli


def main() -> None:
    app_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "app.py",
    )

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.address=localhost",
        "--server.headless=false",
    ]

    sys.exit(stcli.main())


if __name__ == "__main__":
    main()