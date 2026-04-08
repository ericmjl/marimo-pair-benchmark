#!/usr/bin/env python3
"""Convert opencode JSON session export to a markdown transcript."""

import json
import sys
from datetime import datetime, timezone


def format_ts(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def fmt_cost(cost):
    if cost is None:
        return "$0.000000"
    return f"${float(cost):.6f}"


def main():
    data = json.load(sys.stdin)
    info = data.get("info", {})
    messages = data.get("messages", [])

    title = info.get("title", "Untitled")
    session_id = info.get("id", "unknown")
    created = info.get("time", {}).get("created")

    total_cost = 0.0
    total_input = 0
    total_output = 0
    total_reasoning = 0

    for msg in messages:
        for part in msg.get("parts", []):
            if part.get("type") == "step-finish":
                c = part.get("cost")
                if c is not None:
                    total_cost += float(c)
                t = part.get("tokens", {})
                if t:
                    total_input += t.get("input", 0)
                    total_output += t.get("output", 0)
                    total_reasoning += t.get("reasoning", 0)

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- **Session**: `{session_id}`")
    if created:
        lines.append(f"- **Created**: {format_ts(created)}")
    lines.append(f"- **Total Cost**: {fmt_cost(total_cost)}")
    lines.append(
        f"- **Total Tokens**: input={total_input}, output={total_output}, reasoning={total_reasoning}"
    )
    lines.append("")

    for msg in messages:
        msg_info = msg.get("info", {})
        role = msg_info.get("role", "unknown")
        model = msg_info.get("model", {})
        model_str = (
            f"{model.get('providerID', '')}/{model.get('modelID', '')}" if model else ""
        )
        parts = msg.get("parts", [])

        msg_cost = 0.0
        msg_tokens = {}
        msg_text_parts = []
        msg_tool_parts = []
        msg_reasoning_parts = []

        for part in parts:
            ptype = part.get("type", "")
            if ptype == "step-finish":
                c = part.get("cost")
                if c is not None:
                    msg_cost += float(c)
                t = part.get("tokens", {})
                if t:
                    msg_tokens = t
            elif ptype == "text":
                msg_text_parts.append(part.get("text", ""))
            elif ptype == "tool":
                msg_tool_parts.append(part)
            elif ptype == "reasoning":
                msg_reasoning_parts.append(part.get("text", ""))

        if role == "user":
            lines.append("---")
            lines.append("")
            lines.append("## User")
            lines.append("")
        elif role == "assistant":
            label = f"## Assistant ({model_str})" if model_str else "## Assistant"
            lines.append("")
            lines.append(label)
            lines.append("")

        if msg_cost > 0 or msg_tokens:
            tok_str = (
                f"in={msg_tokens.get('input', 0)} out={msg_tokens.get('output', 0)} reason={msg_tokens.get('reasoning', 0)}"
                if msg_tokens
                else "N/A"
            )
            lines.append(f"> Cost: {fmt_cost(msg_cost)} | Tokens: {tok_str}")
            lines.append("")

        if msg_reasoning_parts:
            lines.append("<details><summary>Reasoning</summary>")
            lines.append("")
            for rt in msg_reasoning_parts:
                lines.append(rt)
                lines.append("")
            lines.append("</details>")
            lines.append("")

        for text in msg_text_parts:
            lines.append(text)
            lines.append("")

        for tp in msg_tool_parts:
            tname = tp.get("tool", "unknown")
            state_obj = tp.get("state", {})
            status = (
                state_obj.get("status", "")
                if isinstance(state_obj, dict)
                else str(state_obj)
            )
            inp = state_obj.get("input") if isinstance(state_obj, dict) else None
            output = state_obj.get("output") if isinstance(state_obj, dict) else None

            lines.append(f"**Tool: `{tname}`** ({status})")
            if inp:
                args_str = json.dumps(inp, indent=2, default=str)
                if len(args_str) > 2000:
                    args_str = args_str[:2000] + "\n... (truncated)"
                lines.append(f"```json\n{args_str}\n```")
            if output:
                result_str = str(output)
                if len(result_str) > 2000:
                    result_str = result_str[:2000] + "\n... (truncated)"
                lines.append(f"```\n{result_str}\n```")
            lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
