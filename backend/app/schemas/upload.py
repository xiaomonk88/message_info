from pydantic import BaseModel


class UploadResponse(BaseModel):
    path: str  # relative path under data/uploads
    url: str  # /api/v1/files/{path}
    filename: str
    size: int
    mime_type: str
