"""Secret-free exact source revision readback for the live Worker runtime."""

from __future__ import annotations

import argparse
import json

from topicpilot_api.release_provenance import runtime_git_sha


def main(argv: list[str] | None = None) -> int:
    """Emit the Worker runtime revision and fail closed when it is unknown."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the JSON readback")
    parser.parse_args(argv)

    revision = runtime_git_sha()
    payload = {
        "runtimeGitSha": revision,
        "readbackStatus": "READY" if revision != "UNKNOWN" else "UNVERIFIED",
        "source": "RENDER_GIT_COMMIT_OR_GIT_SHA",
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if revision != "UNKNOWN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
