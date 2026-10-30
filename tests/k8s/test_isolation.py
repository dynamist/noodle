"""noodle keeps to its namespace in the shared cluster."""

import json
import subprocess
import uuid

import pytest
import yaml
from conftest import KUBE_CONTEXT, NAMESPACE, ROOT, kubectl, kubectl_json


def probe_from(namespace, host, port, labels=None):
    """Try a TCP connection from a throwaway pod, return True when it connects.

    The pod runs to completion before its log is read: `kubectl run -i` loses
    the output when the container exits before kubectl attaches. It never
    turns ready, so a probe that carries an app's labels is not added to that
    app's Service and gets none of its traffic.
    """
    name = f"probe-{uuid.uuid4().hex[:8]}"
    command = f"nc -z -w 5 {host} {port} && echo OPEN || echo CLOSED"
    container = {
        "name": name,
        "image": "busybox:1.37",
        "command": ["sh", "-c", command],
        "readinessProbe": {"exec": {"command": ["false"]}},
    }
    args = ["run", name, "--restart=Never", "--image=busybox:1.37"]
    args += [f"--overrides={json.dumps({'spec': {'containers': [container]}})}"]
    if labels:
        args += [f"--labels={','.join(f'{key}={value}' for key, value in labels.items())}"]
    kubectl(*args, namespace=namespace)
    try:
        kubectl(
            "wait",
            f"pod/{name}",
            "--for=jsonpath={.status.phase}=Succeeded",
            "--timeout=180s",
            namespace=namespace,
            timeout=200,
        )
        output = kubectl("logs", name, namespace=namespace).stdout
    finally:
        kubectl("delete", "pod", name, "--wait=false", namespace=namespace, check=False)
    assert output.strip() in ("OPEN", "CLOSED"), output
    return output.strip() == "OPEN"


def odoo_client_peer():
    """The namespace selector and the client pod names of odoo-from-dev-apps."""
    policies = yaml.safe_load_all((ROOT / "k8s/base/networkpolicy.yaml").read_text())
    [policy] = [p for p in policies if p["metadata"]["name"] == "odoo-from-dev-apps"]
    [rule] = policy["spec"]["ingress"]
    [peer] = rule["from"]
    selector = ",".join(f"{key}={value}" for key, value in peer["namespaceSelector"]["matchLabels"].items())
    [expression] = peer["podSelector"]["matchExpressions"]
    assert expression["key"] == "app.kubernetes.io/name" and expression["operator"] == "In", expression
    return selector, expression["values"]


def odoo_client_namespaces():
    """Deployed namespaces whose client pods odoo-from-dev-apps lets reach Odoo."""
    selector, _names = odoo_client_peer()
    return [ns["metadata"]["name"] for ns in kubectl_json("get", "namespaces", "-l", selector)["items"]]


def other_namespaces():
    """default plus the namespaces of other dev apps in the shared cluster."""
    selector = f"dynamist.se/dev-app,dynamist.se/dev-app!={NAMESPACE}"
    others = kubectl_json("get", "namespaces", "-l", selector)["items"]
    return ["default", *(ns["metadata"]["name"] for ns in others)]


@pytest.mark.parametrize(
    "host,port", [("odoo.noodle.svc.cluster.local", 8069), ("postgres.noodle.svc.cluster.local", 5432)]
)
def test_other_namespaces_cannot_reach_noodle(host, port):
    """An unlabelled pod is refused everywhere, also in the namespaces of Odoo's clients."""
    for namespace in other_namespaces():
        assert not probe_from(namespace, host, port), f"{host}:{port} is reachable from {namespace}"


def odoo_client_cases():
    _selector, names = odoo_client_peer()
    # postgres is a pod name the clients' namespaces have that must not call Odoo
    return [(name, True) for name in names] + [("postgres", False)]


@pytest.mark.parametrize("name,allowed", odoo_client_cases())
def test_dev_app_clients_reach_odoo(name, allowed):
    """Only the client pods in odoo-from-dev-apps can use the Odoo API, when they are deployed."""
    namespaces = odoo_client_namespaces()
    if not namespaces:
        pytest.skip(f"no namespace matching {odoo_client_peer()[0]} is deployed in the cluster")
    for namespace in namespaces:
        reached = probe_from(namespace, "odoo.noodle.svc.cluster.local", 8069, {"app.kubernetes.io/name": name})
        assert reached == allowed, f"a {name} pod in {namespace} {'cannot' if allowed else 'can'} reach Odoo"


def test_probe_detects_open_ports():
    """Control for the tests above, a probe that can never connect would pass them."""
    assert probe_from("default", "traefik.kube-system.svc.cluster.local", 80)


def test_odoo_reaches_its_database():
    result = kubectl("exec", "deploy/odoo", "--", "pg_isready", "-t", "10")
    assert "accepting connections" in result.stdout


def test_containers_have_requests_and_memory_limits():
    for pod in kubectl_json("get", "pods")["items"]:
        for container in pod["spec"]["containers"]:
            resources = container.get("resources", {})
            assert resources.get("requests"), f"{pod['metadata']['name']}/{container['name']} has no requests"
            assert "memory" in resources.get("limits", {}), f"{pod['metadata']['name']} has no memory limit"


def test_namespace_has_a_quota():
    assert kubectl_json("get", "resourcequota")["items"]


def test_manifests_only_create_the_own_namespace_cluster_wide():
    cluster_kinds = {
        line.split()[-1]
        for line in subprocess.run(
            ["kubectl", "--context", KUBE_CONTEXT, "api-resources", "--namespaced=false", "--no-headers"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    }
    rendered = subprocess.run(
        ["kubectl", "kustomize", str(ROOT / "k8s/overlays/ci")], check=True, capture_output=True, text=True
    ).stdout
    items = [item for item in yaml.safe_load_all(rendered) if item]
    cluster_wide = [(item["kind"], item["metadata"]["name"]) for item in items if item["kind"] in cluster_kinds]
    assert cluster_wide == [("Namespace", NAMESPACE)]
