"""
로깅 유틸리티 모듈

ReseMara.py의 setup_logger() 함수를 분리한 모듈
"""

import logging


def setup_logger(name='ReseMara', log_file='ReseMara.log', level=logging.DEBUG):
    """
    로거를 설정하고 반환하는 함수
    
    Args:
        name (str): 로거 이름 (기본값: 'ReseMara')
        log_file (str): 로그 파일 경로 (기본값: 'ReseMara.log')
        level (int): 로깅 레벨 (기본값: logging.DEBUG)
        
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 싱글톤 로거 인스턴스
_logger = None


def get_logger():
    """
    싱글톤 로거 인스턴스를 반환
    
    Returns:
        logging.Logger: 로거 인스턴스
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger
