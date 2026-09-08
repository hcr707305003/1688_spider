#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI包初始化文件
"""

import sys
import os

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from .app import AlibabaScraperGUI

__all__ = ['AlibabaScraperGUI']
