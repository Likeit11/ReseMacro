"""
ReseMacro 메인 진입점

CLI를 통해 매크로를 실행하거나 스크립트를 로드하여 실행
"""

import sys
import os
import argparse
import atexit
import signal

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import Settings
from core.adb_manager import ADBManager
from macro.base_macro import BaseMacro
from macro.game_macro import GameMacro
from macro.script_loader import ScriptLoader
from utils.logger import get_logger, setup_logger
from utils.file_manager import FileManager

# 로거 초기화
logger = get_logger()

# 전역 변수
macro = None
port_log_file = Settings.PORT_LOG_FILE


def cleanup():
    """프로그램 종료 시 실행될 정리 함수"""
    if hasattr(cleanup, 'is_running'):
        return
    cleanup.is_running = True
    
    logger.debug("정리 작업 시작")
    try:
        if macro is not None:
            # ADB 연결 종료
            macro.adb.close()
            
            # 포트 로그에서 현재 포트 제거
            if os.path.exists(port_log_file):
                FileManager.remove_port_from_log(port_log_file, macro.adb.port)
    except Exception as e:
        logger.error(f"정리 작업 중 오류 발생: {str(e)}")
    
    logger.debug("프로그램 종료")


def signal_handler(signum, frame):
    """시그널 핸들러"""
    logger.debug("시그널 핸들러 호출됨")
    cleanup()
    sys.exit(0)


def connect_adb(ports_to_try):
    """
    ADB 연결 시도
    
    Args:
        ports_to_try: 시도할 포트 리스트
        
    Returns:
        ADBManager: 연결된 ADB 매니저 또는 None
    """
    for port in ports_to_try:
        try:
            logger.debug(f"포트 {port}로 연결 시도 중...")
            adb = ADBManager(port=port)
            adb.connect()
            logger.info(f"포트 {port}로 연결 성공!")
            
            # 성공한 포트 번호를 파일에 추가
            FileManager.write_port_log(port_log_file, port)
            return adb
        except Exception as e:
            logger.debug(f"포트 {port} 연결 실패: {str(e)}")
            continue
    
    return None


def main():
    """메인 함수"""
    global macro
    
    logger.debug("프로그램 시작")
    
    # 종료 시 cleanup 함수 등록
    atexit.register(cleanup)
    
    # Ctrl+C 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    
    # CLI 파서 설정
    parser = argparse.ArgumentParser(description='ReseMacro - 게임 매크로 자동화 도구')
    parser.add_argument('--port', type=int, help='ADB 포트 번호 (자동 검색은 생략)')
    parser.add_argument('--script', type=str, help='실행할 스크립트 파일 경로 (.py)')
    
    args = parser.parse_args()
    
    # 필요한 디렉토리 생성
    FileManager.ensure_directories(Settings.get_required_directories())
    
    # 포트 결정
    if args.port:
        ports_to_try = [args.port]
    else:
        # 포트 자동 검색
        used_ports = FileManager.read_port_log(port_log_file)
        ports_to_try = [p for p in Settings.MUMU_PORTS if p not in used_ports]
        
        if not ports_to_try:
            logger.info("사용 가능한 포트가 없습니다. 모든 포트를 다시 시도합니다.")
            ports_to_try = Settings.MUMU_PORTS
    
    # ADB 연결
    adb = connect_adb(ports_to_try)
    
    if adb is None:
        logger.error("사용 가능한 ADB 포트를 찾지 못했습니다.")
        return 1
    
    # 매크로 인스턴스 생성
    if args.script:
        # 스크립트 모드
        macro = BaseMacro(adb)
        logger.info(f"스크립트 실행: {args.script}")
        
        try:
            ScriptLoader.run_script(macro, args.script)
            logger.info("스크립트 실행 완료")
        except Exception as e:
            logger.error(f"스크립트 실행 실패: {str(e)}")
            return 1
    else:
        # 기본 게임 매크로 모드
        macro = GameMacro(adb)
        logger.info("연결 테스트가 완료되었습니다.")
        logger.info("매크로를 시작합니다.")
        
        try:
            macro.run_macro()
            logger.info("매크로가 완료되었습니다.")
        except KeyboardInterrupt:
            logger.info("\n사용자가 프로그램을 중단했습니다.")
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
