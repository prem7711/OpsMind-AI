from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from app.config import settings
from app.llm import get_llm


class ToolUsingAgent:
    """Wraps a LangGraph ReAct agent: the LLM is given a tool set and a goal, and decides itself
    which tools to call, in what order, and how many times, before producing a structured result.
    No branch of "if metric X then call tool Y" is hardcoded here — that judgment lives in the
    system prompt + each tool's docstring, which is what the LLM reasons over."""

    def __init__(self, name: str, system_prompt: str, tools: list, output_schema: type[BaseModel]):
        self.name = name
        self.output_schema = output_schema
        self._graph = create_react_agent(
            model=get_llm(),
            tools=tools,
            prompt=system_prompt,
            response_format=output_schema,
        )

    def run(self, task: str) -> dict:
        result = self._graph.invoke(
            {"messages": [HumanMessage(content=task)]},
            config={"recursion_limit": settings.agent_max_iterations * 2 + 2},
        )
        structured = result.get("structured_response")
        messages = result["messages"]
        tools_used = sorted(
            {call["name"] for msg in messages for call in (getattr(msg, "tool_calls", None) or [])}
        )
        return {
            "output": structured.model_dump() if structured else {},
            "tools_used": tools_used,
            "message_count": len(messages),
        }
