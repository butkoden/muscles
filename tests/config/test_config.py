import sys
import os
from muscles.core.core import Configurator

sys.path.append(f"../")

directory = os.path.dirname(os.path.abspath(__file__))

config = Configurator(file='./config/configuration.yaml', basedir=directory)

def test_config_1():
    assert config.modules.example.package.value() == 'app.modules.example'
    assert config.acl.api.permission.value() == 'nobody'
    assert str(config.acl.api.permission) == 'nobody'
    assert str(config.acl.get('api.permission')) == 'nobody'
    assert dict(config.acl) == {'api': {'permission': 'nobody'}}
    assert repr(config.acl.api) == "Configurator(permission: nobody\n)"
