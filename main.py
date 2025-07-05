#!/usr/bin/env python3
"""
Simple PostgreSQL SQL Agent
고정 테이블에서 한 컬럼만 SELECT하고 WHERE절만 자연어로 생성하는 간소화된 시스템
"""

import logging
import sys

from simple_agent import create_simple_agent

# 모듈 로거
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def run_interactive():
    """대화형 모드"""
    logger.info("🎯 Simple SQL Agent - 대화형 모드")
    logger.info("명령어: 'quit' (종료)")
    logger.info("-" * 60)
    
    try:
        agent = create_simple_agent()
        logger.info(f"✅ 연결 성공! 테이블: {agent.target_table}")
        logger.info(f"사용 가능한 컬럼: {', '.join(agent.list_columns())}")
    except Exception as e:
        logger.error(f"❌ 초기화 실패: {e}")
        return
    
    while True:
        try:
            user_input = input("\n🤔 질문: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                logger.info("👋 종료합니다.")
                break
            
            # 자연어 쿼리 처리
            logger.info(f"🔍 질문 분석 중...")
            result = agent.ask(user_input)
            
            if result['success']:
                logger.info(f"📝 생성된 SQL: {result['sql']}")
                vals = result.get('result', [])
                col = result.get('target_column', 'value')
                if vals:
                    logger.info(f"✅ 발견된 {col.upper()} 값: {', '.join(map(str, vals))}")
                else:
                    logger.info("✅ 조건에 맞는 데이터를 찾지 못했습니다.")
            else:
                logger.error(f"❌ 오류: {result.get('error', '알 수 없는 오류')}")
                
        except KeyboardInterrupt:
            logger.info("\n👋 종료합니다.")
            break
        except Exception as e:
            logger.error(f"❌ 오류: {e}")


def main():
    """메인 함수"""
    setup_logging()
    try:
        run_interactive()
            
    except Exception as e:
        logger.error(f"❌ 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 