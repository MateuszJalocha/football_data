import argparse
from data_getters import MatchReportLinksGetter, EventsGetter
from src.core.models import MatchInfo, Features, Events
import numpy as np
import logging
from dotenv import load_dotenv
import os
from pathlib import Path

if __name__ == '__main__':
    dotenv_path = Path(os.path.abspath(os.path.dirname(__file__))) / '..' / '..' / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    parser = argparse.ArgumentParser()
    parser.add_argument("--match_data_basic_url", help='Basic link for scrapping match info', default=os.environ.get('MATCH_DATA_BASIC_URL'))
    parser.add_argument('--match_data_reports_url', help='Link with tables containing match report links', default=os.environ.get('MATCH_DATA_REPORTS_URL'))
    parser.add_argument('--start_date_scrapping', help='Start date for scrapping, increment about 1', default=os.environ.get('START_DATE_SCRAPPING'))
    parser.add_argument('--logging_level', default=os.environ.get('LOGGING_LEVEL'))
    parser.add_argument('--logging_format', default=os.environ.get('LOGGING_FORMAT'))
    parser.add_argument('--logging_date_format', default=os.environ.get('LOGGING_DATE_FORMAT'))

    args = parser.parse_args()

    logging.basicConfig(
        level=eval(args.logging_level),
        format=args.logging_format,
        datefmt=args.logging_date_format
    )
    logger = logging.getLogger(__name__)

    match_links_getter = MatchReportLinksGetter(date='2011-08-13', url='https://fbref.com/en/matches')

    match_links_getter = MatchReportLinksGetter(date=args.start_date_scrapping, url=args.match_data_reports_url)
    res = match_links_getter.get_links()

    match_info = MatchInfo(
        home_squad=Features(data=np.array([]), columns=[]),
        home_bench=Features(data=np.array([]), columns=[]),
        away_squad=Features(data=np.array([]), columns=[]),
        away_bench=Features(data=np.array([]), columns=[]),
        match_info=Features(data=np.array([]), columns=[]),
        debug_info=Features(data=[], columns=[]),
        home_events=Events(),
        away_events=Events(),
        home_stats={},
        away_stats={},
    )

    events_getter = EventsGetter(
        url=args.match_data_basic_url + res['Premier_League:2011-08-13'][0],
        basic_page_url=args.match_data_basic_url,
        match_info=match_info
    )
    events_getter.get_events()