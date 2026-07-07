"""Wires the 7 agents into the AI Flow from the TRD:
Log -> Metrics -> K8s -> Dependency -> RootCause -> Recommendation -> Postmortem.

Each node runs its ToolUsingAgent's ReAct loop (the LLM decides which tools to call), persists an
AgentResults row, and folds its structured findings into shared state for downstream agents.
"""
from datetime import datetime, timezone
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents import (
    dependency_agent,
    k8s_agent,
    log_agent,
    metrics_agent,
    postmortem_agent,
    recommendation_agent,
    root_cause_agent,
)
from app.agents.tools.registry import IncidentContext
from app.db.base import SessionLocal
from app.db.models import AgentResult, Investigation, InvestigationStatus, Postmortem, Recommendation


class IncidentState(TypedDict):
    investigation_id: int
    incident_id: int
    title: str
    description: str
    log_findings: dict
    metrics_findings: dict
    k8s_findings: dict
    dependency_findings: dict
    root_cause_findings: dict
    recommendation_findings: dict
    postmortem_findings: dict


def _ctx(state: IncidentState) -> IncidentContext:
    db = SessionLocal()
    try:
        from app.db.models import LogArtifact, MetricArtifact

        log_content = "\n".join(
            l.content for l in db.query(LogArtifact).filter_by(incident_id=state["incident_id"]).all()
        )
        metric_content = "\n".join(
            m.content for m in db.query(MetricArtifact).filter_by(incident_id=state["incident_id"]).all()
        )
    finally:
        db.close()
    return IncidentContext(incident_id=state["incident_id"], log_content=log_content, metric_content=metric_content)


def _persist_agent_result(investigation_id: int, agent_name: str, input_summary: str, result: dict) -> None:
    db = SessionLocal()
    try:
        db.add(
            AgentResult(
                investigation_id=investigation_id,
                agent_name=agent_name,
                input_summary=input_summary,
                tools_used=result["tools_used"],
                output=result["output"],
                status="completed",
            )
        )
        inv = db.get(Investigation, investigation_id)
        inv.current_agent = agent_name
        db.commit()
    finally:
        db.close()


def _log_node(state: IncidentState) -> dict:
    agent = log_agent.build(_ctx(state))
    task = f"Incident: {state['title']}\n{state['description']}\nAnalyze the uploaded logs for this incident."
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], log_agent.NAME, task, result)
    return {"log_findings": result["output"]}


def _metrics_node(state: IncidentState) -> dict:
    agent = metrics_agent.build(_ctx(state))
    task = (
        f"Incident: {state['title']}\n{state['description']}\n"
        f"Log agent findings: {state['log_findings']}\nAnalyze the uploaded metrics for this incident."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], metrics_agent.NAME, task, result)
    return {"metrics_findings": result["output"]}


def _k8s_node(state: IncidentState) -> dict:
    agent = k8s_agent.build(_ctx(state))
    task = (
        f"Incident: {state['title']}\n{state['description']}\n"
        f"Log findings: {state['log_findings']}\nMetrics findings: {state['metrics_findings']}\n"
        "Inspect the Kubernetes cluster state relevant to this incident."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], k8s_agent.NAME, task, result)
    return {"k8s_findings": result["output"]}


def _dependency_node(state: IncidentState) -> dict:
    agent = dependency_agent.build(_ctx(state))
    task = (
        f"Incident: {state['title']}\n{state['description']}\n"
        f"K8s findings: {state['k8s_findings']}\n"
        "Trace the dependency chain of the affected service(s) and check downstream health."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], dependency_agent.NAME, task, result)
    return {"dependency_findings": result["output"]}


def _root_cause_node(state: IncidentState) -> dict:
    agent = root_cause_agent.build(_ctx(state))
    task = (
        f"Incident: {state['title']}\n{state['description']}\n"
        f"Log findings: {state['log_findings']}\nMetrics findings: {state['metrics_findings']}\n"
        f"K8s findings: {state['k8s_findings']}\nDependency findings: {state['dependency_findings']}\n"
        "Determine the single most likely root cause. Re-verify with your tools if the prior "
        "findings are ambiguous or contradictory."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], root_cause_agent.NAME, task, result)
    return {"root_cause_findings": result["output"]}


