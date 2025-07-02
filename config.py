"""
KCMS Configuration - PostgreSQL Docker Container
PostgreSQL Docker 컨테이너 전용 동적 스키마 검색 SQL Agent
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """PostgreSQL Docker 컨테이너 전용 설정 관리 클래스"""
    
    # AI 모델 설정
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
    DEFAULT_MODEL = "accounts/ijzereen/deployedModels/qwen3-4b-l3nkg"
    TEMPERATURE = 0.1
    
    # 쿼리 제한
    MAX_RESULTS = 10
    MAX_TOKENS = 4000
    REQUEST_TIMEOUT = 30
    
    # PostgreSQL Docker 설정
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
    
    @classmethod
    def validate_environment(cls) -> None:
        """환경변수 유효성 검사"""
        # PostgreSQL 필수 설정들은 기본값이 있으므로 항상 통과
        # AI API 키는 자연어 쿼리 사용시에만 필요
        pass
    
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