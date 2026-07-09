"""Core module: defines Widget and a helper function."""


def helper(x):
    return x + 1


class Widget:
    def __init__(self, name):
        self.name = name

    def render(self):
        return helper(len(self.name))
