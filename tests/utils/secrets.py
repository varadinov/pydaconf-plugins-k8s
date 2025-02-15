import base64

from kubernetes import client, config


def to_base64(value: str) -> str:
    return base64.b64encode(value.encode('utf-8')).decode()

def from_base64(value: str) -> str:
    return base64.b64decode(value.encode('utf-8')).decode()

def create_secret(secret_name: str, secret_data: dict[str, str],  namespace: str = 'default') -> None:
    config.load_kube_config()
    v1 = client.CoreV1Api()

    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=secret_name),
        data= {key: to_base64(value) for key, value in secret_data.items()},
        type="Opaque"
    )

    v1.create_namespaced_secret(namespace=namespace, body=secret)

def update_secret_key(secret_name: str, key: str, value: str, namespace: str = 'default') -> None:
    config.load_kube_config()
    v1 = client.CoreV1Api()

    existing_secret = v1.read_namespaced_secret(secret_name, namespace)
    existing_secret.data[key] = to_base64(value)

    v1.replace_namespaced_secret(secret_name, namespace, existing_secret)
