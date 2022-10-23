import itertools
from typing import Optional

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from src.core.models import (
    DetailsGetter,
    MatchData,
    MatchEvents,
    MatchStats,
    PageConnector,
)


class ReportLinksGetter:
    """Get links with match reports, where you can find all information from the match."""

    def __init__(self, date: str, url: str):
        """
        Parameters
        ----------
        date: str
            date from which links with match reports will be scraped
        url: str
            url with match results, where match reports are also stored
        """
        self._suffix = ":" + date
        self._page_connector = PageConnector(url=url + date)

    def get_links(self) -> dict:
        """Get all match report links available at the specific (date) url.

        Return
        ----------
        dict
            with tables containing match report links or empty if there are no tables available in page content
        """
        tables = self._get_match_tables(page_content=self._page_connector.soup)
        if tables:
            return self._get_match_links(tables=tables)
        else:
            return {}

    @staticmethod
    def _get_match_tables(page_content: BeautifulSoup) -> list[BeautifulSoup]:
        """Find all tables available at the specific url.

        Parameters
        ----------
        page_content: BeautifulSoup
            all available information on the webpage.

        Return
        ----------
        list[BeautifulSoup]
            list of all tables available currently in the page_content parameter
        """
        return page_content.findAll("table")

    def _get_match_links(self, tables: list[BeautifulSoup]) -> dict[str, list]:
        """Get all available match report links on the webpage.

        Parameters
        ----------
        tables: list[BeautifulSoup]
            list of all available tables on the webpage.

        Return
        ----------
        dict[str, list]
            with league:date information and list of available links
        """
        match_reports = {}
        for table in tables:
            match_reports = match_reports | self._get_match_report_link(table=table)

        return match_reports

    def _get_match_report_link(self, table: BeautifulSoup) -> dict[str, list]:
        """Get match report links from one table.

        Parameters
        ----------
        table: BeautifulSoup
            with information about matches, including match report links

        Return
        ----------
        dict[str, list]
            with league:date information and list of available links
        """
        links = table.findAll("a")

        league_name = links[0].text.replace(" ", "_")
        match_reports = [
            link.get("href") for link in links if "Match Report" in link.text
        ]

        return {league_name + self._suffix: match_reports}

    @staticmethod
    def _verify_tables_exists(tables: Optional[list[BeautifulSoup]]) -> bool:
        """Verify whether table exists"""
        if len(tables) == 0:
            return False
        else:
            return True


