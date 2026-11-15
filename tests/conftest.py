import asyncio
import dataclasses
import os
import sys

import flet as ft
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import core  # noqa: E402


class FakePage:
    """Minimální náhrada stránky Flet pro testy bez grafického klienta."""

    def __init__(self, web=False):
        self.views = []
        self.dialogs = []
        self.web = web
        self.title = ""
        self.fonts = {}
        self.theme = self.dark_theme = self.theme_mode = self.bgcolor = None
        self.on_view_pop = None
        self.tasks = []

    def update(self, *a):
        pass

    def show_dialog(self, d):
        self.dialogs.append(d)

    def pop_dialog(self):
        return self.dialogs.pop() if self.dialogs else None

    def run_task(self, fn, *a, **kw):
        self.tasks.append(fn(*a, **kw))


class MemoryStore:
    def __init__(self):
        self.data = {}
        self.imgs = {}

    async def get_json(self, key, default):
        return self.data.get(key, default)

    async def set_json(self, key, value):
        import json
        self.data[key] = json.loads(json.dumps(value))

    async def remove(self, key):
        self.data.pop(key, None)

    async def save_image(self, image_id, data):
        self.imgs[image_id] = data
        return "pref:" + image_id

    async def load_image(self, ref):
        return self.imgs.get(ref[5:])

    async def delete_image(self, ref):
        self.imgs.pop(ref[5:], None)


def drain(page):
    loop = asyncio.new_event_loop()
    try:
        for _ in range(10):
            if not page.tasks:
                break
            tasks, page.tasks = page.tasks, []
            for t in tasks:
                loop.run_until_complete(t)
    finally:
        loop.close()


def walk(ctrl, seen=None):
    """Projde strom ovládacích prvků."""
    if seen is None:
        seen = set()
    if ctrl is None or id(ctrl) in seen:
        return
    if isinstance(ctrl, (list, tuple)):
        for c in ctrl:
            yield from walk(c, seen)
        return
    if not isinstance(ctrl, ft.BaseControl):
        return
    seen.add(id(ctrl))
    yield ctrl
    for f in dataclasses.fields(ctrl):
        if f.name.startswith("_") or f.name in ("parent", "page"):
            continue
        v = getattr(ctrl, f.name, None)
        if isinstance(v, (ft.BaseControl, list, tuple)):
            yield from walk(v, seen)


class Ev:
    def __init__(self, control, value=None):
        self.control = control
        self.data = value


@pytest.fixture
def make_app():
    def _make(web=False):
        page = FakePage(web=web)
        app = core.App(page, set())
        app.store = MemoryStore()

        async def no_pick():  # bez grafického klienta není výběr souborů
            return None
        app.pick_image = no_pick
        return app, page
    return _make
