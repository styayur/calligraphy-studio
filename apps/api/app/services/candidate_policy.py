"""Conservative cultural compatibility shared by composition and similarity."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CandidatePolicy:
    tradition: str | None = None
    locale: str | None = None
    script: str | None = None
    period: str | None = None
    work: str | None = None
    mode: Literal["strict", "related", "cross-tradition"] = "strict"
    variant_type: str | None = None

    def accepts(self, glyph) -> bool:
        if self.mode != "cross-tradition":
            if self.tradition and glyph.writing_tradition != self.tradition:
                return False
            if self.locale and glyph.locale and glyph.locale != self.locale:
                return False
        if self.script and glyph.script != self.script:
            return False
        if self.variant_type and glyph.variant_type != self.variant_type:
            return False
        if self.mode == "strict" and not self.variant_type and glyph.variant_type == "hentaigana":
            return False
        if self.mode == "strict" and not self.variant_type and getattr(glyph,'orthography',None) == 'historical-kana':
            return False
        return True


WEIGHTS = dict(visual=.55, locale=.12, tradition=.12, script=.08, period=.05, work=.05, repetition=1)


def candidate_cost(glyph, visual_cost: float, policy: CandidatePolicy, weights: dict | None = None,
                   repetition: float = 0) -> float:
    import math
    if not policy.accepts(glyph):
        return float("inf")
    w = weights or WEIGHTS
    if set(w) != set(WEIGHTS) or any(not math.isfinite(v) or v < 0 for v in w.values()):
        raise ValueError("Invalid candidate weights")
    def mismatch(actual, expected):
        return int(bool(actual and expected and actual != expected))
    return (w["visual"] * visual_cost + w["locale"] * mismatch(glyph.locale, policy.locale)
            + w["tradition"] * mismatch(glyph.writing_tradition, policy.tradition)
            + w["script"] * mismatch(glyph.script, policy.script)
            + w["period"] * mismatch(glyph.period, policy.period)
            + w["work"] * mismatch(glyph.source.work, policy.work) + w["repetition"] * repetition)
