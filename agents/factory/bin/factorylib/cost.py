"""API-equivalent cost of a job's agents, read from Claude Code's transcripts.

Claude Code writes each subagent's messages, with model and token usage, to
<config>/projects/<project>/<session>/subagents/agent-<id>.jsonl. Every factory
prompt starts with `Job folder: <path>/`, which ties a transcript to its job
across sessions. The transcript format isn't a documented interface, so a
Claude Code update can break this. Codex sessions aren't counted.
"""

import json
import os
import re
from pathlib import Path

from .jobfiles import job_dir
from .project import config, repo


def transcripts_dir():
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    return home / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo()))


def prompt_text(line):
    content = json.loads(line)["message"]["content"]
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content if isinstance(b, dict))


def _usage_by_message(path, needle):
    usage = {}
    with path.open() as f:
        first = f.readline()
        try:
            if not first or needle not in prompt_text(first):
                return usage
        except (ValueError, KeyError, TypeError):
            return usage
        for line in f:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            msg = entry.get("message")
            if entry.get("type") == "assistant" and isinstance(msg, dict) and msg.get("usage"):
                usage[msg.get("id")] = (msg.get("model"), msg["usage"])
    return usage


def _price(usage, p):
    write_1h = (usage.get("cache_creation") or {}).get("ephemeral_1h_input_tokens", 0)
    write_5m = usage.get("cache_creation_input_tokens", 0) - write_1h
    return (usage.get("input_tokens", 0) * p["input"]
            + usage.get("output_tokens", 0) * p["output"]
            + write_5m * p["cache_write_5m"]
            + write_1h * p["cache_write_1h"]
            + usage.get("cache_read_input_tokens", 0) * p["cache_read"]) / 1e6


def cost_usd(job):
    """Sum every subagent whose prompt names this job's folder.

    Unpriced models count as 0, and a transcript that can't be read is skipped:
    cost is for display and must never block a stage change.
    """
    needle = f"Job folder: {job_dir(job['id'])}/"
    prices = config().get("prices_usd_per_mtok", {})
    total = 0.0
    for path in transcripts_dir().glob("*/subagents/agent-*.jsonl"):
        try:
            usages = _usage_by_message(path, needle).values()
            total += sum(_price(u, prices[m]) for m, u in usages if m in prices and isinstance(u, dict))
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue
    return round(total, 2)
