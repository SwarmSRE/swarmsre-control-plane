import json
import logging
import os
import platform
import stat
import subprocess
import tempfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

POLICY_PATH = Path(__file__).parent.parent / "policies" / "safety.rego"
OPA_VERSION = "v0.61.0"
BIN_DIR = Path(__file__).parent.parent / ".bin"
OPA_BIN = BIN_DIR / "opa"

class SafetyGate:
    def __init__(self, policy_path: str | Path = POLICY_PATH):
        self.policy_path = Path(policy_path)

    def _ensure_opa_cli(self):
        """Downloads the OPA CLI if it doesn't exist."""
        if OPA_BIN.exists():
            return
            
        system = platform.system().lower()
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            arch_str = "amd64"
        elif arch in ["arm64", "aarch64"]:
            arch_str = "arm64_static" if system == "linux" else "aarch64"
        else:
            raise RuntimeError(f"Unsupported architecture for automatic OPA download: {arch}")

        if system == "darwin":
            os_str = "darwin"
        elif system == "linux":
            os_str = "linux"
        else:
            raise RuntimeError(f"Unsupported OS for automatic OPA download: {system}")

        logger.info(f"Downloading OPA CLI {OPA_VERSION} for {os_str}/{arch_str} to {OPA_BIN}...")
        logger.warning("Skipping checksum verification for MVP")
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        
        url = f"https://openpolicyagent.org/downloads/{OPA_VERSION}/opa_{os_str}_{arch_str}"
        if system == "linux" and arch_str == "amd64":
            url = f"https://openpolicyagent.org/downloads/{OPA_VERSION}/opa_linux_amd64_static"
            
        try:
            urllib.request.urlretrieve(url, OPA_BIN)
            # Make executable
            OPA_BIN.chmod(OPA_BIN.stat().st_mode | stat.S_IEXEC)
            logger.info("OPA CLI downloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to download OPA CLI: {e}")
            raise RuntimeError(f"Could not download OPA CLI: {e}")

    def validate_patch(self, patch: dict, namespace: str = "default") -> list[str]:
        """
        Validate a Kubernetes patch using OPA Rego policies.
        Returns a list of denial messages. If empty, the patch is safe.
        """
        self._ensure_opa_cli()
        
        admission_input = {
            "request": {
                "operation": "UPDATE",
                "object": patch,
                "namespace": namespace,
            }
        }
        
        # Write input to a temporary file for the OPA CLI
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
            json.dump(admission_input, f)
            input_path = f.name
            
        try:
            cmd = [
                str(OPA_BIN),
                "eval",
                "-i", input_path,
                "-d", str(self.policy_path),
                "data.swarmsre.admission.deny",
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10.0)
            output = json.loads(result.stdout)
            
            # Extract results
            # OPA format: {"result": [{"expressions": [{"value": ["msg1", "msg2"]}]}]}
            results = output.get("result", [])
            if not results:
                return []
                
            expressions = results[0].get("expressions", [])
            if not expressions:
                return []
                
            # The value could be a list of messages
            denials = expressions[0].get("value", [])
            return denials
            
        except subprocess.CalledProcessError as e:
            logger.error(f"OPA eval failed: {e.stderr}")
            return [f"Safety policy evaluation failed: {e.stderr}"]
        except subprocess.TimeoutExpired as e:
            logger.error(f"OPA eval timed out after 10s: {e}")
            return ["Safety policy evaluation timed out after 10s."]
        except Exception as e:
            logger.error(f"Unexpected error in safety gate: {e}")
            return [f"Unexpected error in safety gate: {e}"]
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

# Global instance for easy reuse
safety_gate = SafetyGate()

def validate_kubernetes_patch(patch: dict, namespace: str = "default") -> list[str]:
    """Helper to validate using the global safety gate instance."""
    return safety_gate.validate_patch(patch, namespace)
