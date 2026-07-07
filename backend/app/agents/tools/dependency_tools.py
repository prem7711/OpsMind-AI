from langchain_core.tools import StructuredTool

_MOCK_GRAPH = {
    "api-server": ["postgres", "redis", "kafka"],
    "worker": ["postgres", "kafka"],
    "postgres": [],
    "redis": [],
    "kafka": [],
}
_MOCK_HEALTH = {
    "api-server": "degraded",
    "worker": "healthy",
    "postgres": "healthy",
    "redis": "healthy",
    "kafka": "degraded",
}


def make_dependency_tools() -> list:
    """Tools for service dependency topology and health (mock service graph for this pass)."""

    def get_service_dependency_graph(service_name: str) -> str:
        """Return the direct downstream dependencies of a named service."""
        return str({service_name: _MOCK_GRAPH.get(service_name, [])})

    def check_service_health(service_name: str) -> str:
        """Return the current health status (healthy/degraded/down) of a named service."""
        return str({service_name: _MOCK_HEALTH.get(service_name, "unknown")})

    return [
        StructuredTool.from_function(
            get_service_dependency_graph,
            name="get_service_dependency_graph",
            description=get_service_dependency_graph.__doc__,
        ),
        StructuredTool.from_function(
            check_service_health, name="check_service_health", description=check_service_health.__doc__
        ),
    ]
