"""Independent offline suite; not part of the frozen tests/research collection."""

import socket

import pytest


@pytest.fixture(autouse=True)
def prohibit_network(monkeypatch):
    def rejected(*args, **kwargs):
        raise AssertionError("model readiness acceptance must remain offline")
    monkeypatch.setattr(socket.socket, "connect", rejected)
    monkeypatch.setattr(socket, "create_connection", rejected)
