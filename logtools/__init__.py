#!/usr/bin/env python
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ........................................ NOTICE
#
# This file has been derived and modified from a source licensed under Apache Version 2.0.
# See files NOTICE and README.md for more details.
#
# ........................................ ******


import logging

## This might be specific to Ubuntu+Python3: +++++++++++++++++++++++++++++++++
## Had to:
##     sudo pip3 install mysql-connector (not sure necessary)
##     pip3 install PyMySQL

import pymysql
pymysql.install_as_MySQLdb()
## END OF SPECIFIC TO Ubuntu+Python3:        +++++++++++++++++++++++++++++++++


from ._config import *
from ._filterbots import *
from ._flattenjson import *
from ._geoip import *
from ._join import *
from ._merge import *
from ._parse import *
from ._urlparse import *
from ._plot import *
from ._qps import *
from ._sample import *
from ._filter import *
from ._tail import *
from ._sumstat import *
from ._serve import *

