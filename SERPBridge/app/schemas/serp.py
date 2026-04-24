from pydantic import BaseModel


class QueryRequest(BaseModel):
    keyword: str
    country: str = "us"
    language: str = "en"
    device: str = "desktop"
    page: int = 1


class OrganicResult(BaseModel):
    rank: int
    title: str | None = None
    link: str
    display_link: str | None = None
    snippet: str | None = None
