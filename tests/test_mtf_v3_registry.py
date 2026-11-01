"""V3 research: contact episodes, time labels and short-side symmetry."""
from __future__ import annotations

from dataclasses import replace

from ember.research.mtf_v2_bars import H1, H4, FlowBar
from ember.research.mtf_v3_registry import _label, d1_bias, registry
from ember.research.mtf_v3_zones import Zone


def sample():
    four = [FlowBar(i*H4,100,101,99,100,100,50) for i in range(180)]
    hour = [FlowBar(i*H1,100,100.5,99.5,100,100,50) for i in range(700)]
    zone = Zone("test-demand","demand","swing",99,101,4*H4,10*H4,"HL")
    return hour,four,zone


def test_episode_is_not_one_signal_per_overlapping_hour() -> None:
    hour,four,zone=sample()
    contacts,labels=registry("TESTUSDT",hour,four,[zone])
    assert len(contacts) == 1
    assert len(labels) == 1
    assert contacts[0].zone_known_at <= contacts[0].event_at-H1


def test_future_broken_zone_does_not_retroactively_erase_contact() -> None:
    hour,four,zone=sample()
    zone.broken_at=120*H4
    contacts,_=registry("TESTUSDT",hour,four,[zone])
    assert len(contacts) == 1
    assert contacts[0].event_at < zone.broken_at


def test_end_censors_forward_label_without_fabricating_success() -> None:
    hour,four,zone=sample()
    contacts,_=registry("TESTUSDT",hour,four,[zone])
    event=replace(contacts[0],event_at=hour[-1].ts+H1)
    labeled=_label(event,hour,len(hour)-1)
    assert labeled.status == "CENSORED"
    assert not labeled.forward_close_returns_pct


def test_short_future_excursion_uses_correct_direction() -> None:
    hour,four,_=sample()
    zone=Zone("test-supply","supply","swing",99,101,4*H4,10*H4,"LH")
    contacts,_=registry("TESTUSDT",hour,four,[zone])
    event=contacts[0]
    i=event.event_at//H1-1
    hour[i+1]=FlowBar((i+1)*H1,100,105,95,101,100,60)
    label=_label(event,hour,i)
    assert label.forward_max_favorable_pct["1"]>0
    assert label.forward_max_adverse_pct["1"]<0


def test_daily_bias_never_uses_partial_day() -> None:
    four=[FlowBar(i*H4,100,101,99,100,100,50) for i in range(150)]
    ends=[b.ts+H4 for b in four]
    asof=25*6*H4-2*H4
    before=d1_bias(four,ends,asof)
    changed=four[:]
    changed[149]=replace(changed[149],close=500,high=500)
    assert d1_bias(changed,ends,asof)==before
