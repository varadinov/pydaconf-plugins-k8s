import threading
import time
from tempfile import NamedTemporaryFile

import pytest
from kubernetes.config import kube_config
from pydaconf.utils.exceptions import PluginException
from testcontainers.k3s import K3SContainer

from pydaconf_plugins_k8s.secret import K8sSecretPlugin
from tests.utils.secrets import create_secret, update_secret_key


@pytest.fixture(scope="session")
def k3s_cluster() -> K3SContainer:
    """Fixture to spin up a K3s Kubernetes cluster using testcontainers."""
    with K3SContainer() as k3s:
        yaml_config = k3s.config_yaml()

        with NamedTemporaryFile('w') as file:
            # Save kubeconfig to a tempfile
            file.write(yaml_config)
            file.flush()

            # Patch default location
            kube_config.KUBE_CONFIG_DEFAULT_LOCATION = file.name

            yield k3s


def test_read(k3s_cluster: K3SContainer) -> None:
    plugin = K8sSecretPlugin()

    def callback(value: str) -> None:
        _ = value

    create_secret('my-read-secret', {'username': 'user123'})
    secret_value = plugin.run("secret_name=my-read-secret,key=username", callback)
    assert secret_value == 'user123'

def test_read_fail_wrong_secret(k3s_cluster: K3SContainer) -> None:
    plugin = K8sSecretPlugin()

    def callback(value: str) -> None:
        _ = value

    with pytest.raises(PluginException):
        _ = plugin.run("secret_name=wrong_secret,key=username", callback)

def test_read_fail_wrong_key(k3s_cluster: K3SContainer) -> None:
    plugin = K8sSecretPlugin()

    def callback(value: str) -> None:
        _ = value

    create_secret('my-wrong-key-secret', {'username': 'user123'})
    with pytest.raises(PluginException):
        _ = plugin.run("secret_name=my-wrong-key-secret,key=wrongkey", callback)

def test_watch(k3s_cluster: K3SContainer) -> None:
    plugin = K8sSecretPlugin()

    event = threading.Event()
    result = []

    def callback(value: str) -> None:
        result.append(value)
        event.set()

    create_secret('my-watch-secret', {'username': 'user123'})
    returned_value = plugin.run("secret_name=my-watch-secret,key=username,watch=True", callback)
    assert returned_value == 'user123'

    time.sleep(2)
    update_secret_key('my-watch-secret', 'username', 'user4567', 'default')


    # Wait for the callback with a timeout (prevents infinite waiting)
    assert event.wait(timeout=240), "Callback was not called in time"

    # Verify the callback was executed
    assert result == ["user4567"]