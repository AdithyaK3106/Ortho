"""Entry point: imports util, calls make_widget."""

from pkg.util import make_widget


def run():
    return make_widget("demo")


if __name__ == "__main__":
    run()
