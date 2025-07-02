"""
KCMS Database Schema Definitions
PostgreSQL Docker 컨테이너 동적 스키마 정의
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class ColumnSchema:
    """PostgreSQL 컬럼 스키마"""
    name: str
    type: str  # PostgreSQL 타입 (예: 'integer', 'character varying(100)', 'timestamp without time zone')
    nullable: bool = True
    default: Optional[str] = None
    description: str = ""
    characteristics: str = ""  # 추가: 컬럼의 특성, 용도, 관계에 대한 자연어 설명
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "default": self.default,
            "description": self.description,
            "characteristics": self.characteristics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnSchema':
        """딕셔너리에서 생성"""
        return cls(
            name=data["name"],
            type=data["type"],
            nullable=data.get("nullable", True),
            default=data.get("default"),
            description=data.get("description", ""),
            characteristics=data.get("characteristics", "")
        )


@dataclass
class TableSchema:
    """PostgreSQL 테이블 스키마"""
    name: str
    columns: Dict[str, ColumnSchema]
    description: str = ""
    column_guide: str = ""  # 추가: 컬럼들의 특성과 관계에 대한 자연어 설명
    sample_data: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.sample_data is None:
            self.sample_data = []
    
    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """특정 컬럼 스키마 반환"""
        return self.columns.get(name)
    
    def get_column_names(self) -> List[str]:
        """컬럼 이름 목록"""
        return list(self.columns.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "column_guide": self.column_guide,
            "columns": {name: col.to_dict() for name, col in self.columns.items()},
            "sample_data": self.sample_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSchema':
        """딕셔너리에서 생성"""
        columns = {
            name: ColumnSchema.from_dict(col_data) 
            for name, col_data in data.get("columns", {}).items()
        }
        
        return cls(
            name=data["name"],
            columns=columns,
            description=data.get("description", ""),
            column_guide=data.get("column_guide", ""),
            sample_data=data.get("sample_data", [])
        )


class DatabaseSchema:
    """PostgreSQL 데이터베이스 전체 스키마 관리"""
    
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}
        self.metadata = {
            "database_type": "PostgreSQL",
            "version": "1.0",
            "description": "PostgreSQL Docker 컨테이너 동적 스키마"
        }
    
    def add_table(self, table_schema: TableSchema):
        """테이블 스키마 추가"""
        self.tables[table_schema.name] = table_schema
    
    def get_table(self, table_name: str) -> Optional[TableSchema]:
        """특정 테이블 스키마 반환"""
        return self.tables.get(table_name)
    
    def get_table_names(self) -> List[str]:
        """테이블 이름 목록"""
        return list(self.tables.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "metadata": self.metadata,
            "tables": {name: table.to_dict() for name, table in self.tables.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseSchema':
        """딕셔너리에서 생성"""
        schema = cls()
        schema.metadata = data.get("metadata", schema.metadata)
        
        for table_name, table_data in data.get("tables", {}).items():
            table_schema = TableSchema.from_dict(table_data)
            schema.add_table(table_schema)
        
        return schema
    
    def generate_schema_text(self) -> str:
        """스키마 정보를 텍스트로 변환"""
        if not self.tables:
            return "스키마 정보 없음"
        
        parts = [f"=== PostgreSQL 데이터베이스 스키마 ({len(self.tables)}개 테이블) ===\n"]
        
        for table_name, table in self.tables.items():
            parts.append(f"📋 {table_name}")
            parts.append(f"   설명: {table.description}")
            
            # 컬럼 가이드 추가
            if table.column_guide:
                parts.append(f"   📝 컬럼 특성 가이드: {table.column_guide}")
            
            parts.append(f"   컬럼:")
            
            for col_name, col in table.columns.items():
                nullable_text = "NULL 허용" if col.nullable else "NOT NULL"
                parts.append(f"      - {col_name}: {col.type} ({nullable_text}) - {col.description}")
                
                # 컬럼 특성 설명 추가
                if col.characteristics:
                    parts.append(f"        💡 특성: {col.characteristics}")
            
            if table.sample_data:
                parts.append(f"   샘플 데이터: {len(table.sample_data)}건")
            
            parts.append("")
        
        return "\n".join(parts)


# 기존 gangs 테이블 스키마 (실제 PostgreSQL 구조에 맞게 수정)
def get_gangs_schema() -> TableSchema:
    """Gangs 테이블 스키마 정의"""
    return TableSchema(
        name="gangs",
        description="갱단 정보 및 위치 데이터 테이블",
        column_guide="이 테이블은 갱단 조직의 기본 정보와 지리적 위치를 추적합니다. id는 각 갱단의 고유 식별자이며, x_coord와 y_coord는 서울 지역 기준의 GPS 좌표를 나타냅니다. members_count와 established_year는 갱단의 규모와 역사를 파악하는 핵심 지표이며, status 필드는 현재 활동 상태를 추적하여 수사 우선순위 결정에 활용됩니다.",
        columns={
            "id": ColumnSchema(
                name="id",
                type="integer",
                nullable=False,
                description="갱단 고유 식별자 (기본키)",
                characteristics="시스템에서 자동 생성되는 순차적 번호로, 다른 테이블에서 이 갱단을 참조할 때 사용하는 핵심 키입니다."
            ),
            "name": ColumnSchema(
                name="name",
                type="character varying(100)",
                nullable=False,
                description="갱단 이름"
            ),
            "region": ColumnSchema(
                name="region",
                type="character varying(50)",
                nullable=True,
                description="갱단 활동 지역"
            ),
            "members_count": ColumnSchema(
                name="members_count",
                type="integer",
                nullable=True,
                description="갱단 구성원 수",
                characteristics="갱단의 규모를 나타내는 수치형 데이터로, 위험도 평가와 수사 자원 배분의 기준이 됩니다. 0~100 범위의 값을 가집니다."
            ),
            "established_year": ColumnSchema(
                name="established_year",
                type="integer",
                nullable=True,
                description="갱단 설립 연도"
            ),
            "leader": ColumnSchema(
                name="leader",
                type="character varying(100)",
                nullable=True,
                description="갱단 리더 이름"
            ),
            "status": ColumnSchema(
                name="status",
                type="character varying(20)",
                nullable=True,
                description="갱단 상태 (active, inactive, disbanded 등)",
                characteristics="갱단의 현재 활동 상태를 나타내는 카테고리형 데이터입니다. 'active'는 현재 활발히 활동 중, 'inactive'는 일시적 휴면 상태, 'disbanded'는 해체된 상태를 의미합니다."
            ),
            "x_coord": ColumnSchema(
                name="x_coord",
                type="double precision",
                nullable=True,
                description="갱단 위치 X 좌표",
                characteristics="경도(longitude)를 나타내는 GPS 좌표로, y_coord와 함께 갱단의 지리적 위치를 정확히 표현합니다. 서울 지역 기준으로 126~128 범위의 값을 가집니다."
            ),
            "y_coord": ColumnSchema(
                name="y_coord",
                type="double precision",
                nullable=True,
                description="갱단 위치 Y 좌표",
                characteristics="위도(latitude)를 나타내는 GPS 좌표로, x_coord와 함께 사용되어 지도상의 정확한 위치를 표시할 수 있습니다. 서울 지역 기준으로 37~38 범위의 값을 가집니다."
            ),
            "created_at": ColumnSchema(
                name="created_at",
                type="timestamp without time zone",
                nullable=True,
                default="CURRENT_TIMESTAMP",
                description="레코드 생성 일시"
            ),
            "updated_at": ColumnSchema(
                name="updated_at",
                type="timestamp without time zone",
                nullable=True,
                description="레코드 수정 일시"
            )
        },
        sample_data=[
            {
                "id": 1,
                "name": "Dragons",
                "region": "Downtown",
                "members_count": 25,
                "established_year": 1998,
                "leader": "김용태",
                "status": "active",
                "x_coord": 126.9780,
                "y_coord": 37.5665
            },
            {
                "id": 2,
                "name": "Phoenix Gang",
                "region": "Eastside",
                "members_count": 18,
                "established_year": 2001,
                "leader": "박철수",
                "status": "active",
                "x_coord": 127.0276,
                "y_coord": 37.4979
            }
        ]
    )


def get_default_schema() -> DatabaseSchema:
    """기본 PostgreSQL 스키마 (gangs 테이블 포함)"""
    schema = DatabaseSchema()
    schema.add_table(get_gangs_schema())
    return schema


# 편의 함수들 (하위 호환성)
def get_table_schema(table_name: str) -> Optional[TableSchema]:
    """특정 테이블 스키마 반환"""
    schema = get_default_schema()
    return schema.get_table(table_name)


def get_all_tables() -> Dict[str, TableSchema]:
    """모든 테이블 스키마 반환"""
    schema = get_default_schema()
    return schema.tables


def generate_schema_documentation() -> str:
    """전체 스키마 문서 생성"""
    schema = get_default_schema()
    return schema.generate_schema_text()


def get_sql_agent_context() -> str:
    """SQL Agent용 컨텍스트 문자열 생성"""
    return generate_schema_documentation() 