"""
Two-Ways-A-Design-Fail: Two-axis triage for AI interaction designs.

Axis 1 (disagreement): Panel disagreement flags high between-user over-dispersion.
Axis 2 (systematic over-reliance): Panel convergence on wrong AI flags uniformly harmful designs.

Package version: 0.1.0 (vslice-v0)
"""

__version__ = "0.1.0-vslice-v0"

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class RunManifest:
    """Reproducibility manifest for preregistered analysis runs."""
    timestamp: str
    package_version: str
    config_hash: str
    seeds: dict[str, int]
    config: dict[str, Any]
    
    @classmethod
    def create(cls, config: dict[str, Any], seeds: dict[str, int]) -> "RunManifest":
        """Create a manifest from config and seeds."""
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
        return cls(
            timestamp=datetime.utcnow().isoformat() + "Z",
            package_version=__version__,
            config_hash=config_hash,
            seeds=seeds,
            config=config
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