class EventsGetter(DetailsGetter):
    """Get events that appeared during match."""

    def __init__(self, url: str, basic_page_url: str, match_info: MatchData):
        super().__init__(url=url, basic_page_url=basic_page_url, match_info=match_info)
        self._event_names = ["event a", "event b"]
        self._first_team_events_contest = self._page_connector.soup.find_all(
            name="div", attrs={"class": self._event_names[0]}
        )
        self._second_team_events_contest = self._page_connector.soup.find_all(
            name="div", attrs={"class": self._event_names[1]}
        )
        self._events_missing = 0
        self._birth_date_missing = 0

    @property
    def events_missing(self):
        """Information whether event is missing."""
        return self._events_missing

    @property
    def birth_date_missing(self):
        """Information whether player birthdate is missing."""
        return self._birth_date_missing

    def _verify_event_names(self):
        """Verify whether html attributes have the same names as always."""
        if not self._first_team_events_contest and not self._second_team_events_contest:
            print(
                f"Missing events, verify names: {self._event_names[0]} and {self._event_names[1]}"
            )
            self._events_missing += 1

    def get_events(self):
        """Get events for both: home and away teams"""
        self._prepare_events(
            event_content=self._first_team_events_contest,
            events=self.match_info.home_events,
        )
        self._prepare_events(
            event_content=self._second_team_events_contest,
            events=self.match_info.away_events,
        )

    def _prepare_events(self, event_content: list[BeautifulSoup], events: MatchEvents):
        """Add available events to an object containing extracted information.

        Extract:
        1. event type - yellow card, red card, goal, substitute_in
        2. event player info - name, surname
        3. event time - time of an event

        with get event second player information about: assist, substitute is extracted

        Parameters
        ----------
        event_content: list[BeautifulSoup]
            all events information available in the match link
        events: MatchEvents
            object to store event information
        """
        events.event_types = self._get_event_types(event_content=event_content)
        events.player_names = self._get_event_player_name(event_content=event_content)
        events.player_links = self._get_event_player_link(event_content=event_content)
        events.minutes = self._get_event_time(event_content=event_content)

        self._get_event_second_player(
            events=events,
            basic_event_type="substitute_in",
            new_event_type="substitute_out",
        )

        self._get_event_second_player(
            events=events, basic_event_type="goal", new_event_type="assist"
        )

        events.player_names = list(itertools.chain(*events.player_names))

    @staticmethod
    def _get_event_second_player(
        events: MatchEvents, basic_event_type: str, new_event_type: str
    ):
        """Split events with two players (goal, substitute_in) on separated (assist, substitute_out).

        Parameters
        ----------
        events: MatchEvents
            object to store event information
        basic_event_type: str
            information whether we are looking for second player in goal event or substitute_in event
        new_event_type: str
            second player event name: assist, substitute_out
        """
        substitutes_indices = np.where(
            np.array(events.event_types) == basic_event_type
        )[0]
        for idx in substitutes_indices:
            if len(events.player_names[idx]) > 1:
                EventsGetter._split_two_players(
                    events=events, variable="player_names", idx=idx
                )
                EventsGetter._split_two_players(
                    events=events, variable="player_links", idx=idx
                )

                events.minutes.append(events.minutes[idx])
                events.event_types.append(new_event_type)

    @staticmethod
    def _split_two_players(events: MatchEvents, variable: str, idx: int):
        """Split two players in event into separated events (e.g. goal -> goal and assist)."""
        events_variable_values = getattr(events, variable)
        substitute_player_out = events_variable_values[idx][1]
        events_variable_values[idx] = events_variable_values[idx][:1]
        setattr(events, variable, events_variable_values)

        getattr(events, variable).append([substitute_player_out])

    @staticmethod
    def _get_event_time(event_content: list[BeautifulSoup]) -> list[str]:
        """Get information in which minute an events have occurred."""
        return [event.get_text(strip=True).split("’")[0] for event in event_content]

    @staticmethod
    def _get_event_types(event_content: list[BeautifulSoup]) -> list[str]:
        """Get a type of events: yellow card, red card, goal, substitute_in."""
        return [
            event.find("div", {"class", "event_icon"}).get("class")[1]
            for event in event_content
        ]

    @staticmethod
    def _get_event_player_name(event_content: list[BeautifulSoup]) -> list[list]:
        """Get name and surname for player in events."""
        return [
            [player.text for player in event.findAll("a")] for event in event_content
        ]

    @staticmethod
    def _get_event_player_link(event_content: list[BeautifulSoup]) -> list[list]:
        """Get link for player in events."""
        return [
            [player.get("href") for player in event.findAll("a")]
            for event in event_content
        ]


class SquadsGetter(DetailsGetter):
    def __init__(self, url: str, basic_page_url: str, match_info: MatchData):
        super().__init__(url=url, basic_page_url=basic_page_url, match_info=match_info)
        self._lineups = self._page_connector.soup.find_all("div", {"class": "lineup"})
        self._home_squad = None
        self._away_squad = None
        self._lineups_missing = 0

    @property
    def lineups_missing(self):
        """Information whether lineups are missing."""
        return self._lineups_missing

    def _lineups_exists(self):
        """Verify whether lineup exists and add information to match_info."""
        if not self._lineups:
            self._lineups_missing += 1
            lineups_missing = 1
        else:
            lineups_missing = 0
            self._home_squad = pd.read_html(str(self._lineups[0]))
            self._away_squad = pd.read_html(str(self._lineups[1]))

        self.match_info.debug_info.append_feature(
            value=lineups_missing, name="lineups_missing"
        )

    def get_teams_info(self):
        """Get information about squads."""
        self._lineups_exists()

        if not self.match_info.debug_info["lineups_missing"]:
            self._separate_squad(team_type="home")
            self._separate_squad(team_type="away")

    def _separate_squad(self, team_type: str):
        """Separate first team players with bench ones.

        Parameters
        ----------
        team_type: str
            information whether split squads for away or home team
        """
        columns = ["shirt_number", "player"]

        getattr(self.match_info, team_type + "_squad").add_features(
            values=getattr(self, "_" + team_type + "_squad")[:11], names=columns
        )

        getattr(self.match_info, team_type + "_bench").add_features(
            values=getattr(self, "_" + team_type + "_bench")[12:], names=columns
        )


