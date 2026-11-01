"""Research-only 4H source selection-port invariants."""
from ember.research.mtf_v2_bars import H4, FlowBar
from ember.research.mtf_v3_zones import Zone
from ember.research.mtf_v4_source_selection import (
    native_midpoint_dedup,
    source_visible_active_zones,
)


def bars(n: int = 160) -> list[FlowBar]:
    result = [
        FlowBar(i * H4, 100, 101, 99, 100, 100, 50)
        for i in range(n)
    ]
    result[10] = FlowBar(10 * H4, 101, 104, 97, 100, 200, 100)
    result[20] = FlowBar(20 * H4, 100, 105, 99, 104, 200, 100)
    return result


def test_only_active_positive_width_levels_are_emitted() -> None:
    zones = source_visible_active_zones(bars())
    assert all(x["active"] for x in zones)
    assert all(x["high"] > x["low"] for x in zones)


def test_incomplete_future_cannot_change_snapshot_levels() -> None:
    earlier = bars(120)
    first = source_visible_active_zones(earlier)
    future = bars(170)
    future[-1] = FlowBar(169 * H4, 100, 250, 50, 120, 1000, 500)
    assert first == source_visible_active_zones(future[:120])


def test_original_nontransitive_findindex_dedup_chain() -> None:
    def level(i: int, price: float) -> Zone:
        return Zone(
            f"z{i}", "demand", "swing", price - .5, price + .5,
            i * H4, (i + 1) * H4, "test",
        )
    a = level(0, 100.0)
    b = level(1, 100.05)
    c = level(2, 100.10)
    # A excludes B; B (though excluded) still excludes C in TS findIndex.
    assert [z.zone_id for z in native_midpoint_dedup([a, b, c])] == ["z0"]
