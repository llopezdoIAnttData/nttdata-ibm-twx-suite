"""
uuid_registry.py — UUID management for Appian package generation

Appian identifies objects by UUID across environments.
This registry ensures UUIDs are:
  - Consistent within a generation run
  - Deterministic for the same IBM artifact (so re-runs produce the same UUIDs)
  - Saved/loaded to persist UUIDs between incremental runs
"""

import uuid
import json
import hashlib
from pathlib import Path
from typing import Optional


class UUIDRegistry:
    """
    Manages UUID assignment for generated Appian objects.

    Strategy: deterministic UUID v5 from namespace + IBM artifact key.
    This ensures the same IBM artifact always maps to the same Appian UUID,
    which is critical for idempotent deployments.
    """

    # Namespace for NTT DATA Profuturo generated objects
    NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID namespace DNS

    def __init__(self, registry_file: Optional[Path] = None):
        self._registry: dict[str, str] = {}
        self._registry_file = registry_file
        if registry_file and Path(registry_file).exists():
            self.load(registry_file)

    def get_or_create(self, key: str) -> str:
        """
        Get UUID for an IBM artifact key, creating deterministically if not found.

        Args:
            key: Unique IBM artifact identifier (e.g. "BO:SolicitudRedencion",
                 "CONST:MAX_MONTO", "BPD:ProcesoRedencion")

        Returns:
            UUID string in standard 8-4-4-4-12 format
        """
        if key not in self._registry:
            # Deterministic UUID v5 from namespace + key
            generated = str(uuid.uuid5(self.NAMESPACE, key))
            self._registry[key] = generated
        return self._registry[key]

    def get(self, key: str) -> Optional[str]:
        """Get UUID if it exists, None otherwise."""
        return self._registry.get(key)

    def register(self, key: str, uuid_str: str):
        """Manually register a known UUID (e.g., from an existing Appian env)."""
        self._registry[key] = uuid_str

    def save(self, path: Path):
        """Persist registry to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)

    def load(self, path: Path):
        """Load registry from JSON file."""
        with open(path, encoding="utf-8") as f:
            self._registry.update(json.load(f))

    def all_uuids(self) -> dict[str, str]:
        """Return a copy of the full registry."""
        return dict(self._registry)

    def __len__(self):
        return len(self._registry)
