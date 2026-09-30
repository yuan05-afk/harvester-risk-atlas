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
        self.assertIn("No shared number shows that pressure", html)
        self.assertIn("never invents one", html)
        self.assertIn("HPI = 0.30 R + 0.25 C + 0.25 H + 0.20 P", html)
        self.assertLess(html.lower().count(" the "), 12)
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
        self.assertTrue(
            landing.should_play_intro(
                intro_played=True, demo_requested=True, replay=True
            )
        )
        self.assertFalse(
            landing.should_play_intro(
                intro_played=False, demo_requested=True, replay=False
            )
        )
        plain = landing.preload_markup(WEIGHTS)
        forced = landing.preload_markup(WEIGHTS, force_motion=True)
        self.assertNotIn("hra-force-motion", plain)
        self.assertIn('class="hra-preload hra-force-motion"', forced)
        self.assertIn("hra-sil", forced)
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
        self.assertIn("hra-skip-in 0.4s var(--ease) 3s forwards", self.css)
        self.assertIn("translateY(9px)", self.css)
        self.assertIn("hra-sil-in", self.css)
        self.assertIn("hra-draw", self.css)
        self.assertIn("hra-dot-in", self.css)
        self.assertIn(".hra-preload .b1 { --in: 0.40s; }", self.css)
        self.assertIn(".hra-preload .b2 { --in: 2.54s; }", self.css)
        self.assertIn(".hra-preload .b3 { --in: 4.68s; }", self.css)
        self.assertIn(".hra-preload .b4 { --in: 6.82s;", self.css)
        # Each beat is 2.05s and the next starts only after that window.
        starts = [0.40, 2.54, 4.68, 6.82]
        for prev, nxt in zip(starts, starts[1:]):
            self.assertGreaterEqual(nxt, prev + 2.05)
        html = (ROOT / "app" / "landing.py").read_text(encoding="utf-8")
        self.assertIn("<svg", html)
        self.assertIn("hra-leaf", html)
        self.assertIn("hra-sil", html)
        self.assertNotIn("b4f", html)
        sheet = landing.preload_markup(WEIGHTS)
        b4 = sheet.split('class="beat b4"')[1]
        self.assertIn("HPI = 0.30 R + 0.25 C + 0.25 H + 0.20 P", b4)
        self.assertIn("hra-page-in 180ms", self.css)
        self.assertIn(":not(:has(.hra-preload))", self.css)
        # Automatic reduced-motion still removes the sheet and Skip.
        # Replay opts one pass back in and restores the crushed durations.
        reduce_at = self.css.rfind("@media (prefers-reduced-motion: reduce)")
        tail = self.css[reduce_at:]
        self.assertIn(".hra-preload { display: none !important; }", tail)
        self.assertIn(".hra-skip", tail)
        self.assertNotIn(':has(button[kind="secondary"])', tail)
        self.assertIn(".hra-preload.hra-force-motion", tail)
        self.assertIn("display: flex !important", tail)
        self.assertIn("animation-duration: 1.55s !important", tail)
        self.assertIn("animation-duration: 9.15s !important", tail)
        self.assertIn("animation-duration: 0.4s, 0.48s !important", tail)
        replay_at = self.app.find("Replay intro")
        self.assertGreater(replay_at, 0)
        window = self.app[replay_at:replay_at + 220]
        self.assertIn("on_click=replay_intro", window)
        self.assertNotIn('type="primary"', window)
        self.assertIn("force_motion=replay", self.app)
        sheet_at = self.app.find("force_motion=replay")
        sheet_window = self.app[sheet_at:sheet_at + 500]
        self.assertIn("unsafe_allow_html=True", sheet_window)
        self.assertNotIn("st.html(sheet)", sheet_window)
        self.assertIn('st.markdown(\'<div class="hra-skip"></div>\'', self.app)
        self.assertIn('st.markdown(\'<div class="hra-replay"></div>\'', self.app)
        self.assertIn("padding: 1rem 1.25rem !important", self.css)
        self.assertIn("hra-dossier-grid", self.css)
        self.assertIn("hra-dossier-grid", self.app)
        self.assertIn("class=\"term\"", (ROOT / "app" / "landing.py").read_text(encoding="utf-8"))
        self.assertNotIn("st.info(", self.app)
        self.assertNotIn("border-left", self.css)
        self.assertNotIn("HeatMap", self.app)
        self.assertNotIn("MarkerCluster", self.app)


if __name__ == "__main__":
    unittest.main()
