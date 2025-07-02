"""
Configuration - PostgreSQL Docker Container
PostgreSQL Docker 컨테이너 전용 동적 스키마 검색 SQL Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """PostgreSQL Docker 컨테이너 전용 설정 관리 클래스"""
    
    # AI 모델 설정 - Ollama
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")  # 로컬에서는 임의값
    TEMPERATURE = 0
    
    # 쿼리 제한
    MAX_RESULTS = 10
    MAX_TOKENS = 4000
    REQUEST_TIMEOUT = 30
    
    # PostgreSQL Docker 설정 (환경변수 필수)
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432")) if os.getenv("POSTGRES_PORT") else None
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD") 
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    
    # 고정 테이블 및 컬럼 설정
    TARGET_TABLE = os.getenv("TARGET_TABLE", "gangs")  # 기본값: gangs
    TARGET_COLUMN = os.getenv("TARGET_COLUMN", "id")    # 기본값: id
    
    @classmethod
    def validate_environment(cls) -> None:
        """환경변수 유효성 검사"""
        missing_vars = []
        
        # PostgreSQL 필수 환경변수 검사
        if not cls.POSTGRES_HOST:
            missing_vars.append("POSTGRES_HOST")
        if not cls.POSTGRES_PORT:
            missing_vars.append("POSTGRES_PORT") 
        if not cls.POSTGRES_USER:
            missing_vars.append("POSTGRES_USER")
        if not cls.POSTGRES_PASSWORD:
            missing_vars.append("POSTGRES_PASSWORD")
        if not cls.POSTGRES_DB:
            missing_vars.append("POSTGRES_DB")
            
        if missing_vars:
            raise ValueError(f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        # Ollama 연결 확인은 실제 사용시에 수행
        # 로컬 Ollama 서버가 실행 중이어야 자연어 쿼리 기능을 사용할 수 있습니다.
    
    @classmethod
    def get_postgres_uri(cls) -> str:
        """PostgreSQL URI 생성"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_connection_info(cls) -> dict:
        """연결 정보 반환"""
        return {
            "host": cls.POSTGRES_HOST,
            "port": cls.POSTGRES_PORT,
            "database": cls.POSTGRES_DB,
            "user": cls.POSTGRES_USER,
            "type": "PostgreSQL Docker Container"
        } 