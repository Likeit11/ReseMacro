import os
import subprocess
import shutil

def create_requirements():
    """프로젝트에 필요한 의존성 목록을 requirements.txt 파일로 생성합니다."""
    requirements = [
        'adb-shell',
        'Pillow',
        'opencv-python',
        'numpy',
        'customtkinter'
    ]
    
    # build.py가 Source 폴더 안에 있으므로, requirements.txt는 프로젝트 루트에 생성합니다.
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')

    with open(req_path, 'w') as f:
        for req in requirements:
            f.write(f"{req}\n")
    return req_path

def build_executable():
    """PyInstaller를 사용하여 프로젝트를 단일 실행 파일로 빌드합니다."""

    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root) # 작업 디렉토리를 프로젝트 루트로 변경
    
    print("1. requirements.txt 생성 중...")
    req_path = create_requirements()
    
    print("2. 필요한 패키지 설치 중...")
    try:
        subprocess.run(['pip', 'install', '-r', req_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"패키지 설치 중 오류 발생: {e}")
        return

    print("3. PyInstaller로 실행 파일 빌드 중...")

    # 빌드에 필요한 옵션 설정
    pyinstaller_options = [
        'pyinstaller',
        '--noconsole',          # GUI 앱이므로 콘솔 창을 띄우지 않음
        '--onefile',            # 단일 실행 파일로 생성
        '--name', 'ReseMaraGUI', # 출력될 파일의 이름
        f'--add-data', f'Ref_Img{os.pathsep}Ref_Img', # Ref_Img 폴더를 리소스로 추가
        os.path.join('Source', 'gui.py') # 메인 스크립트 경로
    ]
    
    try:
        subprocess.run(pyinstaller_options, check=True)
        print("\n" + "="*30)
        print("    빌드 완료!    ")
        print("="*30)
        print(f"생성된 실행 파일 위치: {os.path.join(project_root, 'dist', 'ReseMaraGUI.exe')}")
    except FileNotFoundError:
         print("\n오류: 'pyinstaller'를 찾을 수 없습니다.")
         print("PyInstaller가 설치되어 있는지 확인하세요: pip install pyinstaller")
    except subprocess.CalledProcessError as e:
        print(f"빌드 중 오류 발생: {e}")

if __name__ == "__main__":
    build_executable()