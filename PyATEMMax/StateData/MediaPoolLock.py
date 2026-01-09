#!/usr/bin/env python3
# coding: utf-8
"""
PyATEMMax state data: MediaPoolLock
Part of the PyATEMMax library.
"""

# pylint: disable=missing-class-docstring, wildcard-import, unused-wildcard-import


class MediaPoolLock():
    def __init__(self):
        self.locked: bool = False
        self.index: int = 0
