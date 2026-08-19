package swarmsre.admission

# Default to allow
default allow = true

# If any deny rules trigger, the request is denied
allow = false {
    count(deny) > 0
}

# Deny privileged containers
deny[msg] {
    container := input.request.object.spec.template.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container '%v' is requesting privileged access, which is forbidden.", [container.name])
}

# Deny added capabilities
deny[msg] {
    container := input.request.object.spec.template.spec.containers[_]
    capability := container.securityContext.capabilities.add[_]
    forbidden_caps := {"SYS_ADMIN", "NET_ADMIN", "ALL"}
    forbidden_caps[capability]
    msg := sprintf("Container '%v' is requesting forbidden capability: %v", [container.name, capability])
}

# Deny hostNetwork
deny[msg] {
    input.request.object.spec.template.spec.hostNetwork == true
    msg := "Pod is requesting hostNetwork, which is forbidden."
}

# Deny hostPort
deny[msg] {
    container := input.request.object.spec.template.spec.containers[_]
    port := container.ports[_]
    port.hostPort
    msg := sprintf("Container '%v' is requesting a hostPort, which is forbidden.", [container.name])
}

# Helper rule to get the namespace, preferring the request context over the object metadata
req_namespace := input.request.namespace {
    input.request.namespace != ""
} else := input.request.object.metadata.namespace

# Deny patches to critical namespaces
deny[msg] {
    protected_namespaces := {"kube-system", "swarmsre-system"}
    protected_namespaces[req_namespace]
    msg := sprintf("Modifications to the protected namespace '%v' are forbidden.", [req_namespace])
}


