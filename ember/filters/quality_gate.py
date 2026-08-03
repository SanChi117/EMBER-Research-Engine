"""Entry-time-only quality scoring."""

from __future__ import annotations

from ember.models import MTFContext, QualityScore, SetupCandidate
from ember.utils import bounded


class QualityGate:
    def score(
        self,
        trade_id: int,
        candidate: SetupCandidate,
        context: MTFContext,
    ) -> QualityScore:
        setup_score = 60.0 if candidate.setup_type in {"pullback", "ignition"} else 40.0
        if candidate.side == "long":
            location_score = (0.4 - context.pda_position) / 0.4 * 100.0
        else:
            location_score = (context.pda_position - 0.6) / 0.4 * 100.0
        location_score = bounded(location_score, 0.0, 100.0)

        session_score = 70.0 if context.session in {"london", "ny"} else 50.0
        timing_score = bounded((context.volume_ratio * 50.0 + session_score) / 2.0, 0.0, 100.0)
        aligned_structure = (
            (candidate.side == "long" and context.htf_structure == "uptrend")
            or (candidate.side == "short" and context.htf_structure == "downtrend")
        )
        structure_score = 80.0 if aligned_structure and context.htf_liquidity_swept else 60.0
        composite = (
            setup_score * 0.3
            + location_score * 0.3
            + timing_score * 0.2
            + structure_score * 0.2
        )
        grade = self._grade(composite)
        return QualityScore(
            trade_id=trade_id,
            setup_score=setup_score,
            location_score=location_score,
            timing_score=timing_score,
            structure_score=structure_score,
            composite=composite,
            grade=grade,
        )

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 75:
            return "A"
        if score >= 60:
            return "B"
        if score >= 45:
            return "C"
        return "D"
