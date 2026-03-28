"""JSON store management — entries CRUD + diff."""
import json
import time
from nsync import crypto


def empty_store(device_id: str = "") -> dict:
    return {"version": 1, "entries": {}, "metadata": {"last_modified": "", "modified_by": device_id}}


def _stamp(store: dict, device_id: str) -> dict:
    store["metadata"]["last_modified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    store["metadata"]["modified_by"] = device_id
    return store


def load_encrypted(blob: bytes, key: str) -> dict:
    return json.loads(crypto.decrypt(blob, key))


def dump_encrypted(store: dict, key: str) -> bytes:
    return crypto.encrypt(json.dumps(store, sort_keys=True).encode(), key)


def get(store: dict, path: str) -> str | None:
    return store["entries"].get(path)


def ls(store: dict) -> list[str]:
    return sorted(store["entries"].keys())


def add(store: dict, path: str, content: str, device_id: str) -> dict:
    store["entries"][path] = content
    return _stamp(store, device_id)


def remove(store: dict, path: str, device_id: str) -> dict:
    store["entries"].pop(path, None)
    return _stamp(store, device_id)


def diff(local: dict, remote: dict) -> dict:
    """Compare two stores. Returns {added: [], modified: [], deleted: []}."""
    l_entries, r_entries = local.get("entries", {}), remote.get("entries", {})
    l_keys, r_keys = set(l_entries), set(r_entries)
    return {
        "added": sorted(r_keys - l_keys),
        "modified": sorted(k for k in l_keys & r_keys if l_entries[k] != r_entries[k]),
        "deleted": sorted(l_keys - r_keys),
    }


def make_pending(action: str, path: str, content: str, device_id: str) -> dict:
    return {
        "action": action,
        "path": path,
        "content": content,
        "device": device_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
