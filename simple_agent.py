#!/usr/bin/env python3
"""
Simple PostgreSQL Agent
고정 테이블에서 'id' 컬럼만 조회하고, WHERE절을 자연어로 생성하는 간소화된 에이전트
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.schema import HumanMessage, SystemMessage
from sqlalchemy import create_engine, text, inspect
from config import Config
import re

logger = logging.getLogger(__name__)


class SimplePostgreSQLAgent:
    """간소화된 PostgreSQL Agent - 고정 테이블, 'id' SELECT, WHERE절만 처리"""

    def __init__(self):
        """Agent 초기화"""
        Config.validate_environment()
        
        self.engine = create_engine(Config.get_postgres_uri())
        self.db = SQLDatabase.from_uri(Config.get_postgres_uri())
        self.target_table = Config.TARGET_TABLE
        self.target_column = Config.TARGET_COLUMN
        
        # 도메인 특화 프롬프트 컨텍스트 (선택)
        self.domain_context = Config.DOMAIN_CONTEXT
        
        self.llm = None
        try:
            self.llm = ChatOpenAI(
                model=Config.OLLAMA_MODEL,
                api_key=Config.OLLAMA_API_KEY,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                request_timeout=Config.REQUEST_TIMEOUT
            )
            logger.debug(f"Ollama 모델 초기화 완료: {Config.OLLAMA_MODEL} @ {Config.OLLAMA_BASE_URL}")
        except Exception as e:
            logger.warning(f"Ollama 초기화 실패: {e}. 자연어 쿼리 기능을 사용할 수 없습니다.")
        
        self.columns = self._get_table_columns()
        
        logger.debug(f"Simple Agent 초기화 완료 - 테이블: {self.target_table}, 컬럼: {len(self.columns)}개")

    def _get_table_columns(self) -> List[str]:
        """대상 테이블의 컬럼 목록 조회"""
        try:
            inspector = inspect(self.engine)
            columns_info = inspector.get_columns(self.target_table)
            return [col['name'] for col in columns_info]
        except Exception as e:
            logger.error(f"테이블 {self.target_table} 컬럼 조회 실패: {e}")
            return []

    def list_columns(self) -> List[str]:
        """사용 가능한 컬럼 목록 반환"""
        return self.columns.copy()

    def get_sample_data(self, column: str, limit: int = 5) -> List[Any]:
        """특정 컬럼의 샘플 데이터 조회"""
        if column not in self.columns:
            return []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT DISTINCT \"{column}\" FROM {self.target_table} LIMIT {limit}"))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"샘플 데이터 조회 실패: {e}")
            return []

    def get_all_distinct_values(self, column: str) -> List[Any]:
        """지정된 컬럼의 모든 고유값을 가져오기"""
        if column not in self.columns:
            logger.warning(f"컬럼 '{column}'은 테이블에 존재하지 않습니다.")
            return []
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f'SELECT DISTINCT "{column}" FROM {self.target_table} ORDER BY 1'))
                values = [row[0] for row in result.fetchall()]
                logger.debug(f"컬럼 '{column}'에서 {len(values)}개의 고유값을 가져왔습니다.")
                return values
        except Exception as e:
            logger.error(f"컬럼 '{column}'의 고유값 조회 실패: {e}")
            return []

    def execute_fixed_query(self, where_condition: str = "") -> Dict[str, Any]:
        """고정 컬럼에 대한 쿼리를 실행하고 값 목록을 반환"""
        if self.target_column not in self.columns:
            return {
                "success": False,
                "error": f"테이블에 '{self.target_column}' 컬럼이 존재하지 않습니다.",
            }
        
        sql = f'SELECT {self.target_column} FROM {self.target_table}'
        if where_condition.strip():
            sql += f' WHERE {where_condition}'
        sql += f' LIMIT {Config.MAX_RESULTS}'
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                vals = [row[0] for row in result.fetchall()]
            
            logger.debug(f"SQL 실행 성공: {sql} -> {vals}")
            
            return {
                "success": True,
                "sql": sql,
                "result": vals,
                "where_condition": where_condition
            }
        except Exception as e:
            return {
                "success": False,
                "sql": sql,
                "error": str(e)
            }

    def set_domain_context(self, context: str):
        """도메인 특화 프롬프트 컨텍스트를 런타임에 설정"""
        self.domain_context = context.strip()

    def analyze_query(self, natural_query: str) -> str:
        """자연어 질문을 분석해서 WHERE 조건을 추출"""
        if not self.llm:
            raise RuntimeError("Ollama AI 모델이 초기화되지 않았습니다. Ollama 서버가 실행 중인지 확인하세요.")

        # --- ▼▼▼ 수정된 섹션 시작 ▼▼▼ ---

        # 1. 전체 값 컨텍스트를 제공할 컬럼 정의
        # (config.py에서 관리하는 것이 좋습니다)
        context_columns_to_show = ["region", "gang_name", "status"]
        
        # 2. 지정된 컨텍스트 컬럼들에 대해 모든 고유값 가져오기
        context_values_info = []
        for col_name in context_columns_to_show:
            if col_name in self.columns:
                distinct_values = self.get_all_distinct_values(col_name)
                if distinct_values:
                    # 값들을 쉼표로 구분된 문자열로 포맷팅
                    values_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in distinct_values])
                    # 어떤 컬럼의 값인지 명확히 보여주는 라벨 생성
                    context_values_info.append(f"- **'{col_name}'** 컬럼의 사용 가능한 값들: [{values_str}]")

        # 3. 모든 사용 가능한 컬럼에 대한 샘플 데이터 가져오기
        column_sample_info = []
        for col in self.columns:
            samples = self.get_sample_data(col, 3)
            sample_str = ", ".join([f"'{s}'" if isinstance(s, str) else str(s) for s in samples])
            column_sample_info.append(f"- {col} (예시: {sample_str})")

        # 4. 최종 base_prompt를 영어로 구성
        base_prompt = f"""You are an expert at converting natural language questions into PostgreSQL WHERE clauses.
        
