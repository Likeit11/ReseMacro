"""
Python 스크립트 로더 모듈

외부 Python 스크립트 파일을 동적으로 로드하고 실행
"""

import importlib.util
import os
from typing import Optional


class ScriptLoader:
    """Python 스크립트 파일을 로드하고 실행하는 클래스"""
    
    @staticmethod
    def load_script(script_path: str):
        """
        스크립트 파일 로드
        
        Args:
            script_path: 스크립트 파일 경로 (.py)
            
        Returns:
            module: 로드된 스크립트 모듈
            
        Raises:
            FileNotFoundError: 스크립트 파일이 없는 경우
            Exception: 스크립트 로드 실패 시
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"스크립트 파일을 찾을 수 없습니다: {script_path}")
        
        try:
            spec = importlib.util.spec_from_file_location("script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            raise Exception(f"스크립트 로드 실패: {str(e)}")
    
    @staticmethod
    def run_script(macro, script_path: str):
        """
        스크립트 실행
        
        Args:
            macro: BaseMacro 인스턴스
            script_path: 스크립트 파일 경로
            
        Raises:
            ValueError: 스크립트에 'run' 함수가 없는 경우
        """
        module = ScriptLoader.load_script(script_path)
        
        if hasattr(module, 'run'):
            module.run(macro)
        else:
            raise ValueError(f"스크립트에 'run' 함수가 없습니다: {script_path}")
