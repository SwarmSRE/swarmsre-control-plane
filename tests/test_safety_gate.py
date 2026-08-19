import pytest
from core.safety_gate import SafetyGate

@pytest.fixture
def gate():
    return SafetyGate()

def test_allow_safe_patch(gate):
    patch = {
        "metadata": {"namespace": "default"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "image": "nginx"
                        }
                    ]
                }
            }
        }
    }
    denials = gate.validate_patch(patch, namespace="default")
    assert len(denials) == 0

def test_deny_host_network(gate):
    patch = {
        "metadata": {"namespace": "default"},
        "spec": {
            "template": {
                "spec": {
                    "hostNetwork": True,
                    "containers": [
                        {
                            "name": "app",
                            "image": "nginx"
                        }
                    ]
                }
            }
        }
    }
    denials = gate.validate_patch(patch)
    assert len(denials) == 1
    assert "hostNetwork" in denials[0]

def test_deny_privileged_container(gate):
    patch = {
        "metadata": {"namespace": "default"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "securityContext": {
                                "privileged": True
                            }
                        }
                    ]
                }
            }
        }
    }
    denials = gate.validate_patch(patch)
    assert len(denials) == 1
    assert "privileged access" in denials[0]

def test_deny_forbidden_capabilities(gate):
    patch = {
        "metadata": {"namespace": "default"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "securityContext": {
                                "capabilities": {
                                    "add": ["SYS_ADMIN"]
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    denials = gate.validate_patch(patch)
    assert len(denials) == 1
    assert "forbidden capability: SYS_ADMIN" in denials[0]

def test_deny_protected_namespace(gate):
    patch = {
        "metadata": {"namespace": "kube-system"},
        "spec": {}
    }
    denials = gate.validate_patch(patch, namespace="kube-system")
    assert len(denials) == 1
    assert "kube-system" in denials[0]
    
def test_deny_host_port(gate):
    patch = {
        "metadata": {"namespace": "default"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "ports": [
                                {"containerPort": 80, "hostPort": 8080}
                            ]
                        }
                    ]
                }
            }
        }
    }
    denials = gate.validate_patch(patch)
    assert len(denials) == 1
    assert "hostPort" in denials[0]
