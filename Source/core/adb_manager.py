"""
ADB 연결 및 제어 모듈

AdbDeviceTcp를 사용한 안드로이드 디바이스 연결 및 제어 기능을 제공
"""

import re
from adb_shell.adb_device import AdbDeviceTcp
from typing import Optional


class ADBManager:
    """ADB 연결 및 제어를 관리하는 클래스"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 16384):
        """
        ADB 연결 초기화
        
        Args:
            host (str): ADB 호스트 주소 (기본값: '127.0.0.1')
            port (int): ADB 포트 번호
        """
        self.host = host
        self.port = port
        self.device = AdbDeviceTcp(host, port)
        self._connected = False
    
    def connect(self):
        """
        ADB 디바이스에 연결
        
        Raises:
            Exception: 연결 실패 시
        """
        try:
            self.device.connect()
            self._connected = True
        except Exception as e:
            raise Exception(f"ADB 연결 실패: {str(e)}")
    
    def close(self):
        """ADB 연결 종료"""
        try:
            if self._connected:
                self.device.close()
                self._connected = False
        except Exception as e:
            print(f"ADB 연결 종료 중 오류 발생: {str(e)}")
    
    def is_connected(self) -> bool:
        """
        연결 상태 확인
        
        Returns:
            bool: 연결 여부
        """
        return self._connected
    
    def shell(self, command: str, decode: bool = True):
        """
        ADB shell 명령 실행
        
        Args:
            command (str): 실행할 shell 명령
            decode (bool): 결과를 문자열로 디코딩 여부 (기본값: True)
            
        Returns:
            shell 명령 실행 결과
            
        Raises:
            Exception: 명령 실행 실패 시
        """
        if not self._connected:
            raise Exception("ADB가 연결되지 않았습니다")
        
        return self.device.shell(command, decode=decode)
    
    def tap(self, x: int, y: int) -> bool:
        """
        화면의 특정 좌표 터치
        
        Args:
            x (int): x 좌표
            y (int): y 좌표
            
        Returns:
            bool: 성공 여부
        """
        try:
            self.shell(f'input tap {x} {y}')
            return True
        except Exception as e:
            print(f"좌표 클릭 중 오류 발생: {str(e)}")
            return False
    
    def input_text(self, text: str) -> bool:
        """
        텍스트 입력
        
        Args:
            text (str): 입력할 텍스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            self.shell(f'input text {text}')
            return True
        except Exception as e:
            print(f"텍스트 입력 중 오류 발생: {str(e)}")
            return False
    
    def get_current_package(self) -> Optional[str]:
        """
        현재 포커스된 앱의 패키지 이름 가져오기
        
        Returns:
            Optional[str]: 패키지 이름 (찾지 못한 경우 None)
        """
        try:
            result = self.shell('dumpsys window | grep mCurrentFocus')
            
            if result:
                match = re.search(r'{\w+\s+\w+\s+(\S+)}', result)
                if match:
                    package_name = match.group(1).split('/')[0]
                    return package_name
            
            return None
        except Exception as e:
            print(f"패키지 이름 확인 중 오류 발생: {str(e)}")
            return None
    
    def force_stop_app(self, package_name: Optional[str] = None) -> bool:
        """
        앱 강제 종료
        
        Args:
            package_name (Optional[str]): 종료할 패키지 이름 (None이면 현재 앱)
            
        Returns:
            bool: 성공 여부
        """
        try:
            if package_name is None:
                package_name = self.get_current_package()
            
            if package_name:
                self.shell(f'am force-stop {package_name}')
                return True
            else:
                print("종료할 앱을 찾을 수 없습니다")
                return False
        except Exception as e:
            print(f"앱 종료 중 오류 발생: {str(e)}")
            return False
    
    def capture_screen_raw(self):
        """
        화면 캡처 (원시 데이터)
        
        Returns:
            bytes: 화면 캡처 데이터 (PNG 형식)
        """
        return self.shell('screencap -p', decode=False)
