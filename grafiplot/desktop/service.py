"""JSON Lines stdin/stdout protocol; one request and one response per line."""

import json
import sys
import traceback

from grafiplot.desktop.engine import Engine


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Keep the wire channel clean even if a PDF library prints a diagnostic.
    wire = sys.stdout
    sys.stdout = sys.stderr
    engine = Engine()
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                if request.get("method") == "shutdown":
                    break
                result = {
                    "result": engine.call(request["method"], request.get("params"))
                }
            except Exception as error:
                traceback.print_exc(file=sys.stderr)
                result = {"error": str(error)}
            wire.write(json.dumps(result, ensure_ascii=True) + "\n")
            wire.flush()
    finally:
        engine.close()


if __name__ == "__main__":
    main()
