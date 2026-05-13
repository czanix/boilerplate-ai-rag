from abc import ABC, abstractmethod

class LLMPort(ABC):
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1024) -> str: ...
