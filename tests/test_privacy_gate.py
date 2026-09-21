"""tools/privacy_gate.sh must fail CLOSED whenever it cannot really judge.

Each test seeds one way the gate used to report "clean" while checking nothing.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "privacy_gate.sh"
pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or os.name == "nt",
    reason="the gate is a bash script run on POSIX",
)


def git(repo, *args):
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
    )


@pytest.fixture()
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "tools" / "privacy_gate.sh")
    (root / "notes.txt").write_text("the server is called forbiddenhost here\n")
    git(root, "init", "-q")
    git(root, "add", ".")
    git(root, "commit", "-q", "--no-verify", "-m", "first")
    (root / "more.txt").write_text("nothing special\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "--no-verify", "-m", "second mentions forbiddenhost")
    return root


def run(repo, tmp_path, patterns, **env):
    deny = tmp_path / "deny.txt"
    deny.write_bytes(patterns)
    full = dict(
        os.environ,
        DENYLIST_FILE=str(deny),
        BASELINE_FILE=str(tmp_path / "no-baseline"),
        **env,
    )
    done = subprocess.run(
        ["bash", str(repo / "tools" / "privacy_gate.sh")],
        env=full,
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode, done.stdout + done.stderr


def test_control_a_hit_is_red_and_the_match_is_never_printed(repo, tmp_path):
    rc, out = run(repo, tmp_path, b"forbiddenhost\n")
    assert rc == 1 and "notes.txt:1" in out and "forbiddenhost" not in out


def test_control_a_clean_tree_is_green(repo, tmp_path):
    rc, _ = run(repo, tmp_path, b"not-present-anywhere\n")
    assert rc == 0


def test_an_invalid_regex_does_not_switch_the_scan_off(repo, tmp_path):
    rc, out = run(repo, tmp_path, b"forbiddenhost\n(unclosed\n")
    assert rc == 2 and "valid extended regex" in out


def test_a_crlf_list_fails_closed(repo, tmp_path):
    rc, out = run(repo, tmp_path, b"forbiddenhost\r\n")
    assert rc == 2 and "CRLF" in out


def test_a_missing_pr_text_file_fails_closed(repo, tmp_path):
    rc, out = run(
        repo,
        tmp_path,
        b"not-present-anywhere\n",
        PR_TEXT_FILE=str(tmp_path / "absent.txt"),
    )
    assert rc == 2 and "PR_TEXT_FILE" in out


def test_a_hit_in_the_pr_text_is_red(repo, tmp_path):
    text = tmp_path / "pr.txt"
    text.write_text("title\n\nbody with ForbiddenHost\n")
    rc, _ = run(repo, tmp_path, b"forbiddenhost\n", PR_TEXT_FILE=str(text))
    assert rc == 1


@pytest.mark.parametrize("base", ["0" * 40, "no-such-ref"])
def test_a_base_that_does_not_resolve_fails_closed(repo, tmp_path, base):
    rc, out = run(repo, tmp_path, b"not-present-anywhere\n", BASE_SHA=base)
    assert rc == 2 and "BASE_SHA" in out


def test_a_hit_in_a_commit_message_is_red(repo, tmp_path):
    rc, out = run(repo, tmp_path, b"second mentions\n", BASE_SHA="HEAD~1")
    assert rc == 1 and "commit message" in out
