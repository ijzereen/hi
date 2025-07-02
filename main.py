#!/usr/bin/env python3
"""
PostgreSQL SQL Agent
PostgreSQL Docker 컨테이너의 스키마를 동적으로 검색하여 자연어 쿼리를 SQL로 변환하는 시스템
"""

import argparse
import logging
import sys

from config import Config
from sql_agent import create_sql_agent
from schema_inspector import auto_detect_schema, export_current_schema


def setup_logging(verbose: bool = False):
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def show_info():
    """데이터베이스 정보 출력"""
    try:
        agent = create_sql_agent(auto_detect=False)
        info = Config.get_connection_info()
        
        print(f"\n=== PostgreSQL 데이터베이스 정보 ===")
        print(f"호스트: {info['host']}:{info['port']}")
        print(f"데이터베이스: {info['database']}")
        print(f"연결: ✅ 성공, 테이블 수: {len(agent.list_tables())}")
        
    except Exception as e:
        print(f"연결: ❌ 실패 - {e}")


def scan_schema():
    """스키마 검색 및 출력"""
    try:
        print("PostgreSQL 스키마 검색 중...")
        schema = auto_detect_schema()
        
        print(f"\n=== 검색된 스키마 ({len(schema.tables)}개 테이블) ===")
        for table_name, table in schema.tables.items():
            print(f"📋 {table_name}: {len(table.columns)}개 컬럼")
            if hasattr(table, 'sample_data') and table.sample_data:
                print(f"   샘플 데이터: {len(table.sample_data)}건")
                
    except Exception as e:
        print(f"스키마 검색 실패: {e}")


def run_interactive():
    """대화형 모드"""
    print("🔍 PostgreSQL SQL Agent - 대화형 모드")
    print("명령어: 'quit' (종료), 'schema' (스키마), 'tables' (테이블 목록)")
    print("-" * 50)
    
    try:
        agent = create_sql_agent()
        print(f"✅ 연결 성공! {len(agent.list_tables())}개 테이블")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    while True:
        try:
            question = input("\n🤔 질문: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 종료합니다.")
                break
            elif question.lower() in ['schema']:
                print(agent.schema_text)
                continue
            elif question.lower() in ['tables']:
                tables = agent.list_tables()
                print(f"📋 테이블 목록: {', '.join(tables)}")
                continue
            
            # 자연어 쿼리 처리
            print("🔍 처리 중...")
            result = agent.ask(question)
            
            if result['success']:
                print(f"\n📝 SQL: {result['sql']}")
                print(f"📊 결과:\n{result['result']}")
            else:
                print(f"❌ 오류: {result['result']}")
                
        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="PostgreSQL SQL Agent")
    parser.add_argument("--query", "-q", help="자연어 질문")
    parser.add_argument("--info", action="store_true", help="DB 정보 확인")
    parser.add_argument("--scan", action="store_true", help="스키마 검색")
    parser.add_argument("--export", help="스키마 내보내기 (파일명)")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그")
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    try:
        if args.info:
            show_info()
        elif args.scan:
            scan_schema()
        elif args.export:
            schema = export_current_schema(args.export)
            print(f"✅ 스키마를 {args.export}에 저장했습니다.")
        elif args.query:
            agent = create_sql_agent()
            result = agent.ask(args.query)
            if result['success']:
                print(f"SQL: {result['sql']}")
                print(f"결과:\n{result['result']}")
            else:
                print(f"오류: {result['result']}")
        else:
            run_interactive()
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 