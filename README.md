# Simple PostgreSQL SQL Agent

**고정 테이블에서 한 컬럼만 SELECT하고 WHERE절만 자연어로 생성**하는 간소화된 SQL Agent입니다.

## 🎯 핵심 기능 (간소화됨)

- **고정 테이블**: 하나의 테이블만 지정하여 작업 단순화
- **단일 컬럼 SELECT**: 사용자가 선택한 컬럼 하나만 조회
- **WHERE절 자연어 변환**: AI로 자연어 조건을 WHERE절로 변환
- **즉시 실행**: 복잡한 스키마 분석 없이 바로 쿼리 실행

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# PostgreSQL Docker 컨테이너 실행
docker-compose up -d
```

### 2. 환경변수 설정 (필수)

`.env` 파일 생성:
```bash
# PostgreSQL 설정 (모든 값 필수)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# 고정 테이블·컬럼 설정
TARGET_TABLE=gangs
TARGET_COLUMN=id

# (선택) 도메인 특화 컨텍스트 – 공백이 포함되면 꼭 따옴표 사용!
DOMAIN_CONTEXT="Night City 갱단 DB"

# AI 모델 설정 - Ollama (자연어 쿼리용)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:4b
OLLAMA_API_KEY=ollama
```

**주의**: 모든 PostgreSQL 환경변수가 필수이며, TARGET_TABLE로 작업할 테이블을 지정할 수 있습니다.

### 3. Ollama 설치 및 실행 (자연어 쿼리용)

자연어 조건을 WHERE절로 변환하려면 Ollama가 필요합니다:

```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서버 시작
ollama serve

# qwen3:4b 모델 다운로드 (새 터미널에서)
ollama pull qwen3:4b
```

**참고**: Ollama 없이도 직접 SQL WHERE 조건을 입력하여 사용할 수 있습니다.

## 📖 사용법

### 기본 명령어

```bash
# 데이터베이스 및 테이블 정보 확인
python main.py --info

# 특정 컬럼 조회 (조건 없음)
python main.py --column name

# 자연어 조건으로 컬럼 조회
python main.py --column name --condition "Downtown 지역"

# 대화형 모드 (기본값)
python main.py
```

### 대화형 모드 사용법

- `컬럼명` - 해당 컬럼의 모든 값 조회
- `컬럼명 조건` - 자연어 조건으로 필터링하여 조회
- `info` - 데이터베이스 및 테이블 정보
- `columns` - 사용 가능한 컬럼 목록
- `quit` / `exit` / `q` - 종료

### 예시 사용법

```bash
🤔 입력: name                    # name 컬럼의 모든 값
🤔 입력: name Downtown 지역       # Downtown 지역의 조직 이름들
🤔 입력: status 활성            # 활성 상태인 조직들의 status
🤔 입력: members_count 10명 이상  # 10명 이상인 조직들의 멤버 수
```

## 🔧 시스템 구조

### 핵심 컴포넌트 (간소화됨)

1. **main.py** - 메인 실행 파일 및 CLI 인터페이스
2. **simple_agent.py** - 간소화된 SQL Agent (WHERE절만 처리)
3. **config.py** - 설정 관리 (고정 테이블 포함)
4. **schema.py** - 기본 스키마 정의 (간소화됨)

## 🆕 자연어 컬럼 설명 기능

### 테이블 레벨 가이드 (`column_guide`)
```python
TableSchema(
    name="organizations",
    column_guide="이 테이블은 조직의 기본 정보와 지리적 위치를 추적합니다. 
                 x_coord와 y_coord는 GPS 좌표를 나타냅니다..."
)
```

### 컬럼 레벨 특성 (`characteristics`)
```python
ColumnSchema(
    name="members_count",
    characteristics="조직의 규모를 나타내는 수치형 데이터로, 조직 평가와 자원 배분의 기준이 됩니다."
)
```

이러한 자연어 설명들은 AI 모델에게 더 풍부한 컨텍스트를 제공하여 더 정확한 SQL 쿼리를 생성합니다.

## 📊 데이터베이스 구조

이 시스템은 **완전 동적 스키마 검색**을 사용합니다:

- 실행 시점에 PostgreSQL 데이터베이스에 연결하여 모든 테이블과 컬럼 정보를 실시간으로 검색
- 하드코딩된 스키마 정의 없음 - 모든 스키마 정보는 `schema_inspector.py`를 통해 동적으로 수집
- 테이블 구조가 변경되어도 별도 수정 없이 자동으로 새 구조를 인식

**스키마 확인 방법:**
```bash
# 현재 데이터베이스의 모든 테이블 구조 확인
python main.py --scan
```

## 🚨 트러블슈팅

### PostgreSQL 연결 오류
```bash
# Docker 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart
```

### AI 모델 오류
- `FIREWORKS_API_KEY` 환경변수 확인
- API 키 유효성 검증

## 📋 의존성

- **PostgreSQL**: psycopg2-binary
- **AI**: langchain, langchain-openai
- **Schema**: sqlalchemy
- **Utils**: python-dotenv

## 📁 파일 구조 (간소화됨)

```
project/
├── main.py              # 메인 실행 파일 및 CLI
├── simple_agent.py      # 간소화된 SQL Agent
├── config.py            # 설정 관리 (고정 테이블 포함)
├── schema.py            # 기본 스키마 정의
├── docker-compose.yml   # PostgreSQL 컨테이너
├── requirements.txt     # Python 의존성
└── README.md           # 이 파일
```

## 🔨 다른 환경에서 구현하기

다른 컴퓨터에서 이 프로젝트를 구현할 때는 **최소 기능부터 단계별로** 구현하는 것을 권장합니다.

### 1단계: 기본 연결 테스트 (5분)

먼저 환경변수를 설정하고 데이터베이스 연결을 확인하세요:

1. `.env` 파일 생성:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_actual_user
POSTGRES_PASSWORD=your_actual_password
POSTGRES_DB=your_actual_database
```

