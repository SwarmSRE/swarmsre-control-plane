import asyncio
import json
import logging
import typing
from typing import Literal

from pydantic import BaseModel, Field

from agents.prompts.gitops_auditor_prompt import gitops_auditor_prompt
from agents.state import IncidentState
from core.llm import get_worker_llm
from core.mcp_client import mcp

logger = logging.getLogger(__name__)

class GitOpsOutput(BaseModel):
    """Structured insights extracted from Helm history and GitHub commits."""
    drift_detected: Literal["yes", "no", "unknown"] = Field(
        description="Whether a configuration drift or recent deployment was detected."
    )
    drift_details: str = Field(
        description="A summary of the configuration change (e.g., 'image tag changed from v1 to v2')."
    )
    suspect_commits: list[str] = Field(
        default_factory=list,
        description="List of commit SHAs or messages that likely caused the drift."
    )

async def gitops_auditor_node(state: IncidentState) -> dict:
    """Fetches GitOps history via MCP and analyzes it using the worker LLM asynchronously."""
    incident_id = state.get("incident_id")
    logger.info(f"Running async GitOps Auditor for incident {incident_id}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        raise ValueError(f"GitOps Auditor failed for {incident_id}: no pod name in event")

    # In a real cluster, we would parse pod labels to find the Helm release name.
    # For now, we will extract it from the pod name (assuming release-name-xxxxx).
    # We will try to fetch the deployment name to guess the release name.
    parts = pod_name.split("-")
    release_name = "-".join(parts[:-2]) if len(parts) > 2 else pod_name
    
    # 1. Fetch Helm History
    helm_history_str = await mcp.fetch_helm_history(namespace, release_name)
    
    # If helm history fails, we pass an empty string
    helm_diff = ""
    try:
        if "error" not in helm_history_str.lower() and helm_history_str.strip().startswith("["):
            history = json.loads(helm_history_str)
            if len(history) >= 2:
                # Compare the last two revisions
                latest_rev = history[-1]["revision"]
                prev_rev = history[-2]["revision"]
                latest_vals = await mcp.fetch_helm_values(namespace, release_name, latest_rev)
                prev_vals = await mcp.fetch_helm_values(namespace, release_name, prev_rev)
                helm_diff = f"Revision {prev_rev} Values:\n{prev_vals}\n\nRevision {latest_rev} Values:\n{latest_vals}"
            elif len(history) == 1:
                helm_diff = f"Initial deployment (Rev 1). No previous values. Current:\n" + await mcp.fetch_helm_values(namespace, release_name, history[0]["revision"])
    except Exception as e:
        logger.error(f"Failed to parse Helm history for {release_name}: {e}")
        raise ValueError(f"GitOps Auditor failed to fetch Helm history for {release_name}: {e}")

    # 2. Fetch GitHub Commits
    # CNCF-Grade: Read the repo URL from standard OCI annotations on the pod.
    repo = None
    try:
        status_json = await mcp.fetch_pod_status(namespace, pod_name)
        pod_data = json.loads(status_json)
        annotations = pod_data.get("metadata", {}).get("annotations", {})
        # Look for standard vcs-uri or OCI image source
        repo_url = annotations.get("org.opencontainers.image.source") or annotations.get("app.kubernetes.io/vcs-uri")
        if repo_url:
            repo = repo_url.replace("https://github.com/", "").replace(".git", "")
    except Exception as e:
        logger.error(f"Failed to read pod annotations for GitOps repo: {e}")
        raise ValueError(f"GitOps Auditor failed to read pod annotations: {e}")

    from datetime import datetime, timedelta, UTC
    since = (datetime.now(UTC) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    if repo:
        commits_str = await mcp.fetch_github_commits(repo, since)
    else:
        commits_str = "No GitHub repository configured via 'org.opencontainers.image.source' or 'app.kubernetes.io/vcs-uri' annotations. Skipping commit history."
    
    llm = get_worker_llm()
    structured_llm = llm.with_structured_output(GitOpsOutput)
    chain = gitops_auditor_prompt | structured_llm
    
    reason = event.get("reason", "Unknown")
    
    result = typing.cast(GitOpsOutput, await chain.ainvoke({
        "reason": reason,
        "helm_diff": helm_diff[:4000],  # Truncate if too long
        "commits": commits_str[:2000]
    }))
    
    logger.info(f"GitOps Auditor extracted drift_detected: {result.drift_detected}")
    
    return {
        "gitops_output": result.model_dump(),
        "messages": [f"[GitOps Auditor] Configuration drift detected: '{result.drift_detected}'. {len(result.suspect_commits)} suspect commits."]
    }
