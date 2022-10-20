from typing import Optional
import itertools
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from src.core.models import DetailsGetter, PageConnector, MatchInfo, Events


class MatchReportLinksGetter:
    """Get links with match reports, where you can find all the information from the match."""

    def __init__(self, date: str, url: str):
        """
        Parameters
        ----------
        date: str
            date from which links with match reports will be scraped
        url: str
            url with match results, where match reports are also stored
        """
        self._suffix = ':' + date
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
        return page_content.findAll('table')

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
        links = table.findAll('a')

        league_name = links[0].text.replace(' ', '_')
        match_reports = [link.get('href') for link in links if 'Match Report' in link.text]

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

    def __init__(self, url: str, basic_page_url: str, match_info: MatchInfo):
        """
        Parameters
        ----------
        url: str
            url with match results, where match reports are also stored
        basic_page_url: str
            url of basic webpage to create links for PageConnector
        match_info: MatchInfo
            object that store extracted information
        """
        super().__init__(url=url, basic_page_url=basic_page_url, match_info=match_info)
        self._event_names = ['event a', 'event b']
        self._first_team_events_contest = self._page_connector.soup.find_all(name='div',
                                                                             attrs={'class': self._event_names[0]})
        self._second_team_events_contest = self._page_connector.soup.find_all(name='div',
                                                                              attrs={'class': self._event_names[1]})
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
            print(f'Missing events, verify names: {self._event_names[0]} and {self._event_names[1]}')
            self._events_missing += 1

    def get_events(self):
        """Get events for both: home and away teams"""
        self._prepare_events(event_content=self._first_team_events_contest, events=self.match_info.home_events)
        self._prepare_events(event_content=self._second_team_events_contest, events=self.match_info.away_events)

    def _prepare_events(self, event_content: list[BeautifulSoup], events: Events):
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
        events: Events
            object to store event information
        """
        events.event_types = self._get_event_types(event_content=event_content)
        events.player_names = self._get_event_player_name(event_content=event_content)
        events.player_links = self._get_event_player_link(event_content=event_content)
        events.minutes = self._get_event_time(event_content=event_content)

        self._get_event_second_player(
            events=events,
            basic_event_type='substitute_in',
            new_event_type='substitute_out'
        )

        self._get_event_second_player(
            events=events,
            basic_event_type='goal',
            new_event_type='assist'
        )

        events.player_names = list(itertools.chain(*events.player_names))

    @staticmethod
    def _get_event_second_player(events: Events, basic_event_type: str, new_event_type: str):
        """Split events with two players (goal, substitute_in) on separated (assist, substitute_out).

        Parameters
        ----------
        events: Events
            object to store event information
        basic_event_type: str
            information whether we are looking for second player in goal event or substitute_in event
        new_event_type: str
            second player event name: assist, substitute_out
        """
        substitutes_indices = np.where(np.array(events.event_types) == basic_event_type)[0]
        for idx in substitutes_indices:
            if len(events.player_names[idx]) > 1:
                substitute_player_out = events.player_names[idx][1] #todo add method to split players
                events.player_names[idx] = events.player_names[idx][:1]

                substitute_player_link_out = events.player_links[idx][1]
                events.player_links[idx] = events.player_links[idx][:1]

                events.minutes.append(events.minutes[idx])
                events.player_names.append([substitute_player_out])
                events.player_links.append([substitute_player_link_out])
                events.event_types.append(new_event_type)

    def _split_two_players(self):
        return 0

    @staticmethod
    def _get_event_time(event_content: list[BeautifulSoup]) -> list[str]:
        """Get information in which minute an events have occurred."""
        return [event.get_text(strip=True).split('’')[0] for event in event_content]

    @staticmethod
    def _get_event_types(event_content: list[BeautifulSoup]) -> list[str]:
        """Get a type of events: yellow card, red card, goal, substitute_in."""
        return [event.find('div', {'class', 'event_icon'}).get('class')[1] for event in event_content]

    @staticmethod
    def _get_event_player_name(event_content: list[BeautifulSoup]) -> list[list]:
        """Get name and surname for player in events."""
        return [[player.text for player in event.findAll('a')] for event in event_content]

    @staticmethod
    def _get_event_player_link(event_content: list[BeautifulSoup]) -> list[list]:
        """Get link for player in events."""
        return [[player.get('href') for player in event.findAll('a')] for event in event_content]
