from __future__ import annotations

from datetime import datetime, UTC

from pydantic import BaseModel, Field

from app.core.exceptions import BadRequestException
from app.services.ocr.base import OCRLine, OCRResult


MOCK_OCR_SAMPLES: dict[str, dict] = {
    "firewall_basic": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "firewall_basic",
        "full_text": "设备名称：FW-O1\n管理IP：10.0.O.1\n系统版本：V3.2.1\n设备型号：USG-6000",
        "pages": [
            {
                "page": 1,
                "confidence": 0.98,
                "text": "设备名称：FW-O1\n管理IP：10.0.O.1\n系统版本：V3.2.1\n设备型号：USG-6000",
                "segments": [
                    {"text": "设备名称：FW-O1", "confidence": 0.99, "source_text": "设备名称：FW-O1"},
                    {"text": "管理IP：10.0.O.1", "confidence": 0.97, "source_text": "管理IP：10.0.O.1"},
                ],
            }
        ],
    },
    "switch_h3c": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "switch_h3c",
        "full_text": "设备厂商：H3C\n设备类型：交换机\n主机名：SW-CORE-01",
        "pages": [{"page": 1, "confidence": 0.96, "text": "设备厂商：H3C\n设备类型：交换机\n主机名：SW-CORE-01", "segments": []}],
    },
    "server_linux": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "server_linux",
        "full_text": "操作系统：Linux\n主机名称：SRV-LINUX-99\n版本：Rocky Linux 9",
        "pages": [{"page": 1, "confidence": 0.95, "text": "操作系统：Linux\n主机名称：SRV-LINUX-99\n版本：Rocky Linux 9", "segments": []}],
    },
    "windows_host": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "windows_host",
        "full_text": "主机名称：WIN-SRV-01\n操作系统：Windows Server 2022\n补丁级别：KB5030219",
        "pages": [{"page": 1, "confidence": 0.97, "text": "主机名称：WIN-SRV-01\n操作系统：Windows Server 2022\n补丁级别：KB5030219", "segments": []}],
    },
    "windows_host_partial": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "windows_host_partial",
        "full_text": "主机名称：WIN-SRV-02\n操作系统：Windows Server 2019",
        "pages": [{"page": 1, "confidence": 0.93, "text": "主机名称：WIN-SRV-02\n操作系统：Windows Server 2019", "segments": []}],
    },
    "windows_password_policy": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "windows_password_policy",
        "full_text": "主机名称：WIN-SRV-01\n最小密码长度：I2 位\n密码复杂度 = 大写字母、小写字母、数字和特殊字符\n账户锁定阈值 = 5次\n默认账户状态：禁用",
        "pages": [{"page": 1, "confidence": 0.96, "text": "主机名称：WIN-SRV-01\n最小密码长度：I2 位\n密码复杂度 = 大写字母、小写字母、数字和特殊字符\n账户锁定阈值 = 5次\n默认账户状态：禁用", "segments": []}],
    },
    "linux_access_control": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "linux_access_control",
        "full_text": "主机名称：SRV-LINUX-01\n是否允许远程登录：是\nPermitRootLogin = yes\n管理员账户数量 = 2个\n长期未用账户状态：禁用",
        "pages": [{"page": 1, "confidence": 0.95, "text": "主机名称：SRV-LINUX-01\n是否允许远程登录：是\nPermitRootLogin = yes\n管理员账户数量 = 2个\n长期未用账户状态：禁用", "segments": []}],
    },
    "host_audit_config": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "host_audit_config",
        "full_text": "主机名称：SRV-AUDIT-01\n审计功能状态：已启用\n登录日志 = 开启\n操作日志：enabled\n日志保留时间：18O 天",
        "pages": [{"page": 1, "confidence": 0.95, "text": "主机名称：SRV-AUDIT-01\n审计功能状态：已启用\n登录日志 = 开启\n操作日志：enabled\n日志保留时间：18O 天", "segments": []}],
    },
    "host_malware_protection": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "host_malware_protection",
        "full_text": "主机名称：SRV-AV-01\n已安装杀毒软件：是\n实时防护状态：启用\n病毒库版本 = V1.2.3\n基线检查状态：已启用",
        "pages": [{"page": 1, "confidence": 0.95, "text": "主机名称：SRV-AV-01\n已安装杀毒软件：是\n实时防护状态：启用\n病毒库版本 = V1.2.3\n基线检查状态：已启用", "segments": []}],
    },
    "security_policy": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "security_policy",
        "full_text": "策略名称：办公区访问服务器\n源区域：办公区\n目的区域：服务器区\n动作：permit",
        "pages": [{"page": 1, "confidence": 0.96, "text": "策略名称：办公区访问服务器\n源区域：办公区\n目的区域：服务器区\n动作：permit", "segments": []}],
    },
    "security_policy_missing_action": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "security_policy_missing_action",
        "full_text": "策略名称：办公区访问服务器\n源区域：办公区\n目的区域：服务器区",
        "pages": [{"page": 1, "confidence": 0.92, "text": "策略名称：办公区访问服务器\n源区域：办公区\n目的区域：服务器区", "segments": []}],
    },
    "network_config": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "network_config",
        "full_text": "管理地址：192.168.1.10\n子网掩码：255.255.255.O\n默认网关：192.168.1.1",
        "pages": [{"page": 1, "confidence": 0.95, "text": "管理地址：192.168.1.10\n子网掩码：255.255.255.O\n默认网关：192.168.1.1", "segments": []}],
    },
    "noisy_mixed": {
        "provider": "mock_ocr",
        "status": "completed",
        "sample_id": "noisy_mixed",
        "full_text": "设备名 ： SW-l01\nIP地址：172.16.O.5\n版本号： V2.O\n备注：图片模糊",
        "pages": [{"page": 1, "confidence": 0.83, "text": "设备名 ： SW-l01\nIP地址：172.16.O.5\n版本号： V2.O\n备注：图片模糊", "segments": []}],
    },
}


