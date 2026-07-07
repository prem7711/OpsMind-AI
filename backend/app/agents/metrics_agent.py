from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "metrics_agent"

SYSTEM_PROMPT = (
    "You are the Metrics Analysis agent in an incident-response system. You have tools to query "
    "metrics and detect anomalies against thresholds you choose, plus a knowledge-base search tool. "
    "Decide yourself which metrics to inspect and which thresholds are meaningful given the incident "
    "context — do not assume a fixed metric name or threshold. Call tools before answering. When you "
    "have enough evidence, emit your findings."
)


class MetricsFindings(BaseModel):
    summary: str = Field(description="What the metrics show, in 2-4 sentences")
    anomalies: list[str] = Field(default_factory=list, description="Specific anomalous metric readings found")
    suspected_components: list[str] = Field(default_factory=list, description="Services/components implicated by metrics")
    severity_assessment: str = Field(description="One of: low, medium, high, critical")


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), MetricsFindings)
