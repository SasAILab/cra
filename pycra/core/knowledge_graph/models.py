from pydantic import BaseModel, Field
import uuid
from typing import Dict, Any, List, Optional, Tuple, Literal, get_args
from enum import Enum
class EntityTypeEnum(str, Enum):
    # 参与方
    ContractParty = "合同主体（甲乙方）"
    RelatedParty = "关联方（担保人、代理人）"
    Person = "自然人"
    Organization = "组织机构"

    # 标的物
    Contract = "合同本身"
    ProductService = "产品或服务"
    RightObligation = "权利或义务"
    IntellectualProperty = "知识产权"

    # 核心条款
    Amount = "金额"
    DateTerm = "日期或期限"
    Location = "地点"
    Condition = "条件"
    BreachClause = "违约条款"

    # 时空与度量
    SpecificTime = "具体时间"
    TimeSpan = "时间段"
    SpecificLocation = "具体地点"
    Currency = "货币"
    Unit = "度量单位"
EntityType = Literal[tuple(e.name for e in EntityTypeEnum)]
ENTITY_DES = {
    e.name: e.value
    for e in EntityTypeEnum
}
ENTITY_LIST = list(get_args(EntityType))


class RelationshipTypeEnum(str, Enum):
    signs = "签署"
    pays = "支付"
    provides_delivers = "提供/交付"
    owns_enjoys = "拥有/享有"
    undertakes = "承担"
    specifies_agrees = "指定/约定"
    contains = "包含"
    triggers = "触发"
    applies_to = "适用于"
    is_located_at = "位于"
    occurs_on_during = "发生在"
    has_amount_of = "金额是"
    has_term_of = "期限是"
RelationshipType = Literal[tuple(e.name for e in RelationshipTypeEnum)]
RELATIONSHIP_DES = {e.name: e.value for e in RelationshipTypeEnum}
RELATIONSHIP_LIST = list(get_args(RelationshipType))

class EntitySchema(BaseModel):
    """
    定义知识图谱中的单个实体。
    """
    id: str = Field(
        default_factory=lambda: f"E_{uuid.uuid4().hex[:8]}",
        description="实体的唯一标识符，建议在全局对齐步骤中重新生成。"
    )
    type: EntityType = Field(
        ...,
        description="实体的类型，必须是预定义的EntityType之一。"
    )
    text: str = Field(
        ...,
        description="从合同原文中抽取的实体文本内容。"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="可选的元数据字段，用于存储标准化值、来源等信息。例如：{'normalized_value': 1000000, 'source_paragraph': 5}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "E_a1b2c3d4",
                "type": "ContractParty",
                "text": "XX科技有限公司",
                "metadata": {
                    "source_char_start": 102,
                    "source_char_end": 109
                }
            }
        }


class RelationshipSchema(BaseModel):
    id: str = Field(
        default_factory=lambda: f"R_{uuid.uuid4().hex[:8]}",
        description="关系的唯一标识符。"
    )
    source_id: str = Field(
        ...,
        description="关系头实体的ID，必须对应一个已存在的EntitySchema的id。"
    )
    target_id: str = Field(
        ...,
        description="关系尾实体的ID，必须对应一个已存在的EntitySchema的id。"
    )
    type: RelationshipType = Field(
        ...,
        description="关系的类型，必须是预定义的RelationshipType之一。"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="可选的元数据字段，用于存储关系的可信度、来源句子等信息。例如：{'confidence': 0.95, 'source_sentence': '甲方应支付100万元'}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "R_e5f6g7h8",
                "source_id": "E_a1b2c3d4", # 指向 "XX科技有限公司"
                "target_id": "E_i9j0k1l2", # 指向 "100万元"
                "type": "pays",
                "metadata": {
                    "confidence": 0.98,
                    "source_sentence": "合同签订后，XX科技有限公司应向乙方支付合同总金额100万元。"
                }
            }
        }