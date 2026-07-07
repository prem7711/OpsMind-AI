from langchain_core.tools import StructuredTool

_MOCK_QUERY_STATS = {
    "connections": {"active": 98, "max": 100},
    "slow_queries": [
        {"query": "SELECT * FROM orders WHERE status = ?", "avg_ms": 4200, "calls": 1500},
    ],
}


def make_sql_tools() -> list:
    """Read-only SQL diagnostic tools. Non-SELECT statements are rejected outright."""

    def run_diagnostic_query(query: str) -> str:
        """Run a read-only diagnostic SQL query (e.g. against pg_stat_activity). Only SELECT is permitted."""
        if not query.strip().lower().startswith("select"):
            return "rejected: only read-only SELECT diagnostic queries are permitted"
        return str(_MOCK_QUERY_STATS)

    def explain_query(query: str) -> str:
        """Return optimization hints for a given SQL query."""
        hints = []
        if "select *" in query.lower():
            hints.append("avoid SELECT * — fetch only needed columns")
        if "where" not in query.lower():
            hints.append("missing WHERE clause — likely full table scan")
        return str({"query": query, "hints": hints or ["no obvious issues detected"]})

    return [
        StructuredTool.from_function(
            run_diagnostic_query, name="run_diagnostic_query", description=run_diagnostic_query.__doc__
        ),
        StructuredTool.from_function(explain_query, name="explain_query", description=explain_query.__doc__),
    ]
