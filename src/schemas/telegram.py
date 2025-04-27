from pydantic import BaseModel


class InitDataRequest(BaseModel):
    initData: str
