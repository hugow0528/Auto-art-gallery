"""
Resolve rebase conflicts in gallery.json.

During a 'git pull --rebase', when two concurrent runs both append to this
JSON file, git cannot auto-merge it. This script resolves the conflict by
taking the remote (HEAD) as the base and re-appending any artworks from our
rebased commit (REBASE_HEAD) that are not yet present.

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


def merge_artworks():
    remote = git_show("HEAD", "gallery.json")
    ours = git_show("REBASE_HEAD", "gallery.json")
    if remote is None or ours is None:
        print("ERROR: could not load gallery.json from git", flush=True)
        return False

    remote_ids = {a["id"] for a in remote["artworks"]}
    added = 0
    for artwork in ours["artworks"]:
        if artwork["id"] not in remote_ids:
            remote["artworks"].append(artwork)
            print(f"Re-applied artwork: {artwork['id']}", flush=True)
            added += 1

    if added == 0:
        print("No new artworks to re-apply in gallery.json", flush=True)

    with open("gallery.json", "w", encoding="utf-8") as f:
        json.dump(remote, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


if __name__ == "__main__":
    sys.exit(0 if merge_artworks() else 1)
