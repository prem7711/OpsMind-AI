from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "recommendation_agent"

SYSTEM_PROMPT = (
    "You are the Recommendation agent in an incident-response system. Given the confirmed root cause "
    "and contributing factors, propose concrete remediation actions (for example: increase DB pool "
    "size, restart a Kafka consumer group, optimize a slow SQL query, scale a deployment, enable a "
    "circuit breaker, roll back a deployment — or something else entirely if that fits better). You "
    "have SQL diagnostic tools and a knowledge-base search tool available to validate a recommendation "
    "before proposing it — use them when they would sharpen your answer. Rank recommendations by "
    "confidence and give a rationale for each."
)


class RecommendationItem(BaseModel):
    action: str = Field(description="A specific, actionable remediation step")
    category: str = Field(description="Short category, e.g. scale, restart, optimize_sql, circuit_breaker, rollback, config")
    rationale: str = Field(description="Why this action addresses the root cause")
    confidence: float = Field(description="Confidence this action will help, 0.0-1.0")


class RecommendationFindings(BaseModel):
    recommendations: list[RecommendationItem] = Field(default_factory=list)


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), RecommendationFindings)
