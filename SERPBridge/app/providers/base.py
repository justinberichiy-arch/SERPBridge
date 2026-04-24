from abc import ABC, abstractmethod

from app.core.config import ProviderAccount
from app.schemas.serp import OrganicResult, QueryRequest


class BaseSerpProvider(ABC):
    name: str

    def __init__(self, account: ProviderAccount) -> None:
        self.account = account

    @abstractmethod
    async def fetch(self, request: QueryRequest) -> tuple[int, dict]:
        raise NotImplementedError

    @abstractmethod
    def extract_organic(self, raw: dict) -> list[OrganicResult]:
        raise NotImplementedError
