"""Config file management for nsync (~/.config/nsync/config.json)."""
import json
import os
import secrets
import string

CONFIG_DIR = os.path.expanduser("~/.config/nsync")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "region": "",
    "user_pool_id": "",
    "client_id": "",
    "identity_pool_id": "",
    "bucket": "",
    "username": "",
    "device_password": "",
    "cloud_key": "",
    "refresh_token": "",
    "device_id": "",
    "trusted": False,
}


def _gen_password(length: int = 64) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def load() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return {**DEFAULTS, **json.load(f)}
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def init_config(
    region: str,
    user_pool_id: str,
    client_id: str,
    identity_pool_id: str,
    bucket: str,
    username: str,
    cloud_key: str,
    device_id: str,
    trusted: bool,
) -> dict:
    """Create initial config with auto-generated device password."""
    cfg = {
        **DEFAULTS,
        "region": region,
        "user_pool_id": user_pool_id,
        "client_id": client_id,
        "identity_pool_id": identity_pool_id,
        "bucket": bucket,
        "username": username,
        "device_password": _gen_password(),
        "cloud_key": cloud_key,
        "device_id": device_id,
        "trusted": trusted,
    }
    save(cfg)
    return cfg
