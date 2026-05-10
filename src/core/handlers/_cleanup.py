"""Pages → Markdown 변환 결과의 공통 결함을 정리하는 후처리기."""
import re


def strip_print_header(text: str) -> str:
    """파일 선두의 인쇄 페이지 흔적을 제거한다."""
    return re.sub(r'^\s*(?:인쇄하기\s*\n+\s*인쇄|인쇄)\s*\n+', '', text)


def strip_board_meta(text: str) -> str:
    """게시판 메타 라인(작성자|조회|날짜)을 삭제한다."""
    pattern = re.compile(
        r'^\s*[^\n|]{1,40}\s*\|\s*조회\s*\d+\s*\|\s*'
        r'\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}:\d{2}\s*$',
        re.MULTILINE,
    )
    return pattern.sub('', text)


def merge_korean_linebreaks(text: str) -> str:
    """Pages 텍스트박스의 강제 줄바꿈으로 끊긴 한국어 문장을 합친다."""
    _ENDINGS = set('.!?」』"\'…')
    _HEADING_RE = re.compile(r'^\s*#{1,6}\s')
    _HANGUL_RE = re.compile(r'[\uAC00-\uD7A3]')

    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 빈 줄이면 peek: 빈 줄 1개 + 다음 라인이 합칠 후보인지 확인
        if line.strip() == '':
            # 빈 줄 1개만 있는지 확인 (2개 이상이면 단락 경계)
            blank_count = 0
            j = i
            while j < len(lines) and lines[j].strip() == '':
                blank_count += 1
                j += 1

            if blank_count == 1 and len(result) > 0 and j < len(lines):
                prev = result[-1]
                next_line = lines[j]
                if _should_merge(prev, next_line, _ENDINGS, _HEADING_RE, _HANGUL_RE):
                    result[-1] = prev + ' ' + next_line.lstrip()
                    i = j + 1
                    continue

            # 합치지 않으면 빈 줄 그대로 출력
            result.append(line)
            i += 1
            continue

        # 현재 줄이 내용이 있는 줄
        if len(result) > 0 and result[-1].strip() != '':
            prev = result[-1]
            if _should_merge(prev, line, _ENDINGS, _HEADING_RE, _HANGUL_RE):
                result[-1] = prev + ' ' + line.lstrip()
                i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def _should_merge(prev: str, next_line: str, endings, heading_re, hangul_re) -> bool:
    """두 줄을 합칠 조건을 판단한다."""
    _NUMBERED_RE = re.compile(r'^\s*\d+[.)]\s+\S')  # 번호 소제목 패턴
    if not prev.strip() or not next_line.strip():
        return False
    if heading_re.match(prev) or heading_re.match(next_line):
        return False
    if _NUMBERED_RE.match(prev) or _NUMBERED_RE.match(next_line):
        return False


    last_char = prev.rstrip()[-1] if prev.rstrip() else ''
    first_nonws = next_line.lstrip()[0] if next_line.lstrip() else ''

    if not hangul_re.match(last_char):
        return False
    if not hangul_re.match(first_nonws):
        return False
    if last_char in endings:
        return False

    return True


def collapse_blank_lines(text: str) -> str:
    """연속된 빈 줄 3개 이상을 2개로 축소한다."""
    return re.sub(r'\n{3,}', '\n\n', text)


def promote_headings(text: str) -> str:
    """번호 매긴 소제목을 마크다운 헤딩으로 승격한다."""
    dot_re = re.compile(r'^(\s*)(\d+)\.\s+(\S.{0,80})$')
    paren_re = re.compile(r'^(\s*)(\d+)\)\s+(\S.{0,80})$')

    lines = text.split('\n')
    result = []
    for line in lines:
        if line.lstrip().startswith('#'):
            result.append(line)
            continue

        m = dot_re.match(line)
        if m:
            result.append(f'## {m.group(2)}. {m.group(3)}')
            continue

        m = paren_re.match(line)
        if m:
            result.append(f'### {m.group(2)}) {m.group(3)}')
            continue

        result.append(line)

    return '\n'.join(result)


def cleanup_pages_markdown(text: str) -> str:
    """Pages 변환 결과의 공통 결함을 순차적으로 정리한다."""
    text = strip_print_header(text)
    text = strip_board_meta(text)
    text = merge_korean_linebreaks(text)
    text = collapse_blank_lines(text)
    text = promote_headings(text)
    return text.strip()
