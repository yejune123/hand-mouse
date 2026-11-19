# 손인식 마우스 (Windows)

웹캠에서 손가락 위치를 인식해 Windows 마우스 커서를 움직이는 프로그램입니다. 엄지와 검지를 모아 클릭하고, 모은 채 세로로 움직여 스크롤할 수 있습니다. 영상은 PC에서 처리합니다.

## 한 줄 설치

Windows 터미널, 명령 프롬프트(CMD), PowerShell 중 어디서든 다음 명령을 실행합니다. 최신 릴리스 ZIP과 SHA-256 확인 파일을 내려받아 검사한 뒤 `%LOCALAPPDATA%\Programs\HandMouse`에 설치합니다. 설치가 끝나면 바탕화면에 `HandMouse` 바로가기를 만들고 앱을 자동 실행합니다.

```bat
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/yejune123/hand-mouse/main/install.ps1 | iex"
```

릴리스가 아직 생성되지 않았거나 저장소 주소가 다르면 설치할 수 없습니다. 출처를 확인한 다음 실행하세요. 기존 버전이 실행 중이라면 종료하고 다시 설치하세요.

## 사용 방법

1. Windows 카메라 사용 권한을 허용하고 프로그램에서 **카메라 시작**을 누릅니다.
2. 손을 카메라에 비춥니다.
3. 일시 중지는 기본적으로 **F8**입니다. 설정에서 변경할 수 있습니다.
4. 물리 마우스나 터치패드 입력을 감지해 제어를 일시 중지하는 옵션이 있습니다.

설정은 `%LOCALAPPDATA%\HandMouse\settings.json`에 저장됩니다. 설치 위치와 설정 위치는 다릅니다.

## 직접 빌드

Windows와 Python 3.12가 필요합니다. 공식 [MediaPipe Hand Landmarker 모델](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)을 `assets/hand_landmarker.task`로 저장한 후 SHA-256이 `FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1`인지 확인합니다.

```powershell
python -m unittest -v test_gesture
.\build.ps1 -Python python
```

결과는 `dist/HandMouse/HandMouse.exe`입니다. 같은 폴더의 모든 파일을 함께 보관해야 합니다. 릴리스 작업은 Windows에서 동일한 빌드를 수행하고 ZIP과 SHA-256 파일을 게시합니다.

Android 실험 버전은 별도 [안내](android/README.md)를 참고하세요. 공개 저장소에는 Windows 소스만 포함하며 Android APK를 설치 명령으로 배포하지 않습니다.

## 모델 및 배포

공개 저장소에는 모델 바이너리를 넣지 않습니다. 릴리스 빌드 시 Google의 공식 주소에서 내려받고 해시를 확인합니다. MediaPipe에 관한 정보는 [공식 저장소](https://github.com/google-ai-edge/mediapipe)를 참고하세요. 이 저장소의 소스에 대한 재사용 허가는 별도 라이선스 파일이 추가되기 전까지 부여되지 않습니다.


