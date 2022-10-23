from typing import Optional, Union

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class MatchEvents(BaseModel):
    event_types: list[Optional[str]] = []
    player_names: list[Optional[str]] = []
    player_links: list[Optional[str]] = []
    minutes: list[Optional[str]] = []


class MatchStats(BaseModel):
    table_names: list[Optional[str]] = []
    tab_names: list[Optional[str]] = []
    table: list[Optional[pd.DataFrame]] = []

    class Config:
        arbitrary_types_allowed = True


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


class MatchData:
    def __init__(self):
        self.home_info = dict(
            squad=Features(data=[], columns=[]),
            bench=Features(data=[], columns=[]),
            events=MatchEvents(),
            stats=MatchStats(),
        )
        self.away_info = dict(
            squad=Features(data=[], columns=[]),
            bench=Features(data=[], columns=[]),
            events=MatchEvents(),
            stats=MatchStats(),
        )

        self.debug_info = Features(data=[], columns=[])
        self.match_info = Features(data=[], columns=[])

    @property
    def home_squad(self):
        return self.home_info["squad"]

    @home_squad.setter
    def home_squad(self, value: Features):
        self.home_info["squad"] = value

    @property
    def home_bench(self):
        return self.home_info["bench"]

    @home_bench.setter
    def home_bench(self, value: Features):
        self.home_info["bench"] = value

    @property
    def home_events(self):
        return self.home_info["events"]

    @home_events.setter
    def home_events(self, value: MatchEvents):
        self.home_info["events"] = value

    @property
    def home_stats(self):
        return self.home_info["stats"]

    @home_stats.setter
    def home_stats(self, value: MatchStats):
        self.home_info["stats"] = value

    @property
    def away_squad(self):
        return self.home_info["squad"]

    @away_squad.setter
    def away_squad(self, value: Features):
        self.away_info["squad"] = value

    @property
    def away_bench(self):
        return self.home_info["bench"]

    @away_bench.setter
    def away_bench(self, value: Features):
        self.away_info["bench"] = value

    @property
    def away_events(self):
        return self.home_info["events"]

    @away_events.setter
    def away_events(self, value: MatchEvents):
        self.away_info["events"] = value

    @property
    def away_stats(self):
        return self.home_info["stats"]

    @away_stats.setter
    def away_stats(self, value: MatchStats):
        self.away_info["stats"] = value


class DetailsGetter:
    def __init__(self, url: str, basic_page_url: str, match_info: MatchData):
        """
        Parameters
        ----------
        url: str
            url with match results, where match reports are also stored
        basic_page_url: str
            url of basic webpage to create links for PageConnector
        match_info: MatchData
            object that store extracted information
        """
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
        self.soup = BeautifulSoup(self.page.content, "html.parser")

    def _verify_page_exists(self) -> bool:
        try:
            _ = requests.get(url=self.url)
        except ConnectionError:
            print(f"There is not such a page as {self.page}")
