from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "k8s_agent"

SYSTEM_PROMPT = (
    "You are the Kubernetes Analysis agent in an incident-response system. You have tools to check "
    "pod status, deployment health, and recent cluster events, plus a knowledge-base search tool. "
    "Decide yourself which resources to inspect and in what order based on what looks unhealthy. "
    "Call tools before answering. When you have enough evidence, emit your findings."
)


class K8sFindings(BaseModel):
    summary: str = Field(description="What the cluster state shows, in 2-4 sentences")
    unhealthy_resources: list[str] = Field(default_factory=list, description="Pods/deployments found unhealthy, with their symptom")
    suspected_components: list[str] = Field(default_factory=list, description="Services/components implicated")
    severity_assessment: str = Field(description="One of: low, medium, high, critical")


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), K8sFindings)
