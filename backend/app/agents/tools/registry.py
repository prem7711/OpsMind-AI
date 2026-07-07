from dataclasses import dataclass

from app.agents.tools.dependency_tools import make_dependency_tools
from app.agents.tools.doc_search_tool import make_doc_search_tool
from app.agents.tools.k8s_tools import make_k8s_tools
from app.agents.tools.log_tools import make_log_tools
from app.agents.tools.metrics_tools import make_metrics_tools
from app.agents.tools.sql_tools import make_sql_tools


@dataclass
class IncidentContext:
    incident_id: int
    log_content: str = ""
    metric_content: str = ""
    namespace: str = "default"
    primary_service: str = "api-server"


def tools_for_agent(agent_name: str, ctx: IncidentContext) -> list:
    """Declarative tool set per agent. Each agent's LLM freely decides which of its tools to call, in what
    order, and how many times — this only bounds *which domain* of tools an agent may reach for."""
    doc_tools = make_doc_search_tool()
    mapping = {
        "log_agent": make_log_tools(ctx.log_content) + doc_tools,
        "metrics_agent": make_metrics_tools(ctx.metric_content) + doc_tools,
        "k8s_agent": make_k8s_tools(ctx.namespace) + doc_tools,
        "dependency_agent": make_dependency_tools() + doc_tools,
        "root_cause_agent": (
            make_log_tools(ctx.log_content)
            + make_metrics_tools(ctx.metric_content)
            + make_k8s_tools(ctx.namespace)
            + make_dependency_tools()
            + doc_tools
        ),
        "recommendation_agent": make_sql_tools() + doc_tools,
        "postmortem_agent": doc_tools,
    }
    if agent_name not in mapping:
        raise KeyError(f"no tool set registered for agent '{agent_name}'")
    return mapping[agent_name]
