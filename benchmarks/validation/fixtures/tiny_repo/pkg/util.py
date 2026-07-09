"""Util module: imports core, calls Widget.render indirectly."""

from pkg.core import Widget


def make_widget(name):
    w = Widget(name)
    return w.render()
