from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "root_cause_agent"

SYSTEM_PROMPT = (
    "You are the Root Cause Analysis agent in an incident-response system. You are given the prior "
    "findings from the Log, Metrics, Kubernetes, and Dependency agents. You have access to all of "
    "their underlying tools plus a knowledge-base search tool, so you can re-verify or dig deeper "
    "into any of their claims yourself rather than taking them at face value. Decide yourself which "
    "tools, if any, to call to confirm the most likely root cause. When you have enough evidence, "
    "emit a single root cause with supporting rationale."
)


class RootCauseFindings(BaseModel):
    root_cause: str = Field(description="The single most likely root cause, stated precisely")
    contributing_factors: list[str] = Field(default_factory=list, description="Secondary factors that contributed")
    affected_components: list[str] = Field(default_factory=list, description="All components implicated")
    confidence: float = Field(description="Confidence in this root cause, 0.0-1.0")


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), RootCauseFindings)
