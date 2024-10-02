#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime as dt
from itertools import count
import os
import re
import sys
from distutils.util import strtobool
from logging import basicConfig, getLogger

from playwright.sync_api._generated import Route
from retry import retry
from playwright.sync_api import Page, sync_playwright
from register import register_event
from retry import retry

JST = dt.timezone(dt.timedelta(hours=+9), 'JST')
USER_AGENT = os.environ['USER_AGENT']
PAGE_URL = os.environ['PAGE_URL']
EVENT_LOG = 'event.log'

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
if LOG_LEVEL not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
    LOG_LEVEL = 'INFO'
basicConfig(level=LOG_LEVEL, stream=sys.stderr)
logger = getLogger(__name__)

HEADLESS = bool(strtobool(os.getenv("HEADLESS", "true")))



def update_event_log(event_date: dt.date) -> bool:
    with open(EVENT_LOG, 'r+') as f:
        try:
            last = f.readlines().pop()
        except IndexError:
            last = ''
        currnt = event_date.isoformat()
        if last < currnt:
            f.write(currnt+'\n')
            event = register_event(event_date)
            logger.info(f'event registered: {event}')
        else:
            logger.info('event already registered')



def main():
    logger.debug('start main')
    with sync_playwright() as p:
        logger.debug('start playwright')
        browser = p.chromium.launch(headless=HEADLESS)
        context_params = {
            'user_agent': USER_AGENT,
            'locale': 'ja-JP',
            'viewport': { 'width': 500, 'height': 5000 }
        }
        context = browser.new_context(**context_params)
        context.route("**/*", lambda route: route.abort() if route.request.resource_type in "image" else route.continue_())
        page = context.new_page()
        logger.debug('start page')

        page.goto(PAGE_URL, wait_until="domcontentloaded")

        page.wait_for_selector('[aria-label="閉じる"]').click()

        for i in range(1, 20):
            selector = f'[aria-posinset="{i}"] [data-ad-preview="message"]'
            el = page.wait_for_selector(selector)
            text = el.text_content()
            logger.debug([text])
            el.evaluate('el=>el.scrollIntoView(true)')

        browser.close()


if __name__ == '__main__':
    main()
