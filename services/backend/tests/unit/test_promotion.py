"""Tests for COW promotion service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from slaif_agent_site.agent_state.foundation import CowConflictError
from slaif_agent_site.agent_state.promotion import (
    PromotionError,
    promote_workspace,
)


class TestPromoteWorkspace:
    @pytest.mark.anyio
    async def test_successful_promotion(self) -> None:
        mock_result = MagicMock()
        mock_result.conflict_policy = "error"
        mock_result.no_op = False

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        session_id = uuid4()

        with patch(
            "slaif_agent_site.agent_state.promotion.asyncpg_cow_reviewer"
        ) as mock_reviewer_cls:
            mock_reviewer = AsyncMock()
            mock_reviewer.commit_session.return_value = mock_result
            mock_reviewer_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_reviewer
            )
            mock_reviewer_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await promote_workspace(mock_pool, session_id)
            assert result.conflict_policy == "error"

    @pytest.mark.anyio
    async def test_conflict_raises_promotion_error(self) -> None:
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        session_id = uuid4()

        with patch(
            "slaif_agent_site.agent_state.promotion.asyncpg_cow_reviewer"
        ) as mock_reviewer_cls:
            mock_reviewer = AsyncMock()
            mock_reviewer.commit_session.side_effect = CowConflictError(
                "conflict", "content"
            )
            mock_reviewer_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_reviewer
            )
            mock_reviewer_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(PromotionError, match="COW conflict"):
                await promote_workspace(mock_pool, session_id)
