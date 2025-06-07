import os
import json

def set_doc_manager_settings():
    settings_file = os.path.expanduser(
        "~/.jupyter/lab/user-settings/@jupyterlab/docmanager-extension/plugin.jupyterlab-settings"
    )

    os.makedirs(os.path.dirname(settings_file), exist_ok=True)

    settings = {}
    settings["defaultViewers"] = {}
    settings["defaultViewers"]["csv"] = "editor"

    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=4)

set_doc_manager_settings()

c = get_config()

c.ServerApp.allow_origin = '*'
c.ServerApp.token = ''
c.ServerApp.base_url = '/'
c.ServerApp.default_url = '/lab'

c.Completer.use_jedi = False

c.LanguageServerManager.language_servers = {
    "pylsp": {
        "argv": ["pylsp"],
        "languages": ["python"],
        "mime_types": ["text/x-python"],
        "version": 2,
        "languageId": "python",
        "workspace_configuration": {
            "pylsp.plugins.pydocstyle.enabled": False,
            "pylsp.plugins.pyflakes.enabled": False,
            "pylsp.plugins.mccabe.enabled": False,
            "pylsp.plugins.pylint.enabled": False,
            "pylsp.plugins.pycodestyle.enabled": False,
            "pylsp.plugins.ruff.enabled": True
        }
    }
}

c.KernelSpecManager.ensure_native_kernel = False

c.ServerApp.root_dir = "/srv/workspace"