from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ParsedGuidanceSection:
    guidance_code: str
    source_file: str
    section_path: str
    section_title: str
    level1: str | None
    level2: str | None
    level3: str | None
    raw_markdown: str
    plain_text: str
    keywords_json: list[str]
    check_points_json: list[str]
    evidence_requirements_json: list[str]
    record_suggestion: str | None


class GuidanceParser:
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
    IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]")
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
    TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,}|[一-鿿]{2,}")
    SPLIT_PATTERN = re.compile(r"[；;。.!?\n]+")
    STOPWORDS = {
        "应", "是否", "进行", "通过", "可以", "以及", "相关", "要求", "措施", "测评", "指标", "结果", "标准", "检查", "核查", "访谈", "查看",
        "the", "and", "for", "with", "from", "that", "this", "are",
    }
    EVIDENCE_HINTS = ("文档", "记录", "截图", "日志", "报告", "拓扑", "配置", "清单", "验收", "台账", "方案", "证明", "扫描")
    CHECK_HINTS = ("应核查", "核查", "检查", "访谈", "测试验证", "查看", "确认", "检测")
    RECORD_HINTS = ("预期结果", "符合", "建议", "应为", "应提供")

    def parse(self, file_path: Path, source_file: str) -> list[ParsedGuidanceSection]:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        sections: list[dict] = []
        heading_stack: list[tuple[int, str]] = []
        current: dict | None = None

        for line in lines:
            heading = self._parse_heading(line)
            if heading:
                if current:
                    sections.append(current)
                level, title = heading
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))
                titles = [item[1] for item in heading_stack]
                current = {
                    "heading_line": line.strip(),
                    "heading_level": level,
                    "section_title": title,
                    "section_path": " / ".join(titles),
                    "level1": titles[0] if len(titles) > 0 else None,
                    "level2": titles[1] if len(titles) > 1 else None,
                    "level3": titles[2] if len(titles) > 2 else None,
                    "lines": [],
                }
                continue
            if current:
                current["lines"].append(line)

        if current:
            sections.append(current)

        parsed_sections: list[ParsedGuidanceSection] = []
        for section in sections:
            raw_markdown = "\n".join([section["heading_line"], *section["lines"]]).strip()
            plain_text = self._to_plain_text(raw_markdown)
            if not plain_text:
                continue
            parsed_sections.append(
                ParsedGuidanceSection(
                    guidance_code=self._build_guidance_code(source_file, section["section_path"]),
                    source_file=source_file,
                    section_path=section["section_path"],
                    section_title=section["section_title"],
                    level1=section["level1"],
                    level2=section["level2"],
                    level3=section["level3"],
                    raw_markdown=raw_markdown,
                    plain_text=plain_text,
                    keywords_json=self._extract_keywords(section["section_title"], plain_text),
                    check_points_json=self._extract_check_points(raw_markdown),
                    evidence_requirements_json=self._extract_evidence_requirements(raw_markdown),
                    record_suggestion=self._extract_record_suggestion(raw_markdown),
                )
            )
        return parsed_sections

    def _parse_heading(self, line: str) -> tuple[int, str] | None:
        match = self.HEADING_PATTERN.match(line)
        if not match:
            return None
        return len(match.group(1)), match.group(2).strip()

    def _build_guidance_code(self, source_file: str, section_path: str) -> str:
        slug_source = re.sub(r"[^A-Za-z0-9一-鿿]+", "-", section_path).strip("-").lower()
        slug = slug_source[:64] or "guidance"
        digest = hashlib.sha1(f"{source_file}|{section_path}".encode("utf-8")).hexdigest()[:12]
        return f"gd-{slug}-{digest}"

    def _to_plain_text(self, raw_markdown: str) -> str:
        text = self.IMAGE_PATTERN.sub(" ", raw_markdown)
        text = self.LINK_PATTERN.sub(r"\1", text)
        normalized_lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            stripped = re.sub(r"^#{1,6}\s+", "", stripped)
            stripped = re.sub(r"^[-*+]\s+", "", stripped)
            stripped = re.sub(r"^\d+[.)、]\s*", "", stripped)
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [cell.strip() for cell in stripped.strip("|").split("|")]
                if cells and all(re.fullmatch(r"[:\-\s]+", cell or "") for cell in cells):
                    continue
                stripped = " ".join(cell for cell in cells if cell)
            normalized_lines.append(stripped)
        plain_text = "\n".join(normalized_lines)
        plain_text = re.sub(r"\s+", " ", plain_text).strip()
        return plain_text

    def _extract_keywords(self, title: str, plain_text: str) -> list[str]:
        counter: Counter[str] = Counter()
        for token in self.TOKEN_PATTERN.findall(f"{title} {plain_text}"):
            normalized = token.strip().lower()
            if normalized in self.STOPWORDS:
                continue
            if len(normalized) < 2:
                continue
            counter[normalized] += 1
        keywords = [token for token, _ in counter.most_common(12)]
        return keywords

    def _extract_check_points(self, raw_markdown: str) -> list[str]:
        return self._extract_sentences(raw_markdown, self.CHECK_HINTS, limit=12)

    def _extract_evidence_requirements(self, raw_markdown: str) -> list[str]:
        return self._extract_sentences(raw_markdown, self.EVIDENCE_HINTS, limit=12)

    def _extract_record_suggestion(self, raw_markdown: str) -> str | None:
        candidates = self._extract_sentences(raw_markdown, self.RECORD_HINTS, limit=6)
        return candidates[0] if candidates else None

    def _extract_sentences(self, raw_markdown: str, hints: tuple[str, ...], limit: int) -> list[str]:
        plain_text = self._to_plain_text(raw_markdown)
        if not plain_text:
            return []
        results: list[str] = []
        for chunk in self.SPLIT_PATTERN.split(plain_text):
            sentence = chunk.strip()
            if len(sentence) < 6:
                continue
            if any(hint in sentence for hint in hints):
                if sentence not in results:
                    results.append(sentence)
            if len(results) >= limit:
                break
        return results
