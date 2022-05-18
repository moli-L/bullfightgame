# -*- coding: utf-8 -*-

import requests
import json

from core.error import *

from core.utils import get_logger
logger = get_logger()


def _get_error(status_code, msg):
    if status_code == 404:
        return NotFoundError(msg)
    elif 400 <= status_code < 500:
        return ClientError(msg)
    else:
        return ServerError(msg)


def _handle_response(api_url, response):
    if 200 <= response.status_code < 300:
        return
    else:
        logger.error(
            "[HTTP]接口请求异常，请求连接: %s, error: %s, 返回内容: %s".format(
                api_url, 
                response.status_code, 
                response.content
            )
        )
        error_message = json.loads(response.content)['message']
        error = _get_error(response.status_code, error_message)
        raise error


class Http:
    def __init__(self, token, time_out):
        self.token = token
        self.timeout = time_out

    def get(self, api_url, params=None, data=None):
        headers = {
            "Authorization": "Bot " + self.token,
            "User-Agent": "BullPythonSDK",
        }
        logger.debug("[HTTP]http get headers: %s, api_url: %s" % (headers, api_url))
        response = requests.get(
            url=api_url,
            params=params,
            json=data,
            timeout=self.timeout,
            headers=headers,
        )
        _handle_response(api_url, response)
        return response

    def post(self, api_url, data=None, params=None):
        headers = {
            "Authorization": "Bot " + self.token,
            "User-Agent": "BullPythonSDK",
        }
        logger.debug(
            "[HTTP]http post headers: %s, api_url: %s, data: %s"
            % (headers, api_url, data)
        )
        response = requests.post(
            url=api_url,
            params=params,
            json=data,
            timeout=self.timeout,
            headers=headers,
        )
        _handle_response(api_url, response)
        return response


