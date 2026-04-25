from pathlib import Path

from app.services.guidance_parser import GuidanceParser


def build_markdown_file(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "指导书.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_markdown_heading_split(tmp_path: Path):
    file_path = build_markdown_file(
        tmp_path,
        """
# 安全物理环境
## 安全通用要求
| 测评项 | 操作步骤 | 预期结果 |
| --- | --- | --- |
| 物理访问控制 | 应核查门禁配置 | 应提供门禁记录 |
## 云计算扩展要求
云平台应位于中国境内。
""".strip(),
    )

    parser = GuidanceParser()
    sections = parser.parse(file_path, "md/指导书.md")

    assert len(sections) == 3
    assert sections[1].section_path == "安全物理环境 / 安全通用要求"
    assert "应核查门禁配置" in sections[1].plain_text
    assert any("门禁" in item for item in sections[1].check_points_json)
    assert any("记录" in item for item in sections[1].evidence_requirements_json)


def test_guidance_code_is_stable(tmp_path: Path):
    file_path = build_markdown_file(tmp_path, "# 安全物理环境\n## 安全通用要求\n应核查机房。")
    parser = GuidanceParser()

    first = parser.parse(file_path, "md/指导书.md")
    second = parser.parse(file_path, "md/指导书.md")

    assert first[0].guidance_code == second[0].guidance_code
    assert first[1].guidance_code == second[1].guidance_code
