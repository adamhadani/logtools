#!/usr/bin/env python
import logging

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from filterbots import *
from geoip import *
