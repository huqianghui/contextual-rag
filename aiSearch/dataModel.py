from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class Entity:
    id: str
    fileName: str
    title: str
    content: str
    context: str
    title_embedding: Optional[List[float]]
    content_embedding: Optional[List[float]]
    context_embedding: Optional[List[float]]
    