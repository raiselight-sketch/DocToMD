import sys
from pathlib import Path

# src 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core import DocumentConverter

def test_txt_conversion():
    converter = DocumentConverter()
    
    # 텍스트 파일 생성
    test_input = Path("tests/samples/test.txt")
    test_input.parent.mkdir(parents=True, exist_ok=True)
    with open(test_input, "w", encoding="utf-8") as f:
        f.write("# Hello\nThis is a test file.")
    
    output_dir = Path("tests/output")
    result = converter.convert(test_input, output_dir)
    
    print(f"Input: {result.input_path}")
    print(f"Output: {result.output_path}")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error: {result.error_message}")
    
    assert result.success is True
    assert result.output_path.exists()
    
    with open(result.output_path, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"Content:\n{content}")

if __name__ == "__main__":
    try:
        test_txt_conversion()
        print("\n✅ Basic test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
