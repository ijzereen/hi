"""
PostgreSQL Docker 스키마 검색기
PostgreSQL 데이터베이스의 테이블 구조를 동적으로 분석하여 SQL Agent가 사용할 수 있는 스키마 정보를 생성합니다.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional, Any
import logging
from config import Config
from schema import DatabaseSchema, TableSchema, ColumnSchema

# 로거 설정
logger = logging.getLogger(__name__)

class PostgreSQLSchemaInspector:
    """PostgreSQL 데이터베이스 스키마 동적 검색기"""
    
    def __init__(self):
        """PostgreSQL 스키마 검색기 초기화"""
        self.engine = None
        self.inspector = None
        
    def connect(self) -> bool:
        """PostgreSQL 데이터베이스 연결"""
        try:
            self.engine = create_engine(Config.get_postgres_uri())
            self.inspector = inspect(self.engine)
            
            # 연결 테스트
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logging.info(f"PostgreSQL 연결 성공: {Config.get_connection_info()}")
            return True
            
        except SQLAlchemyError as e:
            logging.error(f"PostgreSQL 연결 실패: {e}")
            return False
    
    def get_all_tables(self, schema: str = 'public') -> List[str]:
        """모든 테이블 목록 조회"""
        if not self.inspector:
            raise RuntimeError("데이터베이스에 연결되지 않았습니다.")
        
        try:
            return self.inspector.get_table_names(schema=schema)
        except SQLAlchemyError as e:
            logging.error(f"테이블 목록 조회 실패: {e}")
            return []
    
    def get_table_columns(self, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """테이블의 컬럼 정보 조회"""
        if not self.inspector:
            raise RuntimeError("데이터베이스에 연결되지 않았습니다.")
        
        try:
            return self.inspector.get_columns(table_name, schema=schema)
        except SQLAlchemyError as e:
            logging.error(f"테이블 {table_name} 컬럼 정보 조회 실패: {e}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """테이블의 샘플 데이터 조회"""
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except SQLAlchemyError as e:
            logging.error(f"테이블 {table_name} 샘플 데이터 조회 실패: {e}")
            return []
    
    def inspect_database_schema(self, include_sample_data: bool = True) -> DatabaseSchema:
        """전체 데이터베이스 스키마 검색"""
        if not self.connect():
            raise RuntimeError("데이터베이스 연결에 실패했습니다.")
        
        database_schema = DatabaseSchema()
        # 단일 테이블만 대상 (Config.TARGET_TABLE)
        target_table = Config.TARGET_TABLE
        if not target_table:
            raise RuntimeError("Config.TARGET_TABLE 값이 설정되어 있지 않습니다.")
        table_names = [target_table]
        logging.info(f"대상 테이블: {target_table}")
        
        for table_name in table_names:
            try:
                # 컬럼 정보 조회
                columns_info = self.get_table_columns(table_name)
                if not columns_info:
                    continue
                
                # 컬럼 스키마 생성
                columns = {}
                for col_info in columns_info:
                    col_name = col_info['name']
                    col_type = str(col_info['type'])
                    nullable = col_info.get('nullable', True)
                    default = col_info.get('default', None)
                    
                    # 자동 설명 생성
                    description = self._generate_column_description(
                        table_name, col_name, col_type, nullable
                    )
                    
                    columns[col_name] = ColumnSchema(
                        name=col_name,
                        type=col_type,
                        nullable=nullable,
                        default=default,
                        description=description
                    )
                
                # 샘플 데이터 수집
                sample_data = []
                if include_sample_data:
                    sample_data = self.get_sample_data(table_name)
                
                # 테이블 설명 생성
                table_description = self._generate_table_description(
                    table_name, list(columns.keys()), sample_data
                )
                
                # 테이블 스키마 추가
                database_schema.add_table(TableSchema(
                    name=table_name,
                    columns=columns,
                    description=table_description,
                    sample_data=sample_data
                ))
                
                logging.info(f"테이블 '{table_name}' 스키마 분석 완료 (컬럼 {len(columns)}개)")
                
            except Exception as e:
                logging.error(f"테이블 '{table_name}' 분석 중 오류: {e}")
                continue
        
        logging.info(f"데이터베이스 스키마 검색 완료: 총 {len(database_schema.tables)}개 테이블")
        return database_schema
    
    def _generate_column_description(
        self, 
        table_name: str, 
        col_name: str, 
        col_type: str, 
        nullable: bool
    ) -> str:
        """컬럼 자동 설명 생성"""
        desc_parts = []
        
        # 기본 타입 설명
        if 'int' in col_type.lower() or 'serial' in col_type.lower():
            desc_parts.append("정수형")
        elif 'varchar' in col_type.lower() or 'text' in col_type.lower():
            desc_parts.append("문자열")
        elif 'timestamp' in col_type.lower() or 'date' in col_type.lower():
            desc_parts.append("날짜/시간")
        elif 'boolean' in col_type.lower():
            desc_parts.append("참/거짓")
        elif 'decimal' in col_type.lower() or 'numeric' in col_type.lower():
            desc_parts.append("숫자")
        
        # 특수 컬럼명 추론
        col_lower = col_name.lower()
        if col_lower in ['id', 'pk', 'primary_key']:
            desc_parts.append("기본키")
        elif col_lower.endswith('_id'):
            desc_parts.append("외래키")
        elif col_lower in ['name', 'title']:
            desc_parts.append("이름/제목")
        elif col_lower in ['email', 'mail']:
            desc_parts.append("이메일 주소")
        elif col_lower in ['phone', 'tel', 'mobile']:
            desc_parts.append("전화번호")
        elif col_lower in ['address', 'addr']:
            desc_parts.append("주소")
        elif col_lower in ['created_at', 'create_time']:
            desc_parts.append("생성일시")
        elif col_lower in ['updated_at', 'update_time', 'modified_at']:
            desc_parts.append("수정일시")
        elif col_lower in ['status', 'state']:
            desc_parts.append("상태")
        elif col_lower in ['count', 'cnt']:
            desc_parts.append("개수")
        elif col_lower in ['price', 'amount', 'cost']:
            desc_parts.append("금액")
        
        # Nullable 정보
        if not nullable:
            desc_parts.append("필수")
        
        return f"{table_name} 테이블의 {', '.join(desc_parts) if desc_parts else '데이터'} 컬럼"
    
    def _generate_table_description(
        self, 
        table_name: str, 
        columns: List[str], 
        sample_data: List[Dict[str, Any]]
    ) -> str:
        """테이블 자동 설명 생성"""
        desc = f"{table_name} 테이블 (컬럼 {len(columns)}개)"
        
        if sample_data:
            desc += f", {len(sample_data)}개 샘플 데이터 포함"
        
        # 주요 컬럼 언급
        key_columns = [col for col in columns if any(
            keyword in col.lower() 
            for keyword in ['id', 'name', 'title', 'email', 'status']
        )]
        
        if key_columns:
            desc += f". 주요 컬럼: {', '.join(key_columns[:3])}"
        
        return desc
    
    def export_schema_code(self, schema: DatabaseSchema, output_file: str = "detected_schema.py"):
        """검색된 스키마를 Python 코드로 내보내기"""
        code_lines = [
            '"""',
            '자동 검색된 PostgreSQL 데이터베이스 스키마',
            f'총 {len(schema.tables)}개 테이블',
            '"""',
            '',
            'import logging',
            'from schema import DatabaseSchema, TableSchema, ColumnSchema',
            '',
            'logger = logging.getLogger(__name__)',
            '',
            'def get_detected_schema() -> DatabaseSchema:',
            '    """검색된 데이터베이스 스키마 반환"""',
            '    schema = DatabaseSchema()',
            ''
        ]
        
        for table in schema.tables.values():
            code_lines.extend([
                f'    # {table.name} 테이블',
                f'    schema.add_table(TableSchema(',
                f'        name="{table.name}",',
                f'        description="{table.description}",',
                f'        columns={{'
            ])
            
            for col in table.columns.values():
                code_lines.append(
                    f'            "{col.name}": ColumnSchema('
                    f'name="{col.name}", type="{col.type}", '
                    f'nullable={col.nullable}, description="{col.description}"),'
                )
            
            code_lines.extend([
                '        }',
                '    ))',
                ''
            ])
        
        code_lines.extend([
            '    return schema',
            '',
            'if __name__ == "__main__":',
            '    schema = get_detected_schema()',
            '    logger.info(f"로드된 스키마: {len(schema.tables)}개 테이블")',
            '    for table_name in schema.tables:',
            '        logger.info(f"- {table_name}")'
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(code_lines))
        
        logger.info(f"스키마 코드를 {output_file}에 저장했습니다.")
    
    def close(self):
        """연결 해제"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.inspector = None


# 편의 함수들
def auto_detect_schema(include_sample_data: bool = True) -> DatabaseSchema:
    """PostgreSQL 스키마 자동 검색"""
    inspector = PostgreSQLSchemaInspector()
    try:
        return inspector.inspect_database_schema(include_sample_data)
    finally:
        inspector.close()


def export_current_schema(output_file: str = "detected_schema.py") -> DatabaseSchema:
    """
    현재 데이터베이스 스키마를 검색하고 Python 코드로 내보내기
    
    Args:
        output_file: 출력할 파일명
        
    Returns:
        DatabaseSchema: 검색된 스키마 객체
    """
    # 스키마 자동 검색
    schema = auto_detect_schema()
    
    # Python 코드 생성
    code_lines = [
        '"""',
        f'자동 검색된 PostgreSQL 데이터베이스 스키마',
        f'총 {len(schema.tables)}개 테이블',
        '"""',
        '',
        'from schema import DatabaseSchema, TableSchema, ColumnSchema',
        '',
        'def get_detected_schema() -> DatabaseSchema:',
        '    """검색된 데이터베이스 스키마 반환"""',
        '    schema = DatabaseSchema()',
        ''
    ]
    
    # 각 테이블 코드 생성
    for table_name, table in schema.tables.items():
        code_lines.append(f'    # {table_name} 테이블')
        code_lines.append(f'    schema.add_table(TableSchema(')
        code_lines.append(f'        name="{table_name}",')
        code_lines.append(f'        description="{table.description}",')
        code_lines.append(f'        columns={{')
        
        for col_name, col in table.columns.items():
            code_lines.append(f'            "{col_name}": ColumnSchema(name="{col_name}", type="{col.type}", nullable={col.nullable}, description="{col.description}"),')
        
        code_lines.append(f'        }}')
        code_lines.append(f'    ))')
        code_lines.append('')
    
    code_lines.extend([
        '    return schema',
        '',
        'if __name__ == "__main__":',
        '    schema = get_detected_schema()',
        f'    logger.info(f"로드된 스키마: {{len(schema.tables)}}개 테이블")',
        '    for table_name in schema.tables:',
        f'        logger.info(f"- {{table_name}}")'
    ])
    
    # 파일에 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(code_lines))
    
    logger.info(f"스키마 코드를 {output_file}에 저장했습니다.")
    
    return schema 