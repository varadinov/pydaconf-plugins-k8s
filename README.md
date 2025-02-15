# Pydaconf Kubernetes Secrets Plugin
Pydaconf plugin for Kubernetes Secrets

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/varadinov/pydaconf-plugins-k8s/ci.yaml)
![GitHub last commit](https://img.shields.io/github/last-commit/varadinov/pydaconf-plugins-k8s)
![GitHub](https://img.shields.io/github/license/varadinov/pydaconf-plugins-k8s)
[![downloads](https://static.pepy.tech/badge/pydaconf-plugins-k8s/month)](https://pepy.tech/project/pydaconf-plugins-k8s)
![PyPI - Version](https://img.shields.io/pypi/v/pydaconf-plugins-k8s)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydaconf-plugins-k8s)

## Pydaconf 
For more information about Pydaconf see the [Docs](https://varadinov.github.io/pydaconf/).

## Installation
Install using `pip install pydaconf-plugins-k8s`  

## A Simple Example
* Create config file in toml, yaml or json
```yaml
secret: K8S_SECRET:///secret_name=my-secret,key=username
```

* Create Pydantic Model and load the configuration
```python
from pydaconf import PydaConf
from pydantic import BaseModel


class Config(BaseModel):
    secret: str

provider = PydaConf[Config]()
provider.from_file("config.yaml")
print(provider.config.secret)
```

## Supported parameters
Parameters can be passed in the configuration value in the following format:
```
K8S_SECRET:///param1=value1,param2=value2
```

| Parameter  | Description                                                                                                                      |
|------------|----------------------------------------------------------------------------------------------------------------------------------|
| secret_name | The name of the kubernetes secret                                                                                                |
| key        | The key of the specific secret element                                                                                           |
| namespace  | If not provided, the plugin will try to load it from the POD file system. If not available, the 'default' namespace will be used |
| watch | Watch the secret for any updates.                                                                                                |

## OnUpdate callback
The plugin can monitor secret update events and notify the on_update_callback. It starts a background thread and subscribes to updates. When an update occurs, it notifies the on_update_callback, ensuring the value in the configuration stays up to date and next time when you access it, it will be the updated version. You can also subscribe to updates using the `.on_update` method.

```python
from pydaconf import PydaConf
from pydantic import BaseModel

def on_change_callback(key: str, value: str):
    print(f"Configuration updated: {key} -> {value}")

class Config(BaseModel):
    api_key: str

provider = PydaConf[Config]()
provider.from_file("config.yaml")

# Subscribe to updates for api_key
provider.on_update(".api_key", on_change_callback)
```