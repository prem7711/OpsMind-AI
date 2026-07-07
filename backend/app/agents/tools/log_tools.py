import re

from langchain_core.tools import StructuredTool


def make_log_tools(log_content: str) -> list:
    """Tools bound to one incident's uploaded log content. The agent decides which to call and with what args."""

    def grep_pattern(pattern: str) -> str:
        """Search log lines by regex pattern. Use for structured matches like error codes or stack frames."""
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return f"invalid regex: {e}"
        matches = [line for line in log_content.splitlines() if rx.search(line)]
        return "\n".join(matches[:200]) or "no matches"

    def search_logs(keyword: str) -> str:
        """Case-insensitive substring search over log lines. Use for free-text terms like a service or exception name."""
        kw = keyword.lower()
        matches = [line for line in log_content.splitlines() if kw in line.lower()]
        return "\n".join(matches[:200]) or "no matches"

    def summarize_log_levels() -> str:
        """Count log lines per severity level (FATAL/ERROR/WARN/INFO/DEBUG). Use to gauge overall severity."""
        levels = ["FATAL", "ERROR", "WARN", "INFO", "DEBUG"]
        counts = {lvl: sum(1 for line in log_content.splitlines() if lvl in line) for lvl in levels}
        return str(counts)

    return [
        StructuredTool.from_function(grep_pattern, name="grep_pattern", description=grep_pattern.__doc__),
        StructuredTool.from_function(search_logs, name="search_logs", description=search_logs.__doc__),
        StructuredTool.from_function(
            summarize_log_levels, name="summarize_log_levels", description=summarize_log_levels.__doc__
        ),
    ]
