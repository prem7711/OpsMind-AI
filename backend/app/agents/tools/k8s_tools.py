from langchain_core.tools import StructuredTool

from app.config import settings

_MOCK_PODS = [
    {"name": "api-server-7d9f-abc12", "namespace": "default", "status": "CrashLoopBackOff", "restarts": 14},
    {"name": "worker-5b6c-def34", "namespace": "default", "status": "Running", "restarts": 0},
]
_MOCK_EVENTS = [
    {"reason": "BackOff", "message": "Back-off restarting failed container", "object": "pod/api-server-7d9f-abc12"},
    {"reason": "OOMKilled", "message": "Container api-server was OOMKilled", "object": "pod/api-server-7d9f-abc12"},
]


def _k8s_client():
    if not settings.kubeconfig_path:
        return None
    from kubernetes import client, config

    config.load_kube_config(config_file=settings.kubeconfig_path)
    return client.CoreV1Api()


def make_k8s_tools(namespace: str = "default") -> list:
    """Tools for cluster state. Use a real cluster when KUBECONFIG_PATH is set, else realistic mock fixtures."""

    def get_pod_status(pod_name: str = "") -> str:
        """Get pod status and restart counts, optionally filtered by a pod-name substring."""
        v1 = _k8s_client()
        if v1 is None:
            pods = [p for p in _MOCK_PODS if pod_name.lower() in p["name"].lower()] if pod_name else _MOCK_PODS
            return str(pods)
        pods = v1.list_namespaced_pod(namespace).items
        result = [
            {
                "name": p.metadata.name,
                "status": p.status.phase,
                "restarts": sum(cs.restart_count for cs in (p.status.container_statuses or [])),
            }
            for p in pods
            if not pod_name or pod_name.lower() in p.metadata.name.lower()
        ]
        return str(result)

    def get_deployment_status(deployment_name: str = "") -> str:
        """Get deployment replica availability, optionally filtered by a deployment-name substring."""
        v1 = _k8s_client()
        if v1 is None:
            return str({"name": deployment_name or "api-server", "desired": 3, "available": 1, "unavailable": 2})
        from kubernetes import client

        apps = client.AppsV1Api()
        deployments = apps.list_namespaced_deployment(namespace).items
        result = [
            {"name": d.metadata.name, "desired": d.spec.replicas, "available": d.status.available_replicas or 0}
            for d in deployments
            if not deployment_name or deployment_name.lower() in d.metadata.name.lower()
        ]
        return str(result)

    def get_events() -> str:
        """List recent cluster warning/error events."""
        v1 = _k8s_client()
        if v1 is None:
            return str(_MOCK_EVENTS)
        events = v1.list_namespaced_event(namespace).items
        return str([{"reason": e.reason, "message": e.message, "object": e.involved_object.name} for e in events[-50:]])

    return [
        StructuredTool.from_function(get_pod_status, name="get_pod_status", description=get_pod_status.__doc__),
        StructuredTool.from_function(
            get_deployment_status, name="get_deployment_status", description=get_deployment_status.__doc__
        ),
        StructuredTool.from_function(get_events, name="get_events", description=get_events.__doc__),
    ]
