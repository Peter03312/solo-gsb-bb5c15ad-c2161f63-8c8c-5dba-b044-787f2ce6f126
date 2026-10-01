"""请求/响应模型。时间一律要求带时区（AwareDatetime），入库前归一化为 UTC。"""
from datetime import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field, field_validator


def _clean_allergens(values: list[str]) -> list[str]:
    cleaned = sorted({v.strip() for v in values if v and v.strip()})
    return cleaned


class MaterialCreate(BaseModel):
    batch_id: str = Field(min_length=1)
    allergens: list[str] = []
    pending: bool = False
    declared_at: Optional[AwareDatetime] = None  # 缺省取服务器当前时间

    @field_validator("allergens")
    @classmethod
    def _v_allergens(cls, v):
        return _clean_allergens(v)


class DeclarationCreate(BaseModel):
    """原料声明更正：追加一个新版本，当前有效声明以最新版本为准。"""

    allergens: list[str] = []
    pending: bool = False
    declared_at: Optional[AwareDatetime] = None

    @field_validator("allergens")
    @classmethod
    def _v_allergens(cls, v):
        return _clean_allergens(v)


class ProcessingCreate(BaseModel):
    processing_id: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    start_utc: AwareDatetime
    end_utc: AwareDatetime
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)

    @field_validator("inputs", "outputs")
    @classmethod
    def _v_batches(cls, v):
        ids = [x.strip() for x in v if x and x.strip()]
        if len(ids) != len(set(ids)):
            raise ValueError("批次号重复")
        if not ids:
            raise ValueError("不能为空")
        return ids


class CleaningCreate(BaseModel):
    equipment_id: str = Field(min_length=1)
    cleaned_at: AwareDatetime
    verified: bool = True


class LabelCreate(BaseModel):
    supersedes_id: Optional[int] = None  # 关联被替代的旧标签


# 声明更正预演请求与正式更正同构；清洗撤销预演/凭据提交无请求体，
# 仅以路径参数（清洗 id / 预演凭据）定位。
class DeclarationPreviewCreate(DeclarationCreate):
    """声明更正预演：拟更正内容（不落库）。"""
