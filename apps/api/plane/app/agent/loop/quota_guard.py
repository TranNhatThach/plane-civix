# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from decimal import Decimal
from typing import Dict, Any, Tuple


class QuotaGuard:
    """
    Token Metering & Pricing Ledger for Commercial Monetization.
    Calculates exact token costs based on model rates and enforces workspace budgets.
    """

    MODEL_RATES = {
        "gpt-4o": (Decimal("2.50"), Decimal("10.00")),
        "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
        "deepseek-chat": (Decimal("0.14"), Decimal("0.28")),
        "deepseek-reasoner": (Decimal("0.55"), Decimal("2.19")),
        "claude-3-5-sonnet": (Decimal("3.00"), Decimal("15.00")),
        "claude-3-5-haiku": (Decimal("0.80"), Decimal("4.00")),
        "gemini-1.5-pro": (Decimal("1.25"), Decimal("5.00")),
        "gemini-1.5-flash": (Decimal("0.075"), Decimal("0.30")),
        "groq/llama-3.3-70b": (Decimal("0.59"), Decimal("0.79")),
    }

    DEFAULT_RATE = (Decimal("0.20"), Decimal("0.80"))

    def __init__(
        self,
        workspace_id: str = "",
        tier: str = "pro",
        monthly_budget: int = 1_000_000,
        current_used: int = 0,
    ):
        self.workspace_id = workspace_id
        self.tier = tier
        self.monthly_budget = monthly_budget
        self.current_used = current_used

    def check_quota(self, estimated_prompt_tokens: int = 1000) -> Tuple[bool, str]:
        """Verifies if workspace has enough token budget remaining."""
        if self.monthly_budget == -1 or self.tier == "enterprise":
            return True, ""

        if self.current_used + estimated_prompt_tokens > self.monthly_budget:
            remaining = max(0, self.monthly_budget - self.current_used)
            return (
                False,
                f"Workspace đã chạm giới hạn {self.monthly_budget:,} tokens trong tháng "
                f"(còn lại: {remaining:,} tokens). Vui lòng nâng cấp gói để tiếp tục.",
            )
        return True, ""

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Decimal:
        """Calculates precise cost in USD."""
        rate = cls.DEFAULT_RATE
        for m, r in cls.MODEL_RATES.items():
            if m.lower() in model_name.lower():
                rate = r
                break

        in_cost = (Decimal(str(prompt_tokens)) / Decimal("1000000")) * rate[0]
        out_cost = (Decimal(str(completion_tokens)) / Decimal("1000000")) * rate[1]
        return in_cost + out_cost

    def record_usage(self, prompt_tokens: int, completion_tokens: int):
        self.current_used += prompt_tokens + completion_tokens
