#!/usr/bin/env python3
"""Write the title and description of the pull request being built to $PR_TEXT_FILE.

Jenkins does not expose the PR description as a variable, so it is read from the forge API. The
server is derived from CHANGE_URL (set by the multibranch job), never written down here: this file
is public. Reads CHANGE_URL, API_TOKEN and PR_TEXT_FILE from the environment. Fails (rc != 0) if the
text cannot be read, so a broken lookup can never look like an empty, clean description.
"""
import json
import os
import sys
import urllib.request
from urllib.parse import urlsplit


def main() -> int:
    url = os.environ.get("CHANGE_URL", "")
    token = os.environ.get("API_TOKEN", "")
    out = os.environ.get("PR_TEXT_FILE", "")
    parts = urlsplit(url)
    segs = [s for s in parts.path.split("/") if s]  # <owner>/<repo>/pulls/<n>
    if not (parts.scheme and parts.netloc and len(segs) >= 4 and segs[-2] == "pulls" and token and out):
        print("pr_text: need CHANGE_URL (<server>/<owner>/<repo>/pulls/<n>), API_TOKEN and PR_TEXT_FILE",
              file=sys.stderr)
        return 2
    api = f"{parts.scheme}://{parts.netloc}/api/v1/repos/{segs[-4]}/{segs[-3]}/pulls/{segs[-1]}"
    req = urllib.request.Request(api, headers={"Authorization": f"token {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        pr = json.load(resp)
    if pr.get("title") is None or pr.get("body") is None:
        print("pr_text: the API answer has no 'title' or 'body' field", file=sys.stderr)
        return 3
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"{pr['title']}\n\n{pr['body']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
