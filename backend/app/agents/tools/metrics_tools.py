import json

import httpx
from langchain_core.tools import StructuredTool

from app.config import settings


def make_metrics_tools(metric_content: str) -> list:
    """Tools bound to one incident's uploaded metric content (and live Prometheus if configured)."""

    def query_metrics(metric_name: str) -> str:
        """Query a metric's recent values by name. Hits Prometheus if PROMETHEUS_URL is configured, else the uploaded metric snapshot."""
        if settings.prometheus_url:
            try:
                resp = httpx.get(
                    f"{settings.prometheus_url}/api/v1/query", params={"query": metric_name}, timeout=5
                )
                resp.raise_for_status()
                return json.dumps(resp.json())
            except Exception as e:
                return f"prometheus query failed: {e}"
        lines = [l for l in metric_content.splitlines() if metric_name.lower() in l.lower()]
        return "\n".join(lines[:100]) or f"no data for metric '{metric_name}' in uploaded content"

    def detect_anomaly(metric_name: str, threshold: float) -> str:
        """Find lines mentioning a metric whose numeric value exceeds the given threshold."""
        hits = []
        for line in metric_content.splitlines():
            if metric_name.lower() not in line.lower():
                continue
            for tok in line.replace(",", " ").split():
                try:
                    if float(tok) > threshold:
                        hits.append(line)
                        break
                except ValueError:
                    continue
        return "\n".join(hits[:50]) or "no anomalies above threshold"

    return [
        StructuredTool.from_function(query_metrics, name="query_metrics", description=query_metrics.__doc__),
        StructuredTool.from_function(detect_anomaly, name="detect_anomaly", description=detect_anomaly.__doc__),
    ]