class StatsGetter(DetailsGetter):
    def __init__(self, url: str, basic_page_url: str, match_info: MatchData):
        super().__init__(url=url, basic_page_url=basic_page_url, match_info=match_info)
        self._tables = self._page_connector.soup.find_all(
            "div", {"class": "table_container"}
        )
        self._table_names = self._page_connector.soup.find_all("h2")
        self._tab_names = self._page_connector.soup.find_all(
            "a", {"class": "sr_preset"}
        )
        self._stats_missing = 0
        self._table_names_missing = 0
        self._tab_names_missing = 0

    @property
    def stats_missing(self):
        """Information whether stats are missing."""
        return self._stats_missing

    @property
    def table_names_missing(self):
        """Information whether table names with stats are different than specified in __init__."""
        return self._table_names_missing

    @property
    def tab_names_missing(self):
        """Information whether tab names with stats are different than specified in __init__."""
        return self._table_names_missing

    def _stats_exists(self):
        """Verify whether stats exists and add information to match_info."""
        if not self._tables:
            self._stats_missing += 1
            stats_missing = 1
        else:
            stats_missing = 0
            self._home_squad = pd.read_html(str(self._tables[0]))
            self._away_squad = pd.read_html(str(self._tables[1]))

        self.match_info.debug_info.append_feature(
            value=stats_missing, name="stats_missing"
        )

    def _table_names_exists(self):
        """Verify whether table names with stats are different than specified in __init__
        and add information to match_info.
        """
        if not self._table_names:
            self._table_names_missing += 1
            table_names_missing = 1
        else:
            table_names_missing = 0
            self._clean_table_names()

        self.match_info.debug_info.append_feature(
            value=table_names_missing, name="table_names_missing"
        )
        self.match_info.debug_info.append_feature(
            value=self._table_names, name="table_names"
        )

    def _tab_names_exists(self):
        """Verify whether tab names with stats are different than specified in __init__
        and add information to match_info.
        """
        if not self._tab_names:
            self._tab_names_missing += 1
            tab_names_missing = 1
        else:
            tab_names_missing = 0
            self._clean_tab_names()

        self.match_info.debug_info.append_feature(
            value=tab_names_missing, name="tab_names_missing"
        )
        self.match_info.debug_info.append_feature(
            value=self._tab_names, name="tab_names"
        )

    def _clean_table_names(self):
        """Select table names with 'Stats' or 'Shots' in name. Also exclude names with 'Team Stats' in it."""
        self._table_names = [
            header.text
            for header in self._table_names
            if (("Stats" in header.text) or ("Shots" in header.text))
            & ("Team Stats" not in header.text)
        ]

    def _clean_tab_names(self):
        """Get only a text from tab names."""
        self._tab_names = [name.text for name in self._tab_names]

    def get_stats(self):
        """Verify whether components exists, their length is proper and save extracted information."""
        self._stats_exists()
        self._table_names_exists()
        self._tab_names_exists()

        self._verify_components_length(team_type="home")

    def _verify_components_length(self, team_type: str):
        """Separate first team players with bench ones.

        Parameters
        ----------
        team_type: str
            information whether split squads for away or home team
        """
        if len(self._tables) == len(self._table_names):
            self.convert_tables(team_type=team_type)
            self.match_info.debug_info.append_feature(
                value=0, name="stats_components_length_miss"
            )
        else:
            if len(self._tables) != len(self._table_names):
                print("Different length of stats components: tables and table names")
            if len(self._tab_names) != len(self._table_names):
                print("Different length of stats components: tab names and table names")
            self.match_info.debug_info.append_feature(
                value=1, name="stats_components_length_miss"
            )

    def convert_tables(self, team_type: str):
        """Assign table variables to match_info stats property.

        Tab names append only in case they exist.

        Parameters
        ----------
        team_type: str
            information whether set attribute for away or home team
        """
        team_stats = {"table_names": [], "tab_names": [], "table": []}
        for idx, table in enumerate(self._tables):
            team_stats["table"].append(self._clean_table(self._tables[idx]))
            team_stats["table_names"].append(self._table_names[idx])
            if self._tab_names:
                team_stats["tab_names"].append(self._tab_names[idx])
        setattr(self.match_info, team_type + "_stats", MatchStats.parse_obj(team_stats))

    @staticmethod
    def _clean_table(table):
        """Clean table scrapped from webpage."""
        # todo remove multiple index in columns and remove last row ('14 players' value)
        # todo also veirfy whether in all cases (2 tables and more) it look the same
        return pd.read_html(str(table))[0]