2. 기본 `config.py` 생성:
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    
    @classmethod
    def get_postgres_uri(cls) -> str:
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
```

**연결 테스트:**
```python
# test_connection.py
from sqlalchemy import create_engine, text
from config import Config

try:
    engine = create_engine(Config.get_postgres_uri())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("✅ PostgreSQL 연결 성공!")
        print(f"버전: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

### 2단계: 수동 SQL 실행 (10분)

AI 없이 수동으로 SQL을 실행하는 간단한 에이전트부터 만드세요:

```python
# simple_agent.py
from langchain_community.utilities import SQLDatabase
from config import Config

class SimpleAgent:
    def __init__(self):
        self.db = SQLDatabase.from_uri(Config.get_postgres_uri())
    
    def execute_sql(self, sql: str) -> str:
        """SQL 직접 실행"""
        try:
            result = self.db.run(sql)
            return result
        except Exception as e:
            return f"오류: {e}"
    
    def list_tables(self) -> str:
        """테이블 목록 조회"""
        return self.execute_sql("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")

# 테스트
if __name__ == "__main__":
    agent = SimpleAgent()
    print("=== 테이블 목록 ===")
    print(agent.list_tables())
```

### 3단계: 기본 CLI (5분)

```python
# minimal_main.py
from simple_agent import SimpleAgent

def main():
    agent = SimpleAgent()
    
    print("🔍 최소 SQL Agent 테스트")
    print("명령어: 'tables' (테이블 목록), 'quit' (종료)")
    print("-" * 40)
    
    while True:
        user_input = input("\n📝 SQL 또는 명령어: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("👋 종료")
            break
        elif user_input.lower() == 'tables':
            print(agent.list_tables())
        elif user_input:
            print(f"결과:\n{agent.execute_sql(user_input)}")

if __name__ == "__main__":
    main()
```

### 4단계: 기본 스키마 구조 (10분)

```python
# basic_schema.py 
from dataclasses import dataclass
from typing import Dict

@dataclass
class ColumnSchema:
    name: str
    type: str
    description: str = ""

@dataclass 
class TableSchema:
    name: str
    columns: Dict[str, ColumnSchema]
    description: str = ""

class DatabaseSchema:
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}
    
    def add_table(self, table: TableSchema):
        self.tables[table.name] = table
    
    def generate_schema_text(self) -> str:
        parts = []
        for table_name, table in self.tables.items():
            parts.append(f"테이블: {table_name}")
            for col_name, col in table.columns.items():
                parts.append(f"  - {col_name}: {col.type} ({col.description})")
        return "\n".join(parts)

# 실제 DB 테이블로 수정 필요!
def get_test_schema() -> DatabaseSchema:
    schema = DatabaseSchema()
    schema.add_table(TableSchema(
        name="your_actual_table_name",  # ← 실제 테이블명으로 변경
        columns={
            "id": ColumnSchema("id", "integer", "기본키"),
            "name": ColumnSchema("name", "varchar", "이름")
        }
    ))
    return schema
```

### 5단계: AI 기능 추가

환경변수 설정:
```bash
export FIREWORKS_API_KEY="your-api-key"
```

```python
# ai_agent.py
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from simple_agent import SimpleAgent
from basic_schema import get_test_schema

class AIAgent(SimpleAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="accounts/ijzereen/deployedModels/qwen3-4b-l3nkg",
            api_key=Config.FIREWORKS_API_KEY,
            base_url="https://api.fireworks.ai/inference/v1",
            temperature=0.1
        )
        self.schema = get_test_schema()
    
    def ask(self, question: str) -> dict:
        """자연어 질문 → SQL → 실행"""
        try:
            sql = self._generate_sql(question)
            result = self.execute_sql(sql)
            return {"sql": sql, "result": result, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _generate_sql(self, question: str) -> str:
        schema_text = self.schema.generate_schema_text()
        
        prompt = f"""PostgreSQL 전문가입니다. 다음 스키마로 SQL을 생성하세요:

{schema_text}

규칙:
1. PostgreSQL 문법 사용
2. 결과 10개 제한 (LIMIT 10)
3. SQL만 반환 (설명 없이)

질문: {question}"""

        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        sql = response.content.strip()
        if sql.startswith("```"):
            sql = sql.split('\n', 1)[1]
        if sql.endswith("```"):
            sql = sql.rsplit('\n', 1)[0]
            
        return sql.strip()
```

### 구현 순서 요약

1. **환경 준비**: `pip install sqlalchemy psycopg2-binary langchain-openai langchain-community`
2. **파일 순서**: `config.py` → `test_connection.py` → `simple_agent.py` → `minimal_main.py` → `basic_schema.py` → `ai_agent.py`
3. **단계별 테스트**: 각 단계마다 실행해서 동작 확인
4. **핵심 확인**: PostgreSQL 연결 → 수동 SQL 실행 → 자연어 SQL 변환

이렇게 하면 **30분 안에** 핵심 기능이 동작합니다. 그 다음 필요하면 자동 스키마 검색 등 고급 기능을 추가하세요.

## 🎉 주요 기능

- ✅ PostgreSQL Docker 컨테이너 전용 설계
- ✅ 실시간 동적 스키마 검색
- ✅ 자연어 컬럼 특성 설명 시스템
- ✅ 자연어 SQL 변환 (AI 모델 연동)
- ✅ 간단하고 직관적인 CLI 인터페이스

더 이상 고정된 스키마 파일을 관리할 필요가 없으며, LLM이 데이터의 의미를 깊이 이해할 수 있습니다! 🎯 