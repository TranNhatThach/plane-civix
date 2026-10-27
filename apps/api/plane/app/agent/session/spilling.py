# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class SpillingEngine:
    """
    Context Hygiene & Tool Output Spilling Engine.
    Prevents Context Overflow by intercepting oversized tool results,
    storing the raw output securely, and providing structured citations.
    """

    DEFAULT_THRESHOLD = 4000  # Characters threshold (~1000 tokens)
    DEFAULT_PREVIEW_SIZE = 1500

    def __init__(self, threshold: int = DEFAULT_THRESHOLD):
        self.threshold = threshold
        self._spill_store: Dict[str, str] = {}

    def process_output(self, tool_name: str, raw_output: Any) -> Tuple[str, Optional[str]]:
        """
        Processes tool output. If payload exceeds threshold, saves to spill store
        and returns (truncated_preview_with_citation, citation_id).
        Otherwise returns (original_payload, None).
        """
        if isinstance(raw_output, (dict, list)):
            payload_str = json.dumps(raw_output, ensure_ascii=False)
        else:
            payload_str = str(raw_output)

        if len(payload_str) <= self.threshold:
            return payload_str, None

        # Generate citation hash
        citation_id = f"spill_{hashlib.sha256(payload_str.encode('utf-8')).hexdigest()[:12]}"
        self._spill_store[citation_id] = payload_str

        preview = payload_str[:self.DEFAULT_PREVIEW_SIZE]
        truncated_msg = (
            f"{preview}\n\n"
            f"... [⚠️ DỮ LIỆU ĐÃ ĐƯỢC TÓM LƯỢC]\n"
            f"Tổng kích thước: {len(payload_str)} ký tự. Dữ liệu đầy đủ đã được lưu trữ an toàn "
            f"tại mã tham chiếu: #{citation_id}.\n"
            f"Gợi ý: Dùng công cụ đọc phân trang nếu cần truy xuất các dòng tiếp theo."
        )
        return truncated_msg, citation_id

    def read_spill(self, citation_id: str, offset: int = 0, limit: int = 3000) -> Optional[str]:
        """Reads paginated slice of stored spill content."""
        if citation_id not in self._spill_store:
            return None
        content = self._spill_store[citation_id]
        return content[offset:offset + limit]

    def clear(self):
        self._spill_store.clear()
