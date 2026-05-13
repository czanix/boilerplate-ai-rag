from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class Chunk:
    text: str
    metadata: dict
    embedding: list[float] | None = None
    similarity: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))
