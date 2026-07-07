from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "postmortem_agent"

SYSTEM_PROMPT = (
    "You are the Postmortem agent in an incident-response system. Given the full investigation "
    "history (log, metrics, k8s, dependency, root-cause, and recommendation findings), write a "
    "complete postmortem. You have a knowledge-base search tool available if you want to ground any "
    "preventive action in established best practice. Be concrete and specific — avoid generic filler."
)


class PostmortemDraft(BaseModel):
    executive_summary: str = Field(description="2-4 sentence summary for stakeholders")
    timeline: list[str] = Field(default_factory=list, description="Ordered timeline entries reconstructed from the investigation")
    root_cause: str = Field(description="The confirmed root cause")
    impact: str = Field(description="Who/what was affected and how badly")
    fix_applied: str = Field(description="The fix that was applied or recommended")
    preventive_actions: list[str] = Field(default_factory=list, description="Concrete steps to prevent recurrence")
    lessons_learned: list[str] = Field(default_factory=list)


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), PostmortemDraft)
