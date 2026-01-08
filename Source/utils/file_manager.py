"""
파일 관리 유틸리티 모듈

폴더 생성, 스크린샷 관리, 포트 로그 파일 관리 등을 담당
"""

import os
from typing import List


class FileManager:
    """파일 및 폴더 관리를 위한 클래스"""
    
    @staticmethod
    def ensure_directories(directories: List[str]):
        """
        필요한 디렉토리들이 존재하는지 확인하고, 없으면 생성
        
        Args:
            directories (List[str]): 생성할 디렉토리 경로 리스트
        """
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    @staticmethod
    def manage_old_files(directory: str, max_files: int = 30, extension: str = '.png'):
        """
        디렉토리 내의 파일 개수를 관리하고, 초과하는 경우 가장 오래된 파일부터 삭제
        
        Args:
            directory (str): 관리할 디렉토리 경로
            max_files (int): 유지할 최대 파일 개수 (기본값: 30)
            extension (str): 관리할 파일 확장자 (기본값: '.png')
        """
        try:
            # 디렉토리의 모든 파일 목록 가져오기
            files = [f for f in os.listdir(directory) if f.endswith(extension)]
            
            # 파일 개수가 max_files 초과하는 경우
            if len(files) > max_files:
                # 파일을 생성 시간 순으로 정렬
                files.sort(key=lambda x: os.path.getctime(os.path.join(directory, x)))
                
                # 초과하는 만큼 오래된 파일부터 삭제
                for f in files[:len(files) - max_files]:
                    file_path = os.path.join(directory, f)
                    os.remove(file_path)
        except Exception as e:
            # 에러 발생 시 로깅 (logger 사용 시)
            print(f"파일 관리 중 오류 발생: {str(e)}")
    
    @staticmethod
    def read_port_log(log_file: str) -> List[int]:
        """
        포트 로그 파일을 읽어서 포트 번호 리스트 반환
        
        Args:
            log_file (str): 포트 로그 파일 경로
            
        Returns:
            List[int]: 포트 번호 리스트
        """
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r') as f:
                ports = [int(port.strip()) for port in f.readlines() if port.strip()]
            return ports
        except Exception as e:
            print(f"포트 로그 파일 읽기 실패: {str(e)}")
            return []
    
    @staticmethod
    def write_port_log(log_file: str, port: int):
        """
        포트 번호를 로그 파일에 추가
        
        Args:
            log_file (str): 포트 로그 파일 경로
            port (int): 추가할 포트 번호
        """
        try:
            with open(log_file, 'a') as f:
                f.write(f"{port}\n")
        except Exception as e:
            print(f"포트 로그 파일 쓰기 실패: {str(e)}")
    
    @staticmethod
    def remove_port_from_log(log_file: str, port: int):
        """
        포트 로그 파일에서 특정 포트 번호 제거
        
        Args:
            log_file (str): 포트 로그 파일 경로
            port (int): 제거할 포트 번호
        """
        if not os.path.exists(log_file):
            return
        
        try:
            # 파일의 모든 포트 번호 읽기
            with open(log_file, 'r') as f:
                ports = f.readlines()
            
            # 현재 포트 번호를 제외한 나머지 포트들만 유지
            remaining_ports = [p.strip() for p in ports if p.strip() != str(port)]
            
            if remaining_ports:
                # 남은 포트들이 있으면 파일 업데이트
                with open(log_file, 'w') as f:
                    f.write('\n'.join(remaining_ports) + '\n')
            else:
                # 남은 포트가 없으면 파일 삭제
                os.remove(log_file)
        except Exception as e:
            print(f"포트 로그 파일 처리 중 오류 발생: {str(e)}")
