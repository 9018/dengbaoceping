from io import BytesIO

from openpyxl import Workbook


def build_history_excel() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "出口防火墙"
    worksheet.append(["扩展标准", "控制点", "测评项", "结果记录", "符合情况", "分值", "编号"])
    worksheet.append(["安全通信网络", "边界访问控制", "应限制非授权访问", "经现场核查，已配置访问控制策略。", "符合", 1.0, "A-01"])
    worksheet.append([None, "边界访问控制", "应保留访问控制日志", "查看日志审计配置，当前已开启日志留存。", "部分符合", 0.6, "A-02"])

    second = workbook.create_sheet("核心交换机")
    second.append(["扩展标准", "控制点", "测评项", "结果记录", "符合情况", "分值", "编号"])
    second.append(["安全区域边界", "网络访问控制", "应配置 ACL", "未提供完整 ACL 配置截图。", "不符合", 0.2, "B-01"])
    second.append(["安全区域边界", "网络访问控制", "应定期核查", "当前设备为汇聚交换机，不适用该项。", "不适用", 0.0, "B-02"])

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()
