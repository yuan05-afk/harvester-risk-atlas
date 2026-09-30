"""Streamlit Cloud import: do not wipe the package out from under importlib."""
from __future__ import annotations

import ast
import importlib._bootstrap as bootstrap
import importlib.util
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"


def _deletes_sys_modules(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Delete):
            for target in sub.targets:
                if _is_sys_modules(target):
                    return True
        if isinstance(sub, ast.Call):
            func = sub.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr in {"pop", "clear"}
                and _is_sys_modules(func.value)
            ):
                return True
    return False


def _is_sys_modules(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        node = node.value
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "modules"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    )


class CloudImportTests(unittest.TestCase):
    def test_entrypoint_does_not_wipe_sys_modules_before_config_import(self):
        tree = ast.parse(APP.read_text(encoding="utf-8"))
        saw_config = False
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "harvester_risk_atlas.config":
                saw_config = True
                break
            if _deletes_sys_modules(node):
                self.fail(
                    "app/streamlit_app.py deletes sys.modules before importing "
                    "harvester_risk_atlas.config. A second Cloud hard-refresh "
                    "then KeyErrors inside importlib._load_unlocked."
                )
        self.assertTrue(saw_config)
        # The wipe must not come back later in the entrypoint either.
        for node in tree.body:
            if _deletes_sys_modules(node):
                self.fail("app/streamlit_app.py still deletes sys.modules")

    def test_wipe_during_load_is_the_cloud_keyerror(self):
        """importlib._load_unlocked pops sys.modules[name] after exec_module.

        Deleting that entry mid-import is what the old per-run wipe did when
        a second hard refresh overlapped the first import.
        """
        name = "_hra_cloud_import_probe"
        sys.modules.pop(name, None)
        started = threading.Event()
        release = threading.Event()
        errors: list[BaseException] = []

        class _Loader:
            def create_module(self, spec):
                return None

            def exec_module(self, module):
                started.set()
                if not release.wait(2):
                    raise TimeoutError("wipe thread did not release the import")

        def _load():
            spec = importlib.util.spec_from_loader(name, _Loader())
            try:
                bootstrap._load(spec)
            except BaseException as exc:  # noqa: BLE001 — the Cloud failure is KeyError
                errors.append(exc)

        worker = threading.Thread(target=_load)
        worker.start()
        try:
            self.assertTrue(started.wait(2))
            module = sys.modules[name]
            self.assertTrue(module.__spec__._initializing)
            # Old app/streamlit_app.py lines 24–30.
            for mod_name in list(sys.modules):
                if mod_name == name:
                    del sys.modules[mod_name]
        finally:
            release.set()
            worker.join(2)
            sys.modules.pop(name, None)

        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], KeyError)
        self.assertEqual(errors[0].args[0], name)

    def test_leaving_an_initializing_module_lets_the_import_finish(self):
        name = "_hra_cloud_import_ok"
        sys.modules.pop(name, None)
        started = threading.Event()
        release = threading.Event()

        class _Loader:
            def create_module(self, spec):
                return None

            def exec_module(self, module):
                started.set()
                if not release.wait(2):
                    raise TimeoutError("second run did not finish")

        spec = importlib.util.spec_from_loader(name, _Loader())

        def _load():
            bootstrap._load(spec)

        worker = threading.Thread(target=_load)
        worker.start()
        try:
            self.assertTrue(started.wait(2))
            module = sys.modules[name]
            self.assertTrue(module.__spec__._initializing)
            # The fixed entrypoint does not delete this entry.
        finally:
            release.set()
            worker.join(2)

        self.assertFalse(worker.is_alive())
        self.assertIn(name, sys.modules)
        self.assertIs(sys.modules[name].__spec__, spec)
        self.assertFalse(sys.modules[name].__spec__._initializing)
        sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
