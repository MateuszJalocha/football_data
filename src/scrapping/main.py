import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.core.models import MatchData
from src.scrapping.data_getters import EventsGetter, SquadsGetter, StatsGetter

if __name__ == "__main__":
    dotenv_path = (
        Path(os.path.abspath(os.path.dirname(__file__))) / ".." / ".." / ".env"
    )
    load_dotenv(dotenv_path=dotenv_path)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--match_data_basic_url",
        help="Basic link for scrapping match info",
        default=os.environ.get("MATCH_DATA_BASIC_URL"),
    )
    parser.add_argument(
        "--match_data_reports_url",
        help="Link with tables containing match report links",
        default=os.environ.get("MATCH_DATA_REPORTS_URL"),
    )
    parser.add_argument(
        "--start_date_scrapping",
        help="Start date for scrapping, increment about 1",
        default=os.environ.get("START_DATE_SCRAPPING"),
    )
    parser.add_argument("--logging_level", default=os.environ.get("LOGGING_LEVEL"))
    parser.add_argument("--logging_format", default=os.environ.get("LOGGING_FORMAT"))
    parser.add_argument(
        "--logging_date_format", default=os.environ.get("LOGGING_DATE_FORMAT")
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=eval(args.logging_level),  # nosec
        format=args.logging_format,
        datefmt=args.logging_date_format,
    )
    logger = logging.getLogger(__name__)

    # match_links_getter = ReportLinksGetter(
    #     date=args.start_date_scrapping, url=args.match_data_reports_url
    # )
    # res = match_links_getter.get_links()
    res = {
        "Premier_League:2011-08-13": [
            "/en/matches/f2922720/Blackburn-Rovers-Wolverhampton-Wanderers-August-13-2011-Premier-League"
        ]
    }

    match_info = MatchData()

    events_getter = EventsGetter(
        url=args.match_data_basic_url + res["Premier_League:2011-08-13"][0],
        basic_page_url=args.match_data_basic_url,
        match_info=match_info,
    )
    events_getter.get_events()
    print(match_info.home_events)

    squads_getter = SquadsGetter(
        url=args.match_data_basic_url + res["Premier_League:2011-08-13"][0],
        basic_page_url=args.match_data_basic_url,
        match_info=match_info,
    )
    squads_getter.get_teams_info()
    print(match_info.home_squad.data)
    print(match_info.home_bench.data)
    print(args.match_data_basic_url + res["Premier_League:2011-08-13"][0])

    stats_getter = StatsGetter(
        url="https://fbref.com/en/matches/f2922720/Blackburn-Rovers-Wolverhampton-Wanderers-August-13-2011-Premier-League",
        basic_page_url="https://fbref.com",
        match_info=match_info,
    )
    stats_getter.get_stats()
    print(match_info.home_stats)