Table: {self.target_table}

---
### Context: Here are the actual values contained in some of the columns.
{chr(10).join(context_values_info)}
---
### All Available Columns
{chr(10).join(column_sample_info)}
---

### Instructions
1.  Based on the user's question, generate **only the WHERE clause** for a `SELECT {self.target_column} FROM {self.target_table}` query.
2.  **Do not include the `WHERE` keyword** in your response.
3.  Use `ILIKE` for case-insensitive string comparisons.
4.  If no conditions are needed, return an empty string.

### Examples
-   **Question:** "Which organization is on the outermost edge?"
-   **Answer:** x_coord = (SELECT MIN(x_coord) FROM {self.target_table}) OR x_coord = (SELECT MAX(x_coord) FROM {self.target_table})

-   **Question:** "Maelstrom gangs in the Watson area?"
-   **Answer:** region ILIKE '%Watson%' AND gang_name ILIKE '%Maelstrom%'
"""

        # --- ▲▲▲ 수정된 섹션 끝 ▲▲▲ ---

        # 도메인 특화 컨텍스트가 있으면 추가
        if self.domain_context:
            system_prompt = f"{self.domain_context.strip()}\n\n{base_prompt}"
        else:
            system_prompt = base_prompt
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Question: {natural_query}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            condition = response.content.strip()
            
            # 후처리 로직 (기존과 동일)
            condition = re.sub(r"<think>[\s\S]*?</think>", "", condition, flags=re.IGNORECASE)
            
            if condition.lower().startswith("where "):
                condition = condition[6:]
            if condition.startswith("```"):
                condition = "\n".join(condition.strip("`").split("\n")[1:])
            if condition.endswith("```"):
                condition = condition.split("\n")[0]
            
            lines = [ln.strip() for ln in condition.splitlines() if ln.strip()]
            condition = lines[-1] if lines else ""
            
            if condition.endswith(";"):
                condition = condition[:-1].strip()
            
            logger.debug(f"분석된 WHERE 조건: {condition}")
            return condition
            
        except Exception as e:
            logger.error(f"쿼리 분석 실패: {e}")
            return ""

    def ask(self, natural_query: str) -> Dict[str, Any]:
        """
        자연어 질문으로 데이터 조회
        
        Args:
            natural_query: 자연어 질문 (예: "가장 외곽에 있는 조직이 어디야?")
        """
        try:
            if self.target_column not in self.columns:
                return {
                    "success": False,
                    "natural_query": natural_query,
                    "error": f"'{self.target_column}' 컬럼이 테이블 '{self.target_table}'에 존재하지 않습니다.",
                    "available_columns": self.columns
                }

            where_condition = self.analyze_query(natural_query)
            
            # 쿼리 실행
            result = self.execute_fixed_query(where_condition)
            result["natural_query"] = natural_query
            result["target_column"] = self.target_column
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "natural_query": natural_query,
                "error": str(e)
            }


def create_simple_agent() -> SimplePostgreSQLAgent:
    """Simple Agent 생성"""
    return SimplePostgreSQLAgent()


def quick_query(natural_query: str) -> Dict[str, Any]:
    """빠른 쿼리 실행"""
    agent = create_simple_agent()
    return agent.ask(natural_query) 