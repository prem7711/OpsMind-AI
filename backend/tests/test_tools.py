from app.agents.tools.dependency_tools import make_dependency_tools
from app.agents.tools.k8s_tools import make_k8s_tools
from app.agents.tools.log_tools import make_log_tools
from app.agents.tools.metrics_tools import make_metrics_tools
from app.agents.tools.sql_tools import make_sql_tools


def _by_name(tools):
    return {t.name: t for t in tools}


def test_log_tools_search_and_grep():
    log = "2026-07-06 ERROR db timeout\n2026-07-06 INFO ok\n2026-07-06 ERROR db timeout again"
    tools = _by_name(make_log_tools(log))
    assert "db timeout" in tools["search_logs"].invoke({"keyword": "timeout"})
    assert tools["search_logs"].invoke({"keyword": "nope"}) == "no matches"
    assert len(tools["grep_pattern"].invoke({"pattern": r"ERROR.*timeout"}).splitlines()) == 2
    counts = tools["summarize_log_levels"].invoke({})
    assert "'ERROR': 2" in counts and "'INFO': 1" in counts


def test_log_tools_invalid_regex():
    tools = _by_name(make_log_tools("some log"))
    assert "invalid regex" in tools["grep_pattern"].invoke({"pattern": "("})


def test_metrics_tools_anomaly_detection():
    metrics = "cpu_usage 45\ncpu_usage 97\nmem_usage 30"
    tools = _by_name(make_metrics_tools(metrics))
    result = tools["detect_anomaly"].invoke({"metric_name": "cpu_usage", "threshold": 90})
    assert "97" in result
    assert "45" not in result


def test_metrics_tools_query_no_prometheus_configured():
    tools = _by_name(make_metrics_tools("db_connections 98"))
    assert "98" in tools["query_metrics"].invoke({"metric_name": "db_connections"})


def test_k8s_tools_mock_mode():
    tools = _by_name(make_k8s_tools())
    result = tools["get_pod_status"].invoke({"pod_name": "api-server"})
    assert "CrashLoopBackOff" in result
    assert "get_events" in tools and "OOMKilled" in tools["get_events"].invoke({})


def test_dependency_tools():
    tools = _by_name(make_dependency_tools())
    assert "postgres" in tools["get_service_dependency_graph"].invoke({"service_name": "api-server"})
    assert "degraded" in tools["check_service_health"].invoke({"service_name": "api-server"})


def test_sql_tools_rejects_non_select():
    tools = _by_name(make_sql_tools())
    assert "rejected" in tools["run_diagnostic_query"].invoke({"query": "DROP TABLE orders"})
    assert "connections" in tools["run_diagnostic_query"].invoke({"query": "SELECT * FROM pg_stat_activity"})


def test_sql_tools_explain_hints():
    tools = _by_name(make_sql_tools())
    hints = tools["explain_query"].invoke({"query": "SELECT * FROM orders"})
    assert "SELECT *" in hints
