"""
PostgreSQL Dynamic SQL Agent
PostgreSQL Docker 컨테이너의 스키마를 동적으로 검색하여 자연어 쿼리를 SQL로 변환하는 에이전트
"""

import logging
from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from config import Config
from schema import DatabaseSchema
from schema_inspector import PostgreSQLSchemaInspector, auto_detect_schema

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLAgent:
    """PostgreSQL Docker 컨테이너 전용 동적 SQL Agent"""
    
    def __init__(self, auto_detect_schema: bool = True):
        """
        PostgreSQL Agent 초기화
        
        Args:
            auto_detect_schema: True면 자동으로 스키마 검색, False면 수동 스키마 설정 필요
        """
        Config.validate_environment()
        
        # AI 모델 초기화
        self.llm = ChatOpenAI(
            model=Config.DEFAULT_MODEL,
            api_key=Config.FIREWORKS_API_KEY,
            base_url=Config.FIREWORKS_BASE_URL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            request_timeout=Config.REQUEST_TIMEOUT
        )
        
        # 데이터베이스 연결
        self.database_uri = Config.get_postgres_uri()
        self.db = SQLDatabase.from_uri(self.database_uri)
        
        # 스키마 관리
        self.schema: Optional[DatabaseSchema] = None
        self.schema_text: str = ""
        
        if auto_detect_schema:
            self.detect_and_load_schema()
        
        logger.info("PostgreSQL Agent 초기화 완료")
    
    def detect_and_load_schema(self) -> DatabaseSchema:
        """PostgreSQL 데이터베이스 스키마 자동 검색 및 로드"""
        logger.info("PostgreSQL 스키마 자동 검색 시작...")
        
        try:
            # 스키마 검색
            self.schema = auto_detect_schema(include_sample_data=True)
            
            # 스키마 텍스트 생성
            self.schema_text = self._generate_schema_text()
            
            logger.info(f"스키마 검색 완료: {len(self.schema.tables)}개 테이블 발견")
            for table_name in self.schema.tables:
                column_count = len(self.schema.tables[table_name].columns)
                logger.info(f"  - {table_name}: {column_count}개 컬럼")
            
            return self.schema
            
        except Exception as e:
            logger.error(f"스키마 자동 검색 실패: {e}")
            raise
    
    def set_manual_schema(self, schema: DatabaseSchema):
        """수동으로 스키마 설정"""
        self.schema = schema
        self.schema_text = self._generate_schema_text()
        logger.info(f"수동 스키마 설정 완료: {len(schema.tables)}개 테이블")
    
    def _generate_schema_text(self) -> str:
        """스키마 정보를 텍스트로 변환"""
        if not self.schema:
            return "스키마 정보 없음"
        
        schema_parts = []
        
        for table_name, table in self.schema.tables.items():
            table_info = [f"\n=== {table_name} 테이블 ==="]
            table_info.append(f"설명: {table.description}")
            table_info.append("컬럼:")
            
            for col_name, col in table.columns.items():
                nullable_text = "NULL 허용" if col.nullable else "NOT NULL"
                table_info.append(f"  - {col_name}: {col.type} ({nullable_text}) - {col.description}")
            
            # 샘플 데이터 추가
            if hasattr(table, 'sample_data') and table.sample_data:
                table_info.append("샘플 데이터:")
                for i, sample in enumerate(table.sample_data[:2], 1):
                    sample_str = ", ".join([f"{k}={v}" for k, v in sample.items()])
                    table_info.append(f"  {i}. {sample_str}")
            
            schema_parts.append("\n".join(table_info))
        
        return "\n".join(schema_parts)
    
    def _create_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        return f"""당신은 PostgreSQL 데이터베이스 전문 SQL 쿼리 생성 어시스턴트입니다.

다음 PostgreSQL 데이터베이스 스키마를 사용하여 사용자의 자연어 요청을 SQL 쿼리로 변환하세요:

{self.schema_text}

규칙:
1. PostgreSQL 문법을 사용하세요
2. 항상 올바른 테이블명과 컬럼명을 사용하세요
3. 결과 개수는 최대 {Config.MAX_RESULTS}개로 제한하세요 (LIMIT 사용)
4. 복잡한 쿼리의 경우 JOIN을 적절히 사용하세요
5. WHERE 조건을 명확히 작성하세요
6. 날짜/시간 비교 시 PostgreSQL의 날짜 함수를 사용하세요
7. 대소문자를 구분하지 않는 검색은 ILIKE를 사용하세요

응답 형식:
- SQL 쿼리만 반환하세요 (설명 없이)
- 쿼리는 실행 가능한 형태여야 합니다
- SELECT 문을 우선적으로 사용하세요"""

    def generate_sql(self, question: str) -> str:
        """자연어 질문을 SQL 쿼리로 변환"""
        if not self.schema:
            raise RuntimeError("스키마가 로드되지 않았습니다. detect_and_load_schema()를 먼저 실행하세요.")
        
        messages = [
            SystemMessage(content=self._create_system_prompt()),
            HumanMessage(content=f"다음 질문에 대한 SQL 쿼리를 생성하세요: {question}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            sql_query = response.content.strip()
            
            # SQL 쿼리 정리 (마크다운 제거 등)
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            
            logger.info(f"생성된 SQL 쿼리: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"SQL 생성 실패: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> str:
        """SQL 쿼리 실행"""
        try:
            result = self.db.run(sql_query)
            logger.info(f"쿼리 실행 성공: {len(result)} 문자")
            return result
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            return f"쿼리 실행 오류: {str(e)}"
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        자연어 질문에 대한 완전한 처리 (SQL 생성 + 실행)
        
        Returns:
            Dict with 'question', 'sql', 'result', 'success' keys
        """
        try:
            # SQL 생성
            sql_query = self.generate_sql(question)
            
            # SQL 실행
            result = self.execute_query(sql_query)
            
            return {
                "question": question,
                "sql": sql_query,
                "result": result,
                "success": True
            }
            
        except Exception as e:
            return {
                "question": question,
                "sql": None,
                "result": f"오류: {str(e)}",
                "success": False
            }
    
    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보 반환"""
        info = Config.get_connection_info()
        
        if self.schema:
            info.update({
                "tables_count": len(self.schema.tables),
                "tables": list(self.schema.tables.keys())
            })
        
        return info
    
    def refresh_schema(self):
        """스키마 새로고침 (테이블이 추가/변경된 경우)"""
        logger.info("스키마 새로고침 중...")
        self.detect_and_load_schema()
    
    def list_tables(self) -> List[str]:
        """테이블 목록 반환"""
        if not self.schema:
            return []
        return list(self.schema.tables.keys())
    
    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블의 상세 정보 반환"""
        if not self.schema or table_name not in self.schema.tables:
            return {"error": f"테이블 '{table_name}'을 찾을 수 없습니다."}
        
        table = self.schema.tables[table_name]
        
        columns_info = []
        for col_name, col in table.columns.items():
            columns_info.append({
                "name": col_name,
                "type": col.type,
                "nullable": col.nullable,
                "description": col.description
            })
        
        return {
            "name": table_name,
            "description": table.description,
            "columns": columns_info,
            "sample_data": getattr(table, 'sample_data', [])
        }


# 기존 SQLAgent와의 호환성을 위한 별칭
class SQLAgent(PostgreSQLAgent):
    """기존 코드 호환성을 위한 별칭"""
    pass


# 편의 함수들
def create_sql_agent(auto_detect: bool = True) -> PostgreSQLAgent:
    """PostgreSQL Agent 생성 편의 함수"""
    return PostgreSQLAgent(auto_detect_schema=auto_detect)


def quick_query(question: str) -> Dict[str, Any]:
    """빠른 쿼리 실행 (일회성)"""
    agent = create_sql_agent()
    return agent.ask(question) 