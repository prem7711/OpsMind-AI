from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "dependency_agent"

SYSTEM_PROMPT = (
    "You are the Dependency Analysis agent in an incident-response system. You have tools to fetch a "
    "service's downstream dependency graph and check any service's health, plus a knowledge-base "
    "search tool. Starting from the primary service under investigation, decide yourself which "
    "downstream services to check and how deep to traverse. Call tools before answering. When you "
    "have enough evidence, emit your findings."
)


class DependencyFindings(BaseModel):
    summary: str = Field(description="What the dependency chain shows, in 2-4 sentences")
    unhealthy_services: list[str] = Field(default_factory=list, description="Downstream services found degraded/down")
    dependency_chain: list[str] = Field(default_factory=list, description="Services traversed, in order")
    severity_assessment: str = Field(description="One of: low, medium, high, critical")


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), DependencyFindings)
