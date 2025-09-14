import os
from configparser import ConfigParser
from typing import Optional


def vesconfig_read() -> ConfigParser:
    xdg_config_home = (
        os.environ["XDG_CONFIG_HOME"]
        if "XDG_CONFIG_HOME" in os.environ
        else "~/.config"
    )
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "ves/config")),
        os.path.expanduser("~/.vesconfig"),
    ]

    config = ConfigParser()
    config.read(configfiles)
    return config


def vesconfig_user_get(config: ConfigParser) -> Optional[str]:
    if "user" in config:
        if "name" in config["user"] and "email" in config["user"]:
            return f"{config['user']['name']} <{config['user']['email']}>"
    return None
