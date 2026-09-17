"""oodev keeps to its namespace in the shared cluster."""

import subprocess
import uuid

import pytest
import yaml
from conftest import KUBE_CONTEXT, NAMESPACE, ROOT, kubectl, kubectl_json


def probe_from(namespace, host, port):
    """Try a TCP connection from a throwaway pod, return True when it connects."""
    name = f"probe-{uuid.uuid4().hex[:8]}"
    result = kubectl(
        "run",
        name,
        "--rm",
        "-i",
        "--quiet",
        "--restart=Never",
        "--image=busybox:1.37",
        "--",
        "sh",
        "-c",
        f"nc -z -w 5 {host} {port} && echo OPEN || echo CLOSED",
        namespace=namespace,
        check=False,
        timeout=180,
    )
    assert "OPEN" in result.stdout or "CLOSED" in result.stdout, result.stdout + result.stderr
    return "OPEN" in result.stdout


def other_namespaces():
    """default plus the namespaces of other dev apps in the shared cluster."""
    selector = f"dynamist.se/dev-app,dynamist.se/dev-app!={NAMESPACE}"
    others = kubectl_json("get", "namespaces", "-l", selector)["items"]
    return ["default", *(ns["metadata"]["name"] for ns in others)]


@pytest.mark.parametrize("host,port", [("odoo.oodev.svc.cluster.local", 8069), ("db.oodev.svc.cluster.local", 5432)])
def test_other_namespaces_cannot_reach_oodev(host, port):
    for namespace in other_namespaces():
        assert not probe_from(namespace, host, port), f"{host}:{port} is reachable from {namespace}"


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
