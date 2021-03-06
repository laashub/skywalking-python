#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import traceback

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    # noinspection PyBroadException
    try:
        from urllib.request import OpenerDirector
        from urllib.error import HTTPError

        _open = OpenerDirector.open

        def _sw_open(this: OpenerDirector, fullurl, data, timeout):
            context = get_context()
            with context.new_exit_span(op=fullurl.selector, peer=fullurl.host) as span:
                span.layer = Layer.Http
                span.component = Component.Http
                try:
                    res = _open(this, fullurl, data, timeout)
                    span.tag(Tag(key=tags.HttpMethod, val=fullurl.get_method()))
                    span.tag(Tag(key=tags.HttpUrl, val=fullurl.full_url))
                    span.tag(Tag(key=tags.HttpStatus, val=res.code))
                    if res.code >= 400:
                        span.error_occurred = True
                except HTTPError as e:
                    span.raised()
                    raise e
                return res

        OpenerDirector.open = _sw_open
    except Exception:
        logger.warning('failed to install plugin %s', __name__)
        traceback.print_exc()
