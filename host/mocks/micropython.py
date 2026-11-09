"""Minimal ``micropython`` module stub for host imports (e.g. highlighter)."""


def const(x):
    return x


def native(f):
    return f


def viper(f):
    return f


def schedule(callback, arg):
    """Host stub: run immediately (device queues to main thread)."""
    callback(arg)
