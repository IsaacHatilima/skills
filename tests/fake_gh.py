#!/usr/bin/env python3
"""A stand-in for the `gh` CLI, backed by a JSON file named by FAKE_GH_STATE.

It implements only the calls the factory's scripts and the tests make, records
every call under "calls", and exits 1 on anything else.
"""

import json
import os
import sys

STATE = os.environ["FAKE_GH_STATE"]
OPERATOR = "operator"


def load():
    with open(STATE) as f:
        return json.load(f)


def save(state):
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)


def opts(args):
    """--flag value pairs (and bare --flags) after the positional arguments."""
    out, i = {}, 0
    while i < len(args):
        if args[i].startswith("--"):
            has_value = i + 1 < len(args) and not args[i + 1].startswith("--")
            out[args[i][2:]] = args[i + 1] if has_value else True
            i += 2 if has_value else 1
        else:
            i += 1
    return out


def pick(obj, fields):
    return {k: obj[k] for k in fields.split(",")}


def issue_view(state, number, o):
    issue = state["issues"][number]
    view = {**issue, "labels": [{"name": n} for n in issue["labels"]],
            "author": {"login": issue["author"]}, "number": int(number)}
    return pick(view, o["json"])


def issue_edit(state, number, o):
    labels = state["issues"][number]["labels"]
    if "add-label" in o:
        labels.append(o["add-label"])
    if "remove-label" in o:
        gone = set(o["remove-label"].split(","))
        state["issues"][number]["labels"] = [n for n in labels if n not in gone]


def add_comment(target, body):
    target.setdefault("comments", []).append(
        {"author": {"login": OPERATOR}, "body": body, "createdAt": f"2026-11-12T00:00:{len(target['comments']):02d}Z"})


def issue(state, args):
    action, rest = args[0], args[1:]
    o = opts(rest)
    if action == "view":
        return issue_view(state, rest[0], o)
    if action == "list":
        found = [{"number": int(n), "title": i["title"]} for n, i in state["issues"].items()
                 if i["state"] == "OPEN" and o["label"] in i["labels"]]
        return found
    if action == "comment":
        add_comment(state["issues"][rest[0]], o["body"])
    elif action == "edit":
        issue_edit(state, rest[0], o)
    else:
        raise KeyError(action)
    return None


def pr_view(state, ref, o):
    pr = state["prs"].get(ref) or next((p for p in state["prs"].values() if p["head"] == ref), None)
    if pr is None:
        sys.exit(1)
    return pick(pr, o["json"]) if "json" in o else pr["url"]


def pr(state, args):
    action, rest = args[0], args[1:]
    o = opts(rest)
    if action == "create":
        n = str(100 + len(state["prs"]))
        state["prs"][n] = {"number": int(n), "url": f"https://example.test/pull/{n}", "head": o["head"],
                           "base": o["base"], "title": o["title"], "body": o["body"],
                           "state": "OPEN", "isDraft": "draft" in o, "comments": []}
        return state["prs"][n]["url"]
    if action == "list":
        return [{"number": p["number"], "url": p["url"]} for p in state["prs"].values()
                if p["head"] == o["head"] and p["state"] == o["state"].upper()]
    if action == "view":
        return pr_view(state, rest[0], o)
    p = state["prs"][rest[0]]
    if action == "ready":
        p["isDraft"] = False
    elif action == "merge":
        p["state"] = "MERGED"
    elif action == "close":
        p["state"] = "CLOSED"
    elif action == "comment":
        add_comment(p, o["body"])
    else:
        raise KeyError(action)
    return None


def main(args):
    fail = os.environ.get("FAKE_GH_FAIL")
    if fail and " ".join(args).startswith(fail):
        print(f"fake gh: failing `{fail}` on purpose", file=sys.stderr)
        sys.exit(1)
    state = load()
    state["calls"].append(args)
    if args[:2] == ["api", "user"]:
        out = OPERATOR
    elif args[0] == "issue":
        out = issue(state, args[1:])
    elif args[0] == "pr":
        out = pr(state, args[1:])
    elif args[:2] == ["label", "create"]:
        state["labels"][args[2]] = opts(args[3:])
        out = None
    else:
        save(state)
        print(f"fake gh: unsupported {args}", file=sys.stderr)
        sys.exit(1)
    save(state)
    if out is not None:
        print(out if isinstance(out, str) else json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1:])
