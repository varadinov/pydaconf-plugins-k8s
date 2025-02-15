import base64
import logging
import threading
import time
from collections.abc import Callable

from kubernetes import client, config, watch
from kubernetes.client import ApiException
from pydaconf.plugins.base import PluginBase
from pydaconf.utils.exceptions import PluginException

from pydaconf_plugins_k8s.utils import parse_config_string


class K8sSecretPlugin(PluginBase):
    """K8s Secrets plugin. Loads variables based on prefix K8S_SECRET:///"""

    PREFIX='K8S_SECRET'

    def __init__(self) -> None:
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.logger = logging.getLogger(__name__)

    
    def _get_current_namespace(self) -> str:
        """Reads the namespace from the service account file."""

        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
                return f.read().strip()
        except FileNotFoundError:
            self.logger.debug("Namespace file not found, defaulting to 'default'")
            return "default"

    def _read_secret(self, secret_name: str, namespace: str, key: str) -> str:
        try:
            secret = self.v1.read_namespaced_secret(secret_name, namespace)
            secret_value =  next(iter([v for k,v in secret.data.items() if k == key]), None)
            if secret_value is None:
                raise PluginException(f"Secret '{key}' value is None")

            return base64.b64decode(secret_value).decode("utf-8")

        except ApiException as e:
           raise PluginException(f"Failed to read secret '{secret_name}' from Kubernetes API. Error: {e.status} {e.reason}") from e

    def _watch_secret(self, secret_name: str, namespace: str, key: str, on_update_callback: Callable[[str], None]) -> None:
        field_selector = f"metadata.name={secret_name}"

        def watch_secret() -> None:
            while True:
                w = watch.Watch()
                try:
                    self.logger.debug(f"Watching secret '{secret_name}' indefinitely...")
                    secret = self.v1.read_namespaced_secret(secret_name, namespace)
                    resource_version = secret.metadata.resource_version

                    for event in w.stream(self.v1.list_namespaced_secret, namespace=namespace, field_selector=field_selector, resource_version=resource_version):
                        secret = event["object"]
                        event_type = event["type"]

                        self.logger.debug(f"Event: {event_type} - Secret {secret_name} updated.")
                        secret_value = next(iter([v for k,v in secret.data.items() if k == key]), None)
                        if secret_value is None:
                            raise PluginException(f"Secret '{key}' value is None")
                        secret_value_decoded = base64.b64decode(secret_value).decode("utf-8")
                        on_update_callback(secret_value_decoded)
                        
                except client.exceptions.ApiException as e:
                    self.logger.debug(f"K8s API exception was raised during watch for secret '{secret_name}'. Error: {e}")

                except Exception as e:
                    self.logger.debug(f"Exception was raised during watch for secret '{secret_name}'. Error: {e}")

                # Wait before retrying
                time.sleep(20)

        threading.Thread(target=watch_secret, daemon=True, name=f"{__name__}.{key}").start()
        

    def run(self, value: str, on_update_callback: Callable[[str], None]) -> str:
        plugin_config = parse_config_string(value)
        secret_name = plugin_config.get('secret_name')
        key = plugin_config.get('key')
        assert secret_name and key

        namespace = plugin_config.get('namespace', 'default')
        enable_watch = plugin_config.get('watch', False)

        if not plugin_config.get('namespace'):
            namespace = self._get_current_namespace()
        
        secret_value = self._read_secret(secret_name, namespace, key)
        
        if enable_watch:
            self._watch_secret(secret_name, namespace, key, on_update_callback)

        return secret_value

