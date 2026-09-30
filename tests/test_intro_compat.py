"""New app file must tolerate an older landing module on Streamlit Cloud.

The call sites inspect signatures. They do not wipe sys.modules — that race
is what PR #13 removed. A stale mixed deploy still needs an owner reboot.
"""
from __future__ import annotations

import ast
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"
sys.path.insert(0, str(ROOT / "app"))

import landing  # noqa: E402

WEIGHTS = {
    "rarity": 0.30,
    "climate_stress": 0.25,
    "harvest_proxy": 0.25,
    "pa_gap": 0.20,
}


def _load_call_sites():
    """Exec only the defensive helpers. Avoids importing Streamlit."""
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    wanted = {"_signature_accepts", "_should_play_intro", "_preload_markup"}
    nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    future = ast.ImportFrom(
        module="__future__",
        names=[ast.alias(name="annotations")],
        level=0,
    )
    module = ast.Module(body=[future, *nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"inspect": inspect, "landing": landing}
    exec(compile(module, str(APP), "exec"), namespace)
    return namespace


def _old_should(*, intro_played: bool, demo_requested: bool) -> bool:
    return not intro_played and not demo_requested


def _old_markup(weights: dict) -> str:
    return f"plain:{weights['rarity']}"


class IntroCompatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _load_call_sites()
        cls.source = APP.read_text(encoding="utf-8")

    def test_current_landing_still_replays_and_forces_motion(self):
        play = self.ns["_should_play_intro"]
        markup = self.ns["_preload_markup"]
        self.assertTrue(play(intro_played=True, demo_requested=True, replay=True))
        self.assertFalse(play(intro_played=False, demo_requested=True, replay=False))
        forced = markup(WEIGHTS, force_motion=True)
        plain = markup(WEIGHTS, force_motion=False)
        self.assertIn('class="hra-preload hra-force-motion"', forced)
        self.assertNotIn("hra-force-motion", plain)

    def test_older_landing_without_replay_does_not_typeerror(self):
        original_should = landing.should_play_intro
        original_markup = landing.preload_markup
        landing.should_play_intro = _old_should
        landing.preload_markup = _old_markup
        try:
            play = self.ns["_should_play_intro"]
            markup = self.ns["_preload_markup"]
            self.assertTrue(play(intro_played=True, demo_requested=True, replay=True))
            self.assertFalse(play(intro_played=True, demo_requested=False, replay=False))
            self.assertTrue(play(intro_played=False, demo_requested=False, replay=False))
            self.assertEqual(markup(WEIGHTS, force_motion=True), "plain:0.3")
        finally:
            landing.should_play_intro = original_should
            landing.preload_markup = original_markup

    def test_unreadable_signature_drops_the_unknown_keyword(self):
        class _Inspect:
            @staticmethod
            def signature(_fn):
                raise ValueError("unreadable")

        original_should = landing.should_play_intro
        original_inspect = self.ns["inspect"]
        landing.should_play_intro = _old_should
        self.ns["inspect"] = _Inspect()
        try:
            play = self.ns["_should_play_intro"]
            self.assertTrue(play(intro_played=True, demo_requested=True, replay=True))
            self.assertFalse(play(intro_played=True, demo_requested=False, replay=False))
        finally:
            self.ns["inspect"] = original_inspect
            landing.should_play_intro = original_should

    def test_call_sites_do_not_wipe_sys_modules(self):
        tree = ast.parse(self.source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "modules":
                self.fail("streamlit_app.py still touches sys.modules")


if __name__ == "__main__":
    unittest.main()
