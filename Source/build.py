import os
import subprocess

def create_requirements():
    requirements = [
        'adb-shell',
        'pillow',  # PIL용
        'opencv-python',  # cv2용
        'numpy',  # np용
        'pyinstaller',  # 빌드용
        'python-dateutil',  # datetime 확장
    ]
    
    with open('requirements.txt', 'w') as f:
        for req in requirements:
            f.write(f"{req}\n")

def build_exe():
    print("requirements.txt 생성 중...")
    create_requirements()
    
    print("필요한 패키지 설치 중...")
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
    
    print("exe 파일 생성 중...")
    subprocess.run([
        'pyinstaller',
        '--onefile',  # 단일 exe 파일로 생성
        '--name', 'ReseMara',  # 출력 파일 이름
        'ReseMara.py'
    ])
    
    print("빌드 완료!")
    print("생성된 exe 파일 위치: dist/ReseMara.exe")

if __name__ == "__main__":
    build_exe() 