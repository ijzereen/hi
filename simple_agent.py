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

    def analyze_query(self, natural_query: str) -> str:
        """자연어 질문을 분석해서 WHERE 조건을 추출"""
        if not self.llm:
            raise RuntimeError("Ollama AI 모델이 초기화되지 않았습니다. Ollama 서버가 실행 중인지 확인하세요.")
        
        column_info = []
        for col in self.columns:
            samples = self.get_sample_data(col, 3)
            sample_str = ", ".join([f"'{s}'" if isinstance(s, str) else str(s) for s in samples[:3]])
            column_info.append(f"- {col}: 예시값 [{sample_str}]")
        
        system_prompt = f"""당신은 자연어 질문을 PostgreSQL WHERE 절로 변환하는 전문가입니다.
        
테이블: {self.target_table}
사용 가능한 컬럼:
{chr(10).join(column_info)}

사용자의 질문을 기반으로 'SELECT {self.target_column} FROM {self.target_table}' 쿼리에 사용할 WHERE 절만 생성해주세요.
- WHERE 키워드는 포함하지 마세요.
- 문자열 비교는 ILIKE를 사용하세요 (대소문자 무시).
- 조건이 필요 없으면 아무것도 출력하지 마세요.

예시 질문: "가장 외곽에 있는 조직이 어디야?"
예시 답변: x_coord = (SELECT MIN(x_coord) FROM {self.target_table}) OR x_coord = (SELECT MAX(x_coord) FROM {self.target_table})

예시 질문: "Watson 지역의 Maelstrom 갱단은?"
예시 답변: region ILIKE '%Watson%' AND gang_name ILIKE '%Maelstrom%'
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"질문: {natural_query}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            condition = response.content.strip()
            
            # 1) Remove chain-of-thought blocks like <think>...</think>
            condition = re.sub(r"<think>[\s\S]*?</think>", "", condition, flags=re.IGNORECASE)
            
            # 2) Strip markdown or leading keywords
            if condition.lower().startswith("where "):
                condition = condition[6:]
            if condition.startswith("```"):
                # remove triple backtick fencing
                condition = "\n".join(condition.strip("`").split("\n")[1:])
            if condition.endswith("```"):
                condition = condition.split("\n")[0]
            
            # 3) Get the last non-empty line (safest assumption of actual SQL)
            lines = [ln.strip() for ln in condition.splitlines() if ln.strip()]
            condition = lines[-1] if lines else ""
            
            # 4) Remove trailing semicolon if exists
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