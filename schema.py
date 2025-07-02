"""
Database Schema Definitions
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