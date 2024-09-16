import datetime as dt
import os
import re
import sys
from distutils.util import strtobool
from logging import basicConfig, getLogger

from retry import retry
from playwright.sync_api import Page, sync_playwright
from register import register_event

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

@retry(tries=5, delay=5)
def get_navite_text_elements(page: Page):
    # goto page and wait for load
    
    page.goto(PAGE_URL, wait_until="domcontentloaded")
    page.wait_for_selector('[data-successful-render-id]>:nth-child(30)', timeout=15000)
    logger.debug('page loaded')

    # get text elements
    navite_text_elements = page.query_selector_all(
        '[data-successful-render-id] .native-text')
    
    return navite_text_elements


def main():
    logger.debug('start main')
    with sync_playwright() as p:
        logger.debug('start playwright')
        browser = p.chromium.launch(headless=HEADLESS)
        context_params = {
            'user_agent': USER_AGENT,
            'locale': 'ja-JP'
        }
        context = browser.new_context(**context_params)
        page = context.new_page()
        logger.debug('start page')

        post_dt = None
        for element in get_navite_text_elements(page):
            text = element.text_content()
            logger.debug([text])

            # post date element
            m: re.Match
            if m := re.match(r'^(?P<num>\d+)(?P<unit>秒|分|時間|日)前..$', text):
                post_dt = dt.datetime.now(JST)
                num = int(m['num'])
                match m['unit']:
                    case '秒':
                        post_dt -= dt.timedelta(seconds=num)
                    case '分':
                        post_dt -= dt.timedelta(minutes=num)
                    case '時間':
                        post_dt -= dt.timedelta(hours=num)
                    case '日':
                        post_dt -= dt.timedelta(days=num)
                continue

            elif m := re.match(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<date>\d+)..$', text):
                date_ = map(int, m.group('year', 'month', 'date'))
                post_dt = dt.datetime(*date_, tzinfo=JST)
                continue

            # text element
            elif post_dt is not None:
                logger.info(f'{post_dt.isoformat()}: {text}')

                # event post text
                if m := re.search(r'(?P<month>\d+)月(?P<date>\d+)日.*室料半額', text):
                    month, date_ = map(int, m.group('month', 'date'))
                    event_date = dt.date(post_dt.year, month, date_)
                    if event_date < post_dt.date():
                        event_date = dt.date(post_dt.year+1, month, date_)
                    logger.info(event_date)
                    update_event_log(event_date)
                    break
        else:
            raise Exception('event not found')

        browser.close()


if __name__ == '__main__':
    main()