class MockOCRSampleCreate(BaseModel):
    provider: str = Field(default="mock_ocr")
    status: str = Field(default="completed")
    sample_id: str
    full_text: str


class MockOCRAdapter:
    def run(self, *, evidence_id: str, filename: str, file_path: str, sample_id: str | None = None) -> OCRResult:
        resolved_sample = sample_id or self._infer_sample_id(filename)
        payload = MOCK_OCR_SAMPLES.get(resolved_sample)
        if not payload:
            raise BadRequestException("MOCK_OCR_SAMPLE_NOT_FOUND", "指定的mock OCR样例不存在")

        lines = self._build_lines(payload)
        full_text = "\n".join(line["text"] for line in lines if line["text"])
        return {
            **payload,
            "full_text": full_text,
            "lines": lines,
            "evidence_id": evidence_id,
            "filename": filename,
            "file_path": file_path,
            "processed_at": datetime.now(UTC).isoformat(),
            "error": payload.get("error"),
        }

    def _build_lines(self, payload: dict) -> list[OCRLine]:
        text = str(payload.get("full_text") or "")
        confidence = self._get_default_confidence(payload)
        return [
            {
                "text": line,
                "confidence": confidence,
                "bbox": [],
            }
            for line in text.splitlines()
            if line.strip()
        ]

    def _get_default_confidence(self, payload: dict) -> float | None:
        pages = payload.get("pages") or []
        if not pages:
            return None
        value = pages[0].get("confidence")
        return float(value) if value is not None else None

    def _infer_sample_id(self, filename: str) -> str:
        lower_name = filename.lower()
        if "firewall" in lower_name or "fw" in lower_name:
            return "firewall_basic"
        if "windows" in lower_name or "host" in lower_name:
            return "windows_host"
        if "policy" in lower_name:
            return "security_policy"
        if "network" in lower_name or "config" in lower_name:
            return "network_config"
        return "noisy_mixed"
