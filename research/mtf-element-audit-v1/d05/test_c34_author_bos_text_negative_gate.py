"""C34 negative-only academic BOS text controls; NEVER claim source-positive case."""
import unittest
from dataclasses import replace
from decimal import Decimal as D
from c34_author_bos_text_negative_gate import (
    C34RulePremises,judge_textual_bos_rules,SOURCE_BOS,AUTHOR_BACKTEST_MISSING)

def good(**changes):
    p=C34RulePremises("BSL","WICK",D("95"),D("100"),
        True,True,False,True,True)
    return replace(p,**changes)

def codes(p):
    return judge_textual_bos_rules(p).mandatory_invalidation_codes

class C34AuthorBOSNegativeOnly(unittest.TestCase):
    def test_text_source_and_missing_backtest_are_explicit(self):
        self.assertIn("drive.google.com",SOURCE_BOS)
        self.assertIn("notion.so",AUTHOR_BACKTEST_MISSING)
    def test_good_synthetic_geometry_never_becomes_author_ready(self):
        a=judge_textual_bos_rules(good())
        self.assertEqual(a.mandatory_invalidation_codes,())
        self.assertEqual(a.instructor_route_classification,
                         "ACADEMIC_BOS_AUTHOR_CHOICE_INDETERMINATE")
        self.assertEqual(a.readiness,"NOT_TRADE_READY")
    def test_market_order_never_allowed(self):
        self.assertFalse(judge_textual_bos_rules(good()).market_orders_allowed)
    def test_limit_order_never_allowed(self):
        self.assertFalse(judge_textual_bos_rules(good()).limit_orders_allowed)
    def test_trade_never_allowed(self):
        self.assertFalse(judge_textual_bos_rules(good()).trades_allowed)
    def test_paper_signal_never_approved(self):
        self.assertFalse(judge_textual_bos_rules(good()).available_for_paper_signals)
    def test_bsl_bos_equal_raid_is_invalid(self):
        self.assertIn("AUTHOR_BSL_RAID_REQUIRES_BOS_BELOW_LEVEL",
                      codes(good(selected_bos_level=D("100"))))
    def test_bsl_bos_above_raid_is_invalid(self):
        self.assertIn("AUTHOR_BSL_RAID_REQUIRES_BOS_BELOW_LEVEL",
                      codes(good(selected_bos_level=D("101"))))
    def test_bsl_bos_below_is_not_by_itself_disqualified(self):
        self.assertNotIn("AUTHOR_BSL_RAID_REQUIRES_BOS_BELOW_LEVEL",codes(good()))
    def test_ssl_bos_equal_raid_is_invalid(self):
        self.assertIn("AUTHOR_SSL_RAID_REQUIRES_BOS_ABOVE_LEVEL",
                      codes(good(raid_side="SSL",selected_bos_level=D("100"))))
    def test_ssl_bos_below_raid_is_invalid(self):
        self.assertIn("AUTHOR_SSL_RAID_REQUIRES_BOS_ABOVE_LEVEL",
                      codes(good(raid_side="SSL",selected_bos_level=D("90"))))
    def test_ssl_bos_above_not_by_itself_disqualified(self):
        self.assertNotIn("AUTHOR_SSL_RAID_REQUIRES_BOS_ABOVE_LEVEL",
                      codes(good(raid_side="SSL",selected_bos_level=D("105"))))
    def test_no_liquidity_raid_is_invalid(self):
        self.assertIn("AUTHOR_REQUIRES_1H_FRACTAL_WICK_RAID",
                      codes(good(raid_interaction="NONE")))
    def test_body_raid_is_invalid_as_wick(self):
        self.assertIn("AUTHOR_REQUIRES_1H_FRACTAL_WICK_RAID",
                      codes(good(raid_interaction="BODY")))
    def test_unknown_raid_is_unresolved_not_invalidated_by_assertion(self):
        a=judge_textual_bos_rules(good(raid_interaction="UNKNOWN"))
        self.assertIn("1H_WICK_RAID_SOURCE_NOT_SHOWN",a.missing_academic_evidence)
        self.assertEqual(a.mandatory_invalidation_codes,())
    def test_no_three_minute_bos_is_invalid(self):
        self.assertIn("AUTHOR_3M_BOS_ABSENT",codes(good(model_3m_bos_exists=False)))
    def test_bos_not_verified_does_not_invent_missing_bos(self):
        a=judge_textual_bos_rules(good(model_3m_bos_exists=None))
        self.assertIn("3M_BOS_SOURCE_NOT_SHOWN",a.missing_academic_evidence)
        self.assertNotIn("AUTHOR_3M_BOS_ABSENT",a.mandatory_invalidation_codes)
    def test_no_proper_target_is_invalid(self):
        self.assertIn("AUTHOR_PROPER_TARGET_ABSENT",codes(good(proper_target_exists=False)))
    def test_first_trouble_bars_rr_is_invalid(self):
        self.assertIn("AUTHOR_FTA_BLOCKS_REWARD_RISK",
                      codes(good(first_trouble_undermines_rr=True)))
    def test_unknown_fta_is_not_false_positive_rejection(self):
        j=judge_textual_bos_rules(good(first_trouble_undermines_rr=None))
        self.assertIn("FIRST_TROUBLE_RR_NOT_VERIFIED",j.missing_academic_evidence)
        self.assertEqual(j.mandatory_invalidation_codes,())
    def test_stop_not_behind_raid_is_invalid(self):
        self.assertIn("AUTHOR_SL_NOT_BEYOND_SWEPT_LIQUIDITY",
                      codes(good(stop_is_beyond_swept_liquidity=False)))
    def test_stop_unknown_is_a_blocker_not_positive(self):
        j=judge_textual_bos_rules(good(stop_is_beyond_swept_liquidity=None))
        self.assertIn("STOP_BEYOND_RAID_NOT_VERIFIED",j.missing_academic_evidence)
    def test_missing_bos_price_is_not_guessed(self):
        j=judge_textual_bos_rules(good(selected_bos_level=None))
        self.assertIn("AUTHOR_BOS_TO_RAID_LEVEL_COMPARISON_NOT_POSSIBLE",
                      j.missing_academic_evidence)
    def test_missing_raid_level_is_not_guessed(self):
        j=judge_textual_bos_rules(good(raid_liquidity_level=None))
        self.assertIn("AUTHOR_BOS_TO_RAID_LEVEL_COMPARISON_NOT_POSSIBLE",
                      j.missing_academic_evidence)
    def test_forged_author_selection_cannot_create_signal(self):
        j=judge_textual_bos_rules(good(author_selected_bos_pivot_documented=True,
                                     author_goldens_positive_and_negative=True))
        self.assertEqual(j.readiness,"NOT_TRADE_READY")
        self.assertFalse(j.available_for_paper_signals)
        self.assertIn("AUTHOR_SELECTED_3M_BOS_PIVOT_POSITIVE_NEGATIVE_GOLDENS_MISSING",
                      j.missing_academic_evidence)
    def test_forged_tick_and_limit_details_cannot_enable_orders(self):
        j=judge_textual_bos_rules(good(price_cross_tick_order_documented=True,
                                     exact_limit_retest_documented=True))
        self.assertFalse(j.market_orders_allowed)
        self.assertFalse(j.limit_orders_allowed)
    def test_claimed_timezone_cannot_set_instructor_session(self):
        j=judge_textual_bos_rules(good(asserted_session_timezone="Europe/Kyiv"))
        self.assertIn("AUTHOR_SESSION_IANA_TIMEZONE_DST_UNVERIFIED",
                      j.missing_academic_evidence)
    def test_fifteen_pips_not_portable_to_crypto(self):
        j=judge_textual_bos_rules(good(stop_size_pips=D("16")))
        self.assertIn("STOP_15_PIPS_UNIT_NOT_PORTABLE_TO_CRYPTO",
                      j.missing_academic_evidence)
        self.assertEqual(j.mandatory_invalidation_codes,())
    def test_multiple_independent_source_negative_conditions(self):
        j=judge_textual_bos_rules(good(raid_interaction="BODY",
              model_3m_bos_exists=False,proper_target_exists=False,
              first_trouble_undermines_rr=True,stop_is_beyond_swept_liquidity=False,
              selected_bos_level=D("105")))
        self.assertEqual(len(j.mandatory_invalidation_codes),6)
    def test_no_reaction_not_secretly_accepted(self):
        j=judge_textual_bos_rules(good(reaction_confirmed=False))
        self.assertIn("LOCAL_RAID_REACTION_SOURCE_NOT_VERIFIED",
                      j.missing_academic_evidence)
        self.assertEqual(j.readiness,"NOT_TRADE_READY")
    def test_wrong_raid_direction_rejected(self):
        with self.assertRaisesRegex(ValueError,"C34_INVALID_RAID_DIRECTION"):
            judge_textual_bos_rules(good(raid_side="EURUSD"))
    def test_wrong_interaction_rejected(self):
        with self.assertRaisesRegex(ValueError,"C34_INVALID_RAID_INTERACTION"):
            judge_textual_bos_rules(good(raid_interaction="MAGIC"))
    def test_invalid_decimal_prices_rejected(self):
        for p in (D("NaN"),D("Infinity"),D("0"),D("-1")):
            with self.subTest(p=str(p)):
                with self.assertRaisesRegex(ValueError,"C34_UNTRUSTED_DECIMAL"):
                    judge_textual_bos_rules(good(selected_bos_level=p))
    def test_invalid_decimal_not_coerced_from_float(self):
        with self.assertRaisesRegex(ValueError,"C34_UNTRUSTED_DECIMAL"):
            judge_textual_bos_rules(good(raid_liquidity_level=100.0))
    def test_bool_flags_are_strict_not_truthy(self):
        with self.assertRaisesRegex(ValueError,"C34_UNTRUSTED_TRI_STATE"):
            judge_textual_bos_rules(good(model_3m_bos_exists=1))
    def test_cannot_enable_author_flag_with_nonboolean(self):
        with self.assertRaisesRegex(ValueError,"C34_UNTRUSTED_AUTHOR_OR_ROUTE_FLAG"):
            judge_textual_bos_rules(good(author_goldens_positive_and_negative="yes"))
    def test_unknown_session_not_accepted_as_invalid_string(self):
        with self.assertRaisesRegex(ValueError,"C34_INVALID_ASSERTED_TIMEZONE"):
            judge_textual_bos_rules(good(asserted_session_timezone=""))
    def test_untrusted_external_scenario_object_rejected(self):
        with self.assertRaisesRegex(ValueError,"C34_UNTRUSTED_RULE_PREMISES"):
            judge_textual_bos_rules({"raid_side":"BSL"})
if __name__=="__main__":unittest.main()
