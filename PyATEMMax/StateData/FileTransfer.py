#!/usr/bin/env python3
# coding: utf-8
"""
PyATEMMax state data: FileTransfer
Part of the PyATEMMax library.
"""

# pylint: disable=missing-class-docstring, wildcard-import, unused-wildcard-import


class FileTransfer():
    def __init__(self):
        self.transferId: int = 0
        self.transferStoreId: int = 0
        self.transferIndex: int = 0
        self.transferActive: bool = False
        self.transferName: str = ""
        self.transferData: bytes = b""
        self.transferHash: bytes = b""
        self.lastTransferId: int = 0
