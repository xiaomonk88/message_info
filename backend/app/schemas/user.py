from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    owned_records: int = 0
    module_grants: int = 0
    shared_records: int = 0


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    role: Literal["admin", "member"] = "member"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[Literal["admin", "member"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # 管理员重置密码


class ModuleGrantItem(BaseModel):
    module_id: int
    scope: Literal["own", "all"] = "own"
    can_create: bool = True
    can_edit: bool = False
    can_delete: bool = False


class ModuleGrantOut(ModuleGrantItem):
    granted: bool = True  # False 表示没有板块授权、只是被分配了其中的记录
    shared_records: int = 0


class GrantsUpdate(BaseModel):
    items: list[ModuleGrantItem] = Field(default_factory=list)


class RecordAccessEntry(BaseModel):
    user_id: int
    username: str
    display_name: Optional[str] = None
    can_edit: bool


class RecordAccessOut(BaseModel):
    owner_id: Optional[int] = None
    owner: Optional[str] = None
    shared: list[RecordAccessEntry] = Field(default_factory=list)


class RecordAccessUpdate(BaseModel):
    """整体替换单条记录的分配名单。"""

    shared: list[dict] = Field(default_factory=list)  # [{user_id, can_edit}]


class RecordAssignRequest(BaseModel):
    record_ids: list[int]
    user_ids: list[int]
    mode: Literal["share", "unshare", "transfer"] = "share"
    can_edit: bool = False
