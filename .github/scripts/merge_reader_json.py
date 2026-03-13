"""
Resolve rebase conflicts in reader_entries.json and reader_progress.json.

During a 'git pull --rebase', when two concurrent runs both append to these
JSON files, git cannot auto-merge them. This script resolves the conflict by:
  - reader_entries.json: taking the remote (HEAD) as the base and re-appending
    any entries from our rebased commit (REBASE_HEAD) that are not yet present.
  - reader_progress.json: keeping the maximum offset from either side.

Exit codes: 0 = success, 1 = failure (caller should abort the rebase).
"""

import json
import subprocess
import sys


def git_show(ref, path):
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def merge_entries():
    remote = git_show("HEAD", "book/reader_entries.json")
    ours = git_show("REBASE_HEAD", "book/reader_entries.json")
    if remote is None or ours is None:
        print("ERROR: could not load reader_entries.json from git", flush=True)
        return False

    remote_ids = {e["id"] for e in remote["entries"]}
    added = 0
    for entry in ours["entries"]:
        if entry["id"] not in remote_ids:
            remote["entries"].append(entry)
            print(f"Re-applied entry: {entry['id']}", flush=True)
            added += 1

    if added == 0:
        print("No new entries to re-apply in reader_entries.json", flush=True)

    with open("book/reader_entries.json", "w", encoding="utf-8") as f:
        json.dump(remote, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


def merge_progress():
    remote = git_show("HEAD", "book/reader_progress.json")
    ours = git_show("REBASE_HEAD", "book/reader_progress.json")
    if remote is None or ours is None:
        print("ERROR: could not load reader_progress.json from git", flush=True)
        return False

    merged = {
        "offset": max(remote["offset"], ours["offset"]),
        "completed": remote.get("completed", False) or ours.get("completed", False),
    }
    with open("book/reader_progress.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Merged reader_progress.json: offset={merged['offset']}", flush=True)
    return True


if __name__ == "__main__":
    ok_entries = merge_entries()
    ok_progress = merge_progress()
    sys.exit(0 if (ok_entries and ok_progress) else 1)
