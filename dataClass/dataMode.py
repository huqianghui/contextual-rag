from pydantic import BaseModel


class ChunkResult(BaseModel):
    chunks: list[str]


class SplitResult(BaseModel):
    tokens: int
    content: str

class MergedChunk(BaseModel):
    splits: str
    totalTokens: int
    note: str

class MergedChunkFile(BaseModel):
    filePath: str
    totalTokens: int

class ChunkFinalResult(BaseModel):
    title: str
    chunk: str
    context: str
    fileName: str