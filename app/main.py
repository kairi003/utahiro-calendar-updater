import os
import re
from datetime import datetime, timedelta, timezone, date
from logging import getLogger, basicConfig, INFO, DEBUG

import requests
from playwright.sync_api import sync_playwright, Page

JST = timezone(timedelta(hours=+9), 'JST')
USER_AGENT = os.environ['USER_AGENT']
SERVER_URL = os.environ['SERVER_URL']
SECRET_KEY = os.environ['SECRET_KEY']
EVENT_TITLE = os.environ['EVENT_TITLE']
PAGE_URL = os.environ['PAGE_URL']

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
if LOG_LEVEL not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
    LOG_LEVEL = 'INFO'
basicConfig(level=LOG_LEVEL)
logger = getLogger(__name__)

def close_dialog(page: Page):
    page.evaluate('''() => {
        [...document.querySelectorAll('.native-text')]
        .find(n=>n.textContent==JSON.parse('"\\udb86\\udd05"'))?.click()
    }''')


def load_more(page: Page):
    child_num = len(page.query_selector_all('[data-successful-render-id]>*'))
    page.evaluate('''() => {
        window.scrollTo(0, document.body.scrollHeight);
    }''')
    page.wait_for_selector(
        f'[data-successful-render-id]>:nth-child({child_num+10})')


def send_event(event_date: date, event_title: str):
    resp = requests.post(SERVER_URL, json={
        'key': SECRET_KEY,
        'content': {
            'title': event_title,
            'date': event_date.isoformat()
        }
    })
    resp.raise_for_status()
    logger.info(resp.text)


def main():
    logger.debug('start main')
    with sync_playwright() as p:
        logger.debug('start playwright')
        browser = p.chromium.launch(headless=True)
        context_params = {
            'user_agent': USER_AGENT,
            'locale': 'ja-JP'
        }
        context = browser.new_context(**context_params)
        page = context.new_page()
        logger.debug('start page')

        # goto page and wait for load
        page.goto(PAGE_URL, wait_until="domcontentloaded")
        page.wait_for_selector('[data-successful-render-id]>:nth-child(30)')
        logger.debug('page loaded')

        # get text elements
        navite_text_elements = page.query_selector_all(
            '[data-successful-render-id] .native-text')
        post_dt = None
        for element in navite_text_elements:
            text = element.text_content()
            logger.debug([text])

            # post date element
            m: re.Match
            if m := re.match(r'^(?P<num>\d+)(?P<unit>秒|分|時間|日)前..$', text):
                post_dt = datetime.now(JST)
                num = int(m['num'])
                match m['unit']:
                    case '秒':
                        post_dt -= timedelta(seconds=num)
                    case '分':
                        post_dt -= timedelta(minutes=num)
                    case '時間':
                        post_dt -= timedelta(hours=num)
                    case '日':
                        post_dt -= timedelta(days=num)
                continue

            elif m := re.match(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<date>\d+)..$', text):
                date_ = map(int, m.group('year', 'month', 'date'))
                post_dt = datetime(*date_, tzinfo=JST)
                continue
            
            # text element
            elif post_dt is not None:
                logger.info(f'{post_dt.isoformat()}: {text}')

                # event post text
                if m := re.search(r'(?P<month>\d+)月(?P<date>\d+)日.*室料半額', text):
                    month, date_ = map(int, m.group('month', 'date'))
                    event_date = date(post_dt.year, month, date_)
                    if event_date < post_dt.date():
                        event_date = date(post_dt.year+1, month, date_)
                    logger.info(event_date)
                    send_event(event_date, EVENT_TITLE)
                    break
                
                post_dt = None

        browser.close()

if __name__ == '__main__':
    main()
