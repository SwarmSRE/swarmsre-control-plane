import asyncio
import logging
import os

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

TARGET_EVENT_REASONS = frozenset({
    "CrashLoopBackOff",
    "OOMKilled",
    "FailedCreate",
    "FailedMount",
    "FailedScheduling",
    "BackOff",
    "Unhealthy",
    "ImagePullBackOff",
    "ErrImagePull",
    "Failed",
})

def get_k8s_client() -> client.CoreV1Api:
    """Initialize Kubernetes client with automatic config detection."""
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config")
    except config.ConfigException:
        config.load_kube_config()
        logger.info("Loaded local kubeconfig")
    return client.CoreV1Api()

async def watch_events(
    callback,
    namespace: str = "",
    timeout_seconds: int = 300,
):
    """Watch Kubernetes events and invoke callback on target event reasons."""
    if os.environ.get("SWARMSRE_WATCHER_ENABLED", "false").lower() != "true":
        logger.info("Kubernetes watcher is disabled via SWARMSRE_WATCHER_ENABLED")
        return

    try:
        v1 = get_k8s_client()
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        return

    w = watch.Watch()
    resource_version = ""
    loop = asyncio.get_running_loop()

    def run_watch():
        nonlocal resource_version
        while True:
            try:
                logger.info(f"Starting event watch (resource_version={resource_version or 'latest'})")
                
                from typing import Any
                kwargs: dict[str, Any] = {
                    "timeout_seconds": timeout_seconds,
                    "watch": True,
                }
                if resource_version:
                    kwargs["resource_version"] = resource_version

                if namespace:
                    stream = w.stream(v1.list_namespaced_event, namespace, **kwargs)
                else:
                    stream = w.stream(v1.list_event_for_all_namespaces, **kwargs)

                for raw_event in stream:
                    event_type = raw_event["type"]  # ADDED, MODIFIED, DELETED
                    event_obj = raw_event["object"]
                    
                    # Update resource_version for reconnection
                    resource_version = event_obj.metadata.resource_version
                    
                    reason = event_obj.reason or ""
                    if reason in TARGET_EVENT_REASONS:
                        incident_data = {
                            "reason": reason,
                            "message": event_obj.message or "",
                            "namespace": event_obj.metadata.namespace,
                            "involved_object": {
                                "kind": event_obj.involved_object.kind,
                                "name": event_obj.involved_object.name,
                                "namespace": event_obj.involved_object.namespace,
                            },
                            "first_timestamp": str(event_obj.first_timestamp),
                            "last_timestamp": str(event_obj.last_timestamp),
                            "count": event_obj.count or 1,
                            "event_type": event_type,
                        }
                        # Call async callback safely from thread
                        asyncio.run_coroutine_threadsafe(callback(incident_data), loop)

            except ApiException as e:
                if e.status == 410:
                    logger.warning("Watch resource version expired (410 Gone), resetting")
                    resource_version = ""
                else:
                    logger.error(f"Kubernetes API error: {e}")
                    import time
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Watch loop error: {e}")
                import time
                time.sleep(5)

    await asyncio.to_thread(run_watch)
