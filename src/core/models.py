from typing import Union
import numpy as np
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup


class Events(BaseModel):
    event_types: list = []
    player_names: list = []
    player_links: list = []
    minutes: list = []


class Features:
    def __init__(self, data: Union[list, np.ndarray], columns: list[str]):
        self.data = data
        self.columns: list[str] = columns

    def __getitem__(self, name: str):
        # todo: what should happen with an unknown key?
        return self.data[self.columns.index(name)]

    def add_features(self, values: np.array, names: list[str]):
        self.data = values
        self.columns = names

    def append_feature(self, value: Union[float, int, str], name: str):
        self.data.append(value)
        self.columns.append(name)


class MatchInfo:
    def __init__(self, home_squad: Features, home_bench: Features, away_squad: Features, away_bench: Features,
                 match_info: Features, home_events: Events, away_events: Events,
                 home_stats: dict, away_stats: dict, debug_info: Features):
        self.home_squad = home_squad
        self.away_squad = away_squad

        self.home_bench = home_bench
        self.away_bench = away_bench

        self.home_events = home_events
        self.away_events = away_events

        self.home_stats = home_stats
        self.away_stats = away_stats

        self.debug_info = debug_info
        self.match_info = match_info


class DetailsGetter:
    def __init__(self, url: str, basic_page_url: str, match_info: MatchInfo):
        self._basic_page_url = basic_page_url
        self._page_connector = PageConnector(url=url)
        self.match_info = match_info

    def get_data(self):
        pass

    def __call__(self):
        return self.get_data()


class PageConnector:
    def __init__(self, url: str):
        self.url = url
        self._verify_page_exists()
        self.page = requests.get(url=url)
        self.soup = BeautifulSoup(self.page.content, 'html.parser')

    def _verify_page_exists(self) -> bool:
        try:
            _ = requests.get(url=self.url)
        except ConnectionError:
            print(f'There is not such a page as {self.page}')