from pydantic import BaseModel, Field, computed_field


class CommonPaginatedQuery(BaseModel):
    page: int = Field(None, ge=1)
    page_size: int = Field(None, gt=0)

    @computed_field
    @property
    def offset(self) -> int | None:
        if self.page is None and self.page_size is not None:
            return 0
        if self.page_size is not None:
            return (self.page - 1) * self.page_size
        return None

    @computed_field
    @property
    def limit(self) -> int:
        if self.page_size is None and self.page_size is not None:
            return 10
        return self.page_size
