from pydantic import BaseModel, Field

from app.agents.base import ToolUsingAgent
from app.agents.tools.registry import IncidentContext, tools_for_agent

NAME = "log_agent"

SYSTEM_PROMPT = (
    "You are the Log Analysis agent in an incident-response system. You have tools to search and "
    "summarize the uploaded log content, plus a knowledge-base search tool. Decide yourself which "
    "tools to call, in what order, and how many times, to find recurring error patterns and the "
    "components they implicate. Call tools before answering — never guess at log content you have "
    "not retrieved. When you have enough evidence, emit your findings."
)


class LogFindings(BaseModel):
    summary: str = Field(description="What the logs show, in 2-4 sentences")
    error_patterns: list[str] = Field(default_factory=list, description="Distinct recurring error/exception patterns found")
    suspected_components: list[str] = Field(default_factory=list, description="Services/components implicated by the logs")
    severity_assessment: str = Field(description="One of: low, medium, high, critical")


def build(ctx: IncidentContext) -> ToolUsingAgent:
    return ToolUsingAgent(NAME, SYSTEM_PROMPT, tools_for_agent(NAME, ctx), LogFindings)