def _recommendation_node(state: IncidentState) -> dict:
    agent = recommendation_agent.build(_ctx(state))
    task = (
        f"Root cause: {state['root_cause_findings']}\n"
        "Propose ranked, concrete remediation actions for this root cause."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], recommendation_agent.NAME, task, result)
    return {"recommendation_findings": result["output"]}


def _postmortem_node(state: IncidentState) -> dict:
    agent = postmortem_agent.build(_ctx(state))
    task = (
        f"Incident: {state['title']}\n{state['description']}\n"
        f"Log findings: {state['log_findings']}\nMetrics findings: {state['metrics_findings']}\n"
        f"K8s findings: {state['k8s_findings']}\nDependency findings: {state['dependency_findings']}\n"
        f"Root cause: {state['root_cause_findings']}\nRecommendations: {state['recommendation_findings']}\n"
        "Write the full postmortem."
    )
    result = agent.run(task)
    _persist_agent_result(state["investigation_id"], postmortem_agent.NAME, task, result)
    return {"postmortem_findings": result["output"]}


def build_graph():
    graph = StateGraph(IncidentState)
    graph.add_node("log_agent", _log_node)
    graph.add_node("metrics_agent", _metrics_node)
    graph.add_node("k8s_agent", _k8s_node)
    graph.add_node("dependency_agent", _dependency_node)
    graph.add_node("root_cause_agent", _root_cause_node)
    graph.add_node("recommendation_agent", _recommendation_node)
    graph.add_node("postmortem_agent", _postmortem_node)

    graph.set_entry_point("log_agent")
    graph.add_edge("log_agent", "metrics_agent")
    graph.add_edge("metrics_agent", "k8s_agent")
    graph.add_edge("k8s_agent", "dependency_agent")
    graph.add_edge("dependency_agent", "root_cause_agent")
    graph.add_edge("root_cause_agent", "recommendation_agent")
    graph.add_edge("recommendation_agent", "postmortem_agent")
    graph.add_edge("postmortem_agent", END)
    return graph.compile()


def run_investigation(investigation_id: int, incident_id: int, title: str, description: str) -> None:
    """Runs synchronously end-to-end; the caller (incident_service) invokes this via BackgroundTasks."""
    db = SessionLocal()
    try:
        inv = db.get(Investigation, investigation_id)
        inv.status = InvestigationStatus.running
        inv.started_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()

    graph = build_graph()
    initial_state: IncidentState = {
        "investigation_id": investigation_id,
        "incident_id": incident_id,
        "title": title,
        "description": description,
        "log_findings": {},
        "metrics_findings": {},
        "k8s_findings": {},
        "dependency_findings": {},
        "root_cause_findings": {},
        "recommendation_findings": {},
        "postmortem_findings": {},
    }

    db = SessionLocal()
    try:
        final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

        for rec in final_state["recommendation_findings"].get("recommendations", []):
            db.add(
                Recommendation(
                    investigation_id=investigation_id,
                    action=rec["action"],
                    category=rec.get("category", "other"),
                    rationale=rec.get("rationale", ""),
                    confidence=rec.get("confidence", 0.5),
                )
            )

        pm = final_state["postmortem_findings"]
        if pm:
            db.add(
                Postmortem(
                    investigation_id=investigation_id,
                    executive_summary=pm.get("executive_summary", ""),
                    timeline=pm.get("timeline", []),
                    root_cause=pm.get("root_cause", ""),
                    impact=pm.get("impact", ""),
                    fix_applied=pm.get("fix_applied", ""),
                    preventive_actions=pm.get("preventive_actions", []),
                    lessons_learned=pm.get("lessons_learned", []),
                )
            )

        inv = db.get(Investigation, investigation_id)
        inv.status = InvestigationStatus.completed
        inv.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        inv = db.get(Investigation, investigation_id)
        inv.status = InvestigationStatus.failed
        inv.error = str(e)
        db.commit()
        raise
    finally:
        db.close()
