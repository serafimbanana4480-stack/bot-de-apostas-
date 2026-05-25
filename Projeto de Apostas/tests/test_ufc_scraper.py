from datetime import datetime

import pytest
import requests_mock

from src.ingestion.ufc_scraper import UFCScraper


def test_scrape_event_list():
    """Tests completed event list scraping from ufcstats.com using mocked HTML responses."""
    scraper = UFCScraper()
    mock_html = """
    <html>
        <body>
            <tr class="b-statistics__table-row"></tr> <!-- Header -->
            <tr class="b-statistics__table-row">
                <td>
                    <a href="http://ufcstats.com/event-details/12345">UFC Fight Night: Blaydes vs. Aspinall</a>
                    <span class="b-statistics__date">July 23, 2022</span>
                </td>
                <td>London, England, United Kingdom</td>
            </tr>
        </body>
    </html>
    """
    
    with requests_mock.Mocker() as m:
        m.get("http://ufcstats.com/statistics/events/completed", text=mock_html)
        events = scraper.scrape_event_list()
        
        assert len(events) == 1
        event = events[0]
        assert event["event_name"] == "UFC Fight Night: Blaydes vs. Aspinall"
        assert event["event_url"] == "http://ufcstats.com/event-details/12345"
        assert event["event_date"] == datetime(2022, 7, 23)
        assert "London" in event["location"]

def test_scrape_fight_details():
    """Tests fight-level detailed strikes, takedowns, and method scraping using mocked HTML response."""
    scraper = UFCScraper()
    mock_html = """
    <html>
        <body>
            <a class="b-fight-details__person-link" href="http://ufcstats.com/fighter-details/a">Jon Jones</a>
            <a class="b-fight-details__person-link" href="http://ufcstats.com/fighter-details/b">Ciryl Gane</a>
            
            <i class="b-fight-details__person-status">W</i>
            <i class="b-fight-details__person-status">L</i>
            
            <i class="b-fight-details__text-item_first">Method: Submission</i>
            <i class="b-fight-details__text-item">Round: 1</i>
            <i class="b-fight-details__text-item">Time: 2:04</i>
            
            <table class="b-fight-details__table">
                <tr class="b-fight-details__table-row"></tr> <!-- Header -->
                <tr class="b-fight-details__table-row">
                    <td>Fighter</td>
                    <td>0 0</td> <!-- KD -->
                    <td>3 of 4 0 of 0</td> <!-- Sig Str -->
                    <td>3 of 4 0 of 0</td> <!-- Total Str -->
                    <td>1 of 1 0 of 0</td> <!-- TD -->
                    <td>Fighter</td>
                    <td>Fighter</td>
                    <td>1 0</td> <!-- Sub Att -->
                </tr>
            </table>
        </body>
    </html>
    """
    
    with requests_mock.Mocker() as m:
        m.get("http://ufcstats.com/fight-details/9999", text=mock_html)
        fight = scraper.scrape_fight_details("http://ufcstats.com/fight-details/9999")
        
        assert fight["fighter_a"] == "Jon Jones"
        assert fight["fighter_b"] == "Ciryl Gane"
        assert fight["winner"] == "Jon Jones"
        assert fight["method"] == "Submission"
        assert fight["end_round"] == 1
        assert fight["end_time"] == "2:04"
        
        # Test strikes and grappling parsed mappings
        kd = fight["striking_stats"]["kd"]
        assert kd["Jon Jones"] == 0
        assert kd["Ciryl Gane"] == 0
        
        sig_landed = fight["striking_stats"]["sig_str_landed"]
        assert sig_landed["Jon Jones"] == 3
        assert sig_landed["Ciryl Gane"] == 0
        
        td_landed = fight["grappling_stats"]["td_landed"]
        assert td_landed["Jon Jones"] == 1
        assert td_landed["Ciryl Gane"] == 0
        
        sub_attempts = fight["grappling_stats"]["sub_attempts"]
        assert sub_attempts["Jon Jones"] == 1
        assert sub_attempts["Ciryl Gane"] == 0

def test_scrape_fighter_history():
    """Tests career and biographical information parsing for fighters using mocked HTML response."""
    scraper = UFCScraper()
    mock_html = """
    <html>
        <body>
            <span class="b-content__title-highlight">Alex Pereira</span>
            
            <li class="b-list__box-list-item">Height: 6' 4"</li>
            <li class="b-list__box-list-item">Weight: 205 lbs.</li>
            <li class="b-list__box-list-item">Reach: 79"</li>
            <li class="b-list__box-list-item">Stance: Orthodox</li>
            
            <div class="b-list__info-box-left">
                <li class="b-list__box-list-item">SLpM: 5.11</li>
                <li class="b-list__box-list-item">Str. Acc.: 62%</li>
                <li class="b-list__box-list-item">SApM: 3.65</li>
                <li class="b-list__box-list-item">Str. Def: 50%</li>
                <li class="b-list__box-list-item">TD Avg.: 0.15</li>
                <li class="b-list__box-list-item">TD Acc.: 100%</li>
                <li class="b-list__box-list-item">TD Def.: 70%</li>
                <li class="b-list__box-list-item">Sub. Avg.: 0.0</li>
            </div>
            
            <tbody class="b-fight-details__table-body">
                <tr class="b-fight-details__table-row">
                    <td><i class="b-flag__text">win</i></td>
                    <td>
                        <a href="http://ufcstats.com/fighter-details/israel-adesanya">Israel Adesanya</a>
                        <a href="http://ufcstats.com/fighter-details/alex-pereira">Alex Pereira</a>
                    </td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td>
                        <a href="http://ufcstats.com/event-details/ufc281">UFC 281: Adesanya vs. Pereira</a>
                        <span class="b-statistics__date">Nov 12, 2022</span>
                    </td>
                    <td>KO/TKO</td>
                    <td>5</td>
                </tr>
            </tbody>
        </body>
    </html>
    """
    
    with requests_mock.Mocker() as m:
        m.get("http://ufcstats.com/fighter-details/alex-pereira", text=mock_html)
        fighter = scraper.scrape_fighter_history("http://ufcstats.com/fighter-details/alex-pereira")
        
        assert fighter["fighter_name"] == "Alex Pereira"
        assert fighter["biography"]["height"] == "6' 4\""
        assert fighter["biography"]["weight"] == "205 lbs."
        assert fighter["biography"]["reach"] == "79\""
        assert fighter["biography"]["stance"] == "Orthodox"
        
        # Test performance stats
        stats = fighter["career_statistics"]
        assert stats["slpm"] == pytest.approx(5.11)
        assert stats["striking_acc"] == pytest.approx(0.62)
        assert stats["sapm"] == pytest.approx(3.65)
        assert stats["striking_def"] == pytest.approx(0.50)
        assert stats["td_avg"] == pytest.approx(0.15)
        assert stats["td_acc"] == pytest.approx(1.0)
        assert stats["td_def"] == pytest.approx(0.70)
        assert stats["sub_avg"] == pytest.approx(0.0)

        # Test fights parsed list
        f = fighter["fights"]
        assert len(f) == 1
        assert f[0]["opponent_name"] == "Israel Adesanya"
        assert f[0]["opponent_url"] == "http://ufcstats.com/fighter-details/israel-adesanya"
        assert f[0]["result"] == "win"
        assert f[0]["method"] == "KO/TKO"
        assert f[0]["event_name"] == "UFC 281: Adesanya vs. Pereira"
        assert f[0]["event_date"].year == 2022
        assert f[0]["end_round"] == 5
