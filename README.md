# PostgreSQL SQL Agent

PostgreSQL Docker 컨테이너의 스키마를 **동적으로 검색**하여 자연어 쿼리를 SQL로 변환하는 시스템입니다.

## 🎯 핵심 기능

- **동적 스키마 검색**: PostgreSQL 컨테이너에 연결하여 실시간으로 테이블 구조 분석
- **자연어 SQL 변환**: AI를 활용한 자연어 쿼리 → SQL 자동 변환
- **자연어 컬럼 설명**: 각 컬럼의 특성과 비즈니스 의미를 자연어로 설명
- **샘플 데이터 수집**: 각 테이블의 샘플 데이터 자동 수집 및 컨텍스트 제공

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate

# PostgreSQL Docker 컨테이너 실행
docker-compose up -d
```

### 2. 환경변수 설정 (선택사항)

`.env` 파일 생성:
```bash
# PostgreSQL 설정 (기본값 사용 가능)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

# AI 모델 설정 (자연어 쿼리용)
FIREWORKS_API_KEY=your-api-key-here
```

## 📖 사용법

### 기본 명령어

```bash
# 데이터베이스 연결 정보 확인
python main.py --info

# 스키마 자동 검색 및 출력
python main.py --scan

# 스키마를 Python 코드로 내보내기
python main.py --export backup_schema.py

# 일회성 자연어 쿼리
python main.py --query "organizations 테이블의 모든 데이터를 보여주세요"

# 대화형 모드 (기본값)
python main.py
```

### 대화형 모드 명령어

- `schema` - 전체 데이터베이스 스키마 출력
- `tables` - 테이블 목록 출력
- `quit` / `exit` / `q` - 종료

### 예시 자연어 쿼리

```
🤔 질문: organizations 테이블에 몇 개의 레코드가 있나요?
🤔 질문: Downtown 지역의 조직을 모두 보여주세요
🤔 질문: Tech Innovators라는 이름을 가진 조직의 위치를 알려주세요
```

## 🔧 시스템 구조

### 핵심 컴포넌트

1. **main.py** - 메인 실행 파일 및 CLI 인터페이스
2. **schema_inspector.py** - PostgreSQL 동적 스키마 검색
3. **sql_agent.py** - AI 기반 자연어 → SQL 변환
4. **schema.py** - 스키마 정의 (자연어 설명 지원)
5. **config.py** - 설정 관리

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

## 📊 현재 데이터베이스 구조

자동 검색된 `organizations` 테이블:

| 컬럼명 | 타입 | 설명 | 특성 |
|--------|------|------|------|
| id | INTEGER (PK) | 조직 고유 식별자 | 시스템 자동 생성 |
| name | VARCHAR(100) | 조직 이름 | - |
| region | VARCHAR(50) | 조직 활동 지역 | - |
| members_count | INTEGER | 조직 구성원 수 | 조직 평가 기준 |
| status | VARCHAR(20) | 조직 상태 | active/inactive/disbanded |
| x_coord | DOUBLE | X 좌표 (경도) | GPS 좌표 |
| y_coord | DOUBLE | Y 좌표 (위도) | GPS 좌표 |

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

## 📁 파일 구조

```
project/
├── main.py              # 메인 실행 파일 및 CLI
├── config.py            # 설정 관리
├── schema.py            # 스키마 정의 (자연어 설명 지원)
├── schema_inspector.py  # 동적 스키마 검색
├── sql_agent.py         # SQL 에이전트
├── docker-compose.yml   # PostgreSQL 컨테이너
├── requirements.txt     # Python 의존성
└── README.md           # 이 파일
```

## 🎉 주요 기능

- ✅ PostgreSQL Docker 컨테이너 전용 설계
- ✅ 실시간 동적 스키마 검색
- ✅ 자연어 컬럼 특성 설명 시스템
- ✅ 자연어 SQL 변환 (AI 모델 연동)
- ✅ 간단하고 직관적인 CLI 인터페이스

더 이상 고정된 스키마 파일을 관리할 필요가 없으며, LLM이 데이터의 의미를 깊이 이해할 수 있습니다! 🎯 