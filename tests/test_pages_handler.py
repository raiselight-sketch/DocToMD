import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# src 경로 추가
sys.path.append(str(Path("/Users/raiselight/doctomd/src")))

from core.handlers.pages_handler import PagesHandler, _find_apple_pages_app

def test_pages_app_validation():
    print("Testing Pages app validation...")
    
    # 1. 정식 Pages가 없는 경우 (서드파티 앱만 있는 경우)
    with patch("subprocess.run") as mock_run:
        # mdfind 결과: 서드파티 앱 경로 반환
        mock_run.side_effect = [
            MagicMock(stdout="/Applications/Pages Creator Studio.app\n", stderr="", returncode=0), # mdfind
            MagicMock(stdout="Identifier=com.apple.Pages\nAuthority=Apple Mac OS Application Signing\nTeamIdentifier=JCRTNEU7GK\n", stderr="", returncode=0) # codesign
        ]
        
        with patch("pathlib.Path.exists", return_value=True):
            result = _find_apple_pages_app()
            print(f"Test 1 (Third-party app only): Expected None, Got {result}")
            assert result is None

    # 2. 정식 Pages가 있는 경우
    with patch("subprocess.run") as mock_run:
        # mdfind 결과: 정식 앱 경로 반환
        mock_run.side_effect = [
            MagicMock(stdout="/Applications/Pages.app\n", stderr="", returncode=0), # mdfind
            MagicMock(stdout="Identifier=com.apple.iWork.Pages\nAuthority=Software Signing\nTeamIdentifier=K36BKF7T3D\n", stderr="", returncode=0), # codesign (1st candidate)
            MagicMock(stdout="Identifier=com.apple.iWork.Pages\nAuthority=Software Signing\nTeamIdentifier=K36BKF7T3D\n", stderr="", returncode=0)  # codesign (2nd candidate)
        ]
        
        with patch("pathlib.Path.exists", return_value=True):
            result = _find_apple_pages_app()
            print(f"Test 2 (Apple Pages app): Expected one of official paths, Got {result}")
            assert result in [Path("/Applications/Pages.app"), Path("/System/Applications/Pages.app")]

    # 3. convert() 메서드 호출 시 앱 미존재 처리
    handler = PagesHandler()
    with patch("core.handlers.pages_handler._find_apple_pages_app", return_value=None):
        result = handler.convert(Path("test.pages"), Path("output"))
        print(f"Test 3 (convert with no app): Expected success=False, Got success={result.success}")
        print(f"Error Message: {result.error_message}")
        assert result.success is False
        assert "Apple Pages가 설치되어 있지 않거나" in result.error_message

if __name__ == "__main__":
    try:
        test_pages_app_validation()
        print("\n✅ Pages validation tests passed!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)
