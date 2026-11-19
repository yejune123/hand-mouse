# ���ν� ���콺 (Windows)

��ķ���� �հ��� ��ġ�� �ν��� Windows ���콺 Ŀ���� �����̴� ���α׷��Դϴ�. ������ ������ ��� Ŭ���ϰ�, ���� ä ���η� ������ ��ũ���� �� �ֽ��ϴ�. ������ PC���� ó���մϴ�.

## �� �� ��ġ

Windows PowerShell���� ���� ������ �����մϴ�. �ֽ� ������ ZIP�� SHA-256 Ȯ�� ������ �����޾� �˻��� �� ����� ��ġ ������ ��ġ�ϰ� �����մϴ�.

```powershell
irm https://raw.githubusercontent.com/yejune123/hand-mouse/main/install.ps1 | iex
```

�������� ���� �������� �ʾҰų� ����� �ּҰ� �ٸ��� ��ġ�� �� �����ϴ�. ��ó�� Ȯ���� ���� �����ϼ���. ���� ������ ���� ���̶�� �����ϰ� �ٽ� ��ġ�ϼ���.

## ��� ���

1. Windows ī�޶� ��� ������ ����ϰ� ���α׷����� **ī�޶� ����**�� �����ϴ�.
2. ���� ī�޶� ����ϴ�.
3. �Ͻ� ������ �⺻������ **F8**�Դϴ�. �������� ������ �� �ֽ��ϴ�.
4. ���� ���콺�� ��ġ�е� �Է��� ������ ��� �Ͻ� �����ϴ� �ɼ��� �ֽ��ϴ�.

������ `%LOCALAPPDATA%\HandMouse\settings.json`�� ����˴ϴ�. ��ġ ��ġ�� ���� ��ġ�� �ٸ��ϴ�.

## ���� ����

Windows�� Python 3.12�� �ʿ��մϴ�. ���� [MediaPipe Hand Landmarker ��](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)�� `assets/hand_landmarker.task`�� ������ �� SHA-256�� `FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1`���� Ȯ���մϴ�.

```powershell
python -m unittest -v test_gesture
.\build.ps1 -Python python
```

����� `dist/HandMouse/HandMouse.exe`�Դϴ�. ���� ������ ��� ������ �Բ� �����ؾ� �մϴ�. ������ �۾��� Windows���� ������ ���带 �����ϰ� ZIP�� SHA-256 ������ �Խ��մϴ�.

Android ���� ������ ���� [�ȳ�](android/README.md)�� �����ϼ���. ���� ����ҿ��� Windows �ҽ��� �����ϸ� Android APK�� ��ġ �������� �������� �ʽ��ϴ�.

## �� �� ����

���� ����ҿ��� �� ���̳ʸ��� ���� �ʽ��ϴ�. ������ ���� �� Google�� ���� �ּҿ��� �����ް� �ؽø� Ȯ���մϴ�. MediaPipe�� ���� ������ [���� �����](https://github.com/google-ai-edge/mediapipe)�� �����ϼ���. �� ������� �ҽ��� ���� ���� �㰡�� ���� ���̼��� ������ �߰��Ǳ� ������ �ο����� �ʽ��ϴ�.

