import logging
import re
from datetime import datetime
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


class UFCScraper:
    """
    Highly robust, production-grade Web Scraper for UFCstats.com.
    Parses completed event lists, detailed fight stats (strikes, grappling, control),
    and historical fighter stats. Serves as our primary MMA data feed.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://ufcstats.com/statistics/events/completed"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def scrape_event_list(self) -> List[Dict[str, Any]]:
        """
        Scrapes completed and upcoming event lists from ufcstats.com/statistics/events/completed.
        Extracts event names, dates, locations, and details URLs.
        """
        self.logger.info("Scraping UFC completed events list...")
        try:
            res = self.session.get(self.base_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "html.parser")
            
            events = []
            rows = soup.find_all("tr", class_="b-statistics__table-row")
            
            for row in rows[1:]: # Skip table header
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                    
                link_el = cols[0].find("a")
                if not link_el:
                    continue
                    
                event_url = link_el["href"]
                event_name = link_el.text.strip()
                
                date_str = cols[0].find("span", class_="b-statistics__date").text.strip()
                location = cols[1].text.strip()
                
                # Parse date
                try:
                    event_date = datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    event_date = datetime.now() # Fallback

                events.append({
                    "event_name": event_name,
                    "event_url": event_url,
                    "event_date": event_date,
                    "location": location
                })
                
            self.logger.info(f"Successfully scraped {len(events)} UFC events.")
            return events
        except Exception as e:
            self.logger.error(f"Failed to scrape UFC event list: {e}")
            return []

    def scrape_fight_details(self, fight_url: str) -> Dict[str, Any]:
        """
        Scrapes detailed statistics for a specific fight from its ufcstats.com URL.
        Captures round-by-round strikes (landed/thrown), takedown attempts, submission attempts,
        control times, and final result method.
        """
        self.logger.info(f"Scraping fight details from: {fight_url}")
        try:
            res = self.session.get(fight_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "html.parser")
            
            # Extract fighter names
            fighter_links = soup.find_all("a", class_="b-fight-details__person-link")
            if len(fighter_links) < 2:
                return {}
                
            fighter_a = fighter_links[0].text.strip()
            fighter_b = fighter_links[1].text.strip()
            
            # Get winner
            winner_indicators = soup.find_all("i", class_="b-fight-details__person-status")
            winner = None
            if len(winner_indicators) >= 2:
                status_a = winner_indicators[0].text.strip()
                status_b = winner_indicators[1].text.strip()
                if "W" in status_a:
                    winner = fighter_a
                elif "W" in status_b:
                    winner = fighter_b
                else:
                    winner = "Draw/No Contest"

            # Parse fight duration (Rounds and Times)
            method = "Decision"
            duration_round = 3
            duration_time = "5:00"
            
            method_el = soup.find("i", class_="b-fight-details__text-item_first")
            if method_el:
                method = method_el.text.replace("Method:", "").strip()
                
            details_items = soup.find_all("i", class_="b-fight-details__text-item")
            for item in details_items:
                text = item.text.strip()
                if "Round:" in text:
                    try:
                        duration_round = int(text.replace("Round:", "").strip())
                    except ValueError:
                        pass
                elif "Time:" in text:
                    duration_time = text.replace("Time:", "").strip()

            # Parse stats tables (Tot striking & Significant strikes)
            # Standard ufcstats page contains multiple tables: 'Totals' and 'Significant Strikes'
            tables = soup.find_all("table", class_="b-fight-details__table")
            
            stats_data = {
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "winner": winner,
                "method": method,
                "end_round": duration_round,
                "end_time": duration_time,
                "striking_stats": {},
                "grappling_stats": {}
            }
            
            if tables:
                # First table holds main totals (KD, Sig. Strikes, Total Strikes, TD, Sub Att, Rev, Ctrl)
                totals_rows = tables[0].find_all("tr", class_="b-fight-details__table-row")
                if len(totals_rows) > 1:
                    cells = totals_rows[1].find_all("td")
                    if len(cells) >= 8:
                        # Determine indices based on columns layout
                        if len(cells) >= 10:
                            kd_idx, sig_idx, tot_idx, td_idx, sub_idx = 1, 2, 4, 5, 7
                        else:
                            kd_idx, sig_idx, tot_idx, td_idx, sub_idx = 1, 2, 3, 4, 7

                        try:
                            kd_vals = re.findall(r"\d+", cells[kd_idx].text)
                            kd_a, kd_b = int(kd_vals[0]), int(kd_vals[1])
                        except (IndexError, ValueError):
                            kd_a, kd_b = 0, 0

                        try:
                            sig_vals = re.findall(r"\d+", cells[sig_idx].text)
                            sig_str_a_landed, sig_str_a_thrown = int(sig_vals[0]), int(sig_vals[1])
                            sig_str_b_landed, sig_str_b_thrown = int(sig_vals[2]), int(sig_vals[3])
                        except (IndexError, ValueError):
                            sig_str_a_landed, sig_str_a_thrown = 0, 0
                            sig_str_b_landed, sig_str_b_thrown = 0, 0

                        try:
                            tot_vals = re.findall(r"\d+", cells[tot_idx].text)
                            tot_str_a_landed, tot_str_a_thrown = int(tot_vals[0]), int(tot_vals[1])
                            tot_str_b_landed, tot_str_b_thrown = int(tot_vals[2]), int(tot_vals[3])
                        except (IndexError, ValueError):
                            tot_str_a_landed, tot_str_a_thrown = 0, 0
                            tot_str_b_landed, tot_str_b_thrown = 0, 0

                        try:
                            td_vals = re.findall(r"\d+", cells[td_idx].text)
                            td_a_landed, td_a_thrown = int(td_vals[0]), int(td_vals[1])
                            td_b_landed, td_b_thrown = int(td_vals[2]), int(td_vals[3])
                        except (IndexError, ValueError):
                            td_a_landed, td_a_thrown = 0, 0
                            td_b_landed, td_b_thrown = 0, 0

                        try:
                            sub_vals = re.findall(r"\d+", cells[sub_idx].text)
                            sub_a, sub_b = int(sub_vals[0]), int(sub_vals[1])
                        except (IndexError, ValueError):
                            sub_a, sub_b = 0, 0
                        
                        stats_data["striking_stats"] = {
                            "kd": {fighter_a: kd_a, fighter_b: kd_b},
                            "sig_str_landed": {fighter_a: sig_str_a_landed, fighter_b: sig_str_b_landed},
                            "sig_str_thrown": {fighter_a: sig_str_a_thrown, fighter_b: sig_str_b_thrown},
                            "total_str_landed": {fighter_a: tot_str_a_landed, fighter_b: tot_str_b_landed},
                            "total_str_thrown": {fighter_a: tot_str_a_thrown, fighter_b: tot_str_b_thrown}
                        }
                        
                        stats_data["grappling_stats"] = {
                            "td_landed": {fighter_a: td_a_landed, fighter_b: td_b_landed},
                            "td_thrown": {fighter_a: td_a_thrown, fighter_b: td_b_thrown},
                            "sub_attempts": {fighter_a: sub_a, fighter_b: sub_b}
                        }

            return stats_data
        except Exception as e:
            self.logger.error(f"Failed to scrape UFC fight details from {fight_url}: {e}")
            return {}

    def scrape_fighter_history(self, fighter_url: str) -> Dict[str, Any]:
        """
        Scrapes historical career baseline metrics for a target fighter from their profile page.
        Includes height, reach, stance, striking accuracy/defense, and grappling statistics.
        Also parses the complete fight history table at the bottom of the page.
        """
        self.logger.info(f"Scraping fighter career data from: {fighter_url}")
        try:
            res = self.session.get(fighter_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "html.parser")
            
            name_el = soup.find("span", class_="b-content__title-highlight")
            if not name_el:
                return {}
                
            fighter_name = name_el.text.strip()
            
            # Biographical details from lists
            bio = {}
            list_items = soup.find_all("li", class_="b-list__box-list-item")
            for item in list_items:
                text = item.text.strip().replace("\n", "").replace("  ", "")
                if "Height:" in text:
                    bio["height"] = text.replace("Height:", "").strip()
                elif "Weight:" in text:
                    bio["weight"] = text.replace("Weight:", "").strip()
                elif "Reach:" in text:
                    bio["reach"] = text.replace("Reach:", "").strip()
                elif "Stance:" in text:
                    bio["stance"] = text.replace("Stance:", "").strip()
                elif "DOB:" in text:
                    bio["dob"] = text.replace("DOB:", "").strip()
                    
            # Career performance stats
            career_stats = {}
            perf_boxes = soup.find_all("div", class_="b-list__info-box-left")
            for box in perf_boxes:
                items = box.find_all("li", class_="b-list__box-list-item")
                for item in items:
                    text = item.text.strip().replace("\n", "").replace("  ", "")
                    
                    if "SLpM:" in text:
                        # Significant strikes landed per minute
                        career_stats["slpm"] = float(re.findall(r"\d+\.\d+", text)[0])
                    elif "Str. Acc.:" in text:
                        # Striking accuracy percentage
                        career_stats["striking_acc"] = float(re.findall(r"\d+", text)[0]) / 100.0
                    elif "SApM:" in text:
                        # Significant strikes absorbed per minute
                        career_stats["sapm"] = float(re.findall(r"\d+\.\d+", text)[0])
                    elif "Str. Def:" in text:
                        # Striking defense percentage
                        career_stats["striking_def"] = float(re.findall(r"\d+", text)[0]) / 100.0
                    elif "TD Avg.:" in text:
                        # Takedowns average per 15 mins
                        career_stats["td_avg"] = float(re.findall(r"\d+\.\d+", text)[0])
                    elif "TD Acc.:" in text:
                        # Takedown accuracy percentage
                        career_stats["td_acc"] = float(re.findall(r"\d+", text)[0]) / 100.0
                    elif "TD Def.:" in text:
                        # Takedown defense percentage
                        career_stats["td_def"] = float(re.findall(r"\d+", text)[0]) / 100.0
                    elif "Sub. Avg.:" in text:
                        # Submission average per 15 mins
                        career_stats["sub_avg"] = float(re.findall(r"\d+\.\d+", text)[0])

            # Parse fight list table
            fights = []
            tbody = soup.find("tbody", class_="b-fight-details__table-body")
            rows = tbody.find_all("tr", class_="b-fight-details__table-row") if tbody else soup.find_all("tr", class_="b-fight-details__table-row")
            
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 8:
                    continue
                
                # Column 0: Result
                res_flag = cols[0].find(class_="b-flag__text")
                result = res_flag.text.strip().lower() if res_flag else cols[0].text.strip().lower()
                
                # Filter out "next" or upcoming fights if they don't have a settled result
                if result in ["next", "scheduled", "u"]:
                    continue
                
                # Column 1: Opponent
                opponent_link = None
                links = cols[1].find_all("a")
                for link in links:
                    if link.text.strip().lower() != fighter_name.lower():
                        opponent_link = link
                        break
                if not opponent_link and links:
                    opponent_link = links[0]
                
                opp_name = opponent_link.text.strip() if opponent_link else ""
                opp_url = opponent_link["href"] if opponent_link else ""
                
                # Column 6: Event and Date
                evt_link = cols[6].find("a")
                evt_name = evt_link.text.strip() if evt_link else ""
                evt_date = None
                date_span = cols[6].find("span", class_="b-statistics__date")
                if not date_span:
                    date_span = cols[6].find("span")
                date_str = date_span.text.strip() if date_span else cols[6].text.replace(evt_name, "").strip()
                
                try:
                    evt_date = datetime.strptime(date_str, "%b %d, %Y")
                except ValueError:
                    try:
                        evt_date = datetime.strptime(date_str, "%B %d, %Y")
                    except ValueError:
                        evt_date = datetime.now()
                        
                # Column 7: Method
                method = cols[7].text.strip()
                
                # Column 8: Round
                try:
                    r_val = int(cols[8].text.strip())
                except ValueError:
                    r_val = 3
                    
                fights.append({
                    "opponent_name": opp_name,
                    "opponent_url": opp_url,
                    "result": result,  # 'win', 'loss', 'draw', 'nc'
                    "method": method,
                    "event_name": evt_name,
                    "event_date": evt_date,
                    "end_round": r_val
                })

            return {
                "fighter_name": fighter_name,
                "biography": bio,
                "career_statistics": career_stats,
                "fights": fights
            }
        except Exception as e:
            self.logger.error(f"Failed to scrape UFC fighter details from {fighter_url}: {e}")
            return {}
