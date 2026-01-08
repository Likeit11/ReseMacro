"""
설정 관리 모듈

하드코딩된 값들을 중앙 집중식으로 관리
"""

import os


class Settings:
    """ReseMacro 설정 클래스"""
    
    # ADB 포트 설정
    MUMU_PORTS = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
    
    # 타임아웃 설정 (초)
    DEFAULT_WAIT_TIME = 1
    IMAGE_FIND_TIMEOUT = 30
    IMAGE_WAIT_TIMEOUT = 20
    
    # 이미지 매칭 임계값
    DEFAULT_THRESHOLD = 0.75
    COMPARE_THRESHOLD = 0.7
    
    # 파일 경로
    LOG_FILE = 'ReseMara.log'
    PORT_LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "port.log")
    
    # 디렉토리 경로
    ROW_SCREEN_DIR = 'Row_Screen'
    REF_IMG_DIR = 'Ref_Img'
    ACCOUNTS_DIR = 'Accounts'
    SCRIPTS_DIR = 'scripts'
    
    # 스크린샷 관리
    MAX_SCREENSHOTS = 30
    
    @classmethod
    def get_required_directories(cls):
        """
        프로그램 실행에 필요한 디렉토리 리스트 반환
        
        Returns:
            list: 필요한 디렉토리 경로 리스트
        """
        return [
            cls.ROW_SCREEN_DIR,
            cls.REF_IMG_DIR,
            cls.ACCOUNTS_DIR
        ]
