"""Home page and preface: plain voice, true cohort line, judging deep link."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import landing  # noqa: E402

WEIGHTS = {
    "rarity": 0.30,
    "climate_stress": 0.25,
    "harvest_proxy": 0.25,
    "pa_gap": 0.20,
}


class LandingCopyTests(unittest.TestCase):
    def test_preface_states_the_problem_and_the_index(self):
        html = landing.preload_markup(WEIGHTS)
        self.assertIn("still taken from the wild", html)
        self.assertIn("None of them is a field score", html)
        self.assertIn("never invents one", html)
        self.assertIn("HPI = 0.30 R + 0.25 C + 0.25 H + 0.20 P", html)
        self.assertNotIn("href=", html)
        landing.assert_plain_voice(html)

    def test_home_is_one_path_not_a_feature_grid(self):
        html = landing.home_markup(
            n_taxa=35,
            band_counts={
                "Lower relative pressure": 2,
                "Moderate": 33,
                "Higher relative pressure": 0,
            },
            n_imputed=1,
            iucn_unlinked=True,
            weights=WEIGHTS,
        )
        self.assertIn("Harvester Risk Atlas", html)
        self.assertIn("The problem", html)
        self.assertIn("What the atlas solves", html)
        self.assertIn("WDPCA Philippines", html)
        self.assertIn("not a Red List assessment", html)
        self.assertIn("35 taxa", html)
        self.assertIn("2 lower, 33 moderate, 0 higher", html)
        self.assertIn("color alone does not separate", html)
        self.assertIn("Categories are blank, not guessed", html)
        self.assertNotIn("AI-powered", html)
        self.assertNotIn("chat", html.lower())
        landing.assert_plain_voice(html)
        # One document, not three icon cards.
        self.assertNotIn("feature-card", html)
        self.assertNotIn("cta-row", html)

    def test_linked_iucn_is_not_described_as_blank(self):
        note = landing.cohort_note(
            n_taxa=4,
            band_counts={"Higher relative pressure": 1, "Moderate": 3},
            n_imputed=0,
            iucn_unlinked=False,
        )
        self.assertNotIn("not guessed", note)
        self.assertNotIn("color alone", note)

    def test_judging_link_skips_the_preface_and_opens_the_map(self):
        self.assertTrue(landing.demo_query_requested({"demo": "1"}))
        self.assertTrue(landing.demo_query_requested({"demo": ""}))
        self.assertFalse(landing.demo_query_requested({}))
        self.assertFalse(
            landing.should_play_intro(intro_played=False, demo_requested=True)
        )
        self.assertFalse(
            landing.should_play_intro(intro_played=True, demo_requested=False)
        )
        self.assertTrue(
            landing.should_play_intro(intro_played=False, demo_requested=False)
        )
        self.assertEqual(landing.default_page(demo_requested=True), "Map")
        self.assertEqual(landing.default_page(demo_requested=False), "Home")


class LandingStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "app" / "styles.css").read_text(encoding="utf-8")
        cls.app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")

    def test_preface_is_opacity_only_and_reduced_motion_removes_it(self):
        self.assertIn(".hra-preload", self.css)
        self.assertIn("hra-preload-leave", self.css)
        self.assertNotIn("hra-bounce", self.css)
        # The later reduced-motion block must hide the preface outright.
        # A crushed duration would otherwise leave a blank sheet up for the delay.
        hide = self.css.split(".hra-preload { display: none !important; }")
        self.assertGreaterEqual(len(hide), 2)
        self.assertIn('"Home"', self.app)
        self.assertIn("Open the map", self.app)
        self.assertIn('qp.get("intro") == "skip"', self.app)
        self.assertIn('st.button("Skip"', self.app)
        self.assertIn("preload_markup", self.app)
        self.assertIn("on_click=go_to", self.app)
        self.assertNotIn('st.session_state["nav_radio"] = "Map"', self.app)


if __name__ == "__main__":
    unittest.main()
