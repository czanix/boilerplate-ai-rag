from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class Document:
    content: str
    source: str
    title: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
