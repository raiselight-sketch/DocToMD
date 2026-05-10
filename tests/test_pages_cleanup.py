"""_cleanup.py 단위 테스트 및 골든 비교 테스트."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.handlers._cleanup import (
    cleanup_pages_markdown,
    collapse_blank_lines,
    merge_korean_linebreaks,
    promote_headings,
    strip_board_meta,
    strip_print_header,
)


# ── A) strip_print_header ──────────────────────────────────────

def test_strip_print_header_full():
    assert strip_print_header("인쇄하기\n\n인쇄\n\n본문") == "본문"


def test_strip_print_header_single():
    assert strip_print_header("인쇄\n\n본문") == "본문"


def test_strip_print_header_preserves_body():
    text = "본문에 인쇄라는 단어가 있다"
    assert strip_print_header(text) == text


# ── B) strip_board_meta ─────────────────────────────────────────

def test_strip_board_meta():
    raw = "박광일  | 조회 0  | 2023/11/21 17:42:27\n실제내용"
    assert strip_board_meta(raw).strip() == "실제내용"


def test_strip_board_meta_no_match():
    text = "일반 텍스트 | 구분자가 있어도"
    assert strip_board_meta(text) == text


# ── C) merge_korean_linebreaks ──────────────────────────────────

def test_merge_midword_break():
    assert merge_korean_linebreaks("한국은 라\n\n면시장에") == "한국은 라 면시장에"


def test_merge_preserves_sentence_end():
    text = "문장 끝.\n\n다음 단락"
    assert merge_korean_linebreaks(text) == text


def test_merge_direct_linebreak():
    assert merge_korean_linebreaks("이것은 중요하\n다고 말했다") == "이것은 중요하 다고 말했다"


def test_merge_two_blanks_keeps_paragraph():
    text = "첫 문단\n\n\n둘째 문단"
    assert merge_korean_linebreaks(text) == text


# ── D) collapse_blank_lines ─────────────────────────────────────

def test_collapse_three_blanks():
    assert collapse_blank_lines("가\n\n\n나") == "가\n\n나"


def test_collapse_preserves_double():
    text = "가\n\n나"
    assert collapse_blank_lines(text) == text


# ── E) promote_headings ─────────────────────────────────────────

def test_promote_dot_heading():
    assert promote_headings("1. 캐스팅") == "## 1. 캐스팅"


def test_promote_paren_heading():
    assert promote_headings("1) 대본을 읽어라!") == "### 1) 대본을 읽어라!"


def test_promote_skip_existing_heading():
    text = "## 이미 헤딩"
    assert promote_headings(text) == text


def test_promote_skip_long_line():
    long_text = "1. " + "가" * 82
    assert promote_headings(long_text) == long_text


# ── 통합 cleanup_pages_markdown ─────────────────────────────────

def test_cleanup_integration():
    raw = "인쇄하기\n\n인쇄\n\n1. 제목\n\n본문이다"
    result = cleanup_pages_markdown(raw)
    assert result.startswith("## 1. 제목")
    assert "인쇄" not in result


# ── 골든 비교 테스트 ─────────────────────────────────────────────

def test_golden_sample():
    samples = Path(__file__).parent / 'samples'
    raw = (samples / 'pages_sample_raw.md').read_text(encoding='utf-8')
    expected = (samples / 'pages_sample_clean.md').read_text(encoding='utf-8')
    result = cleanup_pages_markdown(raw)
    assert result.strip() == expected.strip()
