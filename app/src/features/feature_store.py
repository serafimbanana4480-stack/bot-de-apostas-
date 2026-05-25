import logging

import pandas as pd


class FeatureStore:
    """
    Feature Store to handle temporal features and ensure no data leakage.
    Calculates moving averages, Elo ratings, and form based only on data available 
    prior to the match/fight time.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_football_features(self, df_matches: pd.DataFrame) -> pd.DataFrame:
        """
        Builds football features like trailing xG, past 5 matches form, and H2H.
        Must strictly sort by date and use expanding/rolling windows.
        """
        self.logger.info("Building football temporal features...")
        if df_matches.empty:
            return df_matches
            
        # Example logic:
        # df_matches = df_matches.sort_values('date')
        # df_matches['home_team_form_5'] = df_matches.groupby('home_team')['points'].transform(lambda x: x.rolling(5, closed='left').sum())
        return df_matches

    def build_ufc_features(self, df_fights: pd.DataFrame) -> pd.DataFrame:
        """
        Builds UFC features like win streak, dynamic Elo ratings, and physical/risk factors.
        Stricly chronological processing to prevent look-ahead bias.
        """
        self.logger.info("Building UFC temporal features...")
        if df_fights.empty:
            return df_fights
            

        # Ensure chronological order
        df = df_fights.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Fighter historical states
        fighter_states = {} # name -> { 'elo': 1500.0, 'fights': [] }
        
        def get_fighter_state(name):
            if name not in fighter_states:
                fighter_states[name] = {
                    'elo': 1500.0,
                    'fights': []
                }
            return fighter_states[name]
            
        # Lists to hold computed features
        elo_a_list, elo_b_list = [], []
        elo_diff_list, expected_win_elo_list = [], []
        reach_advantage_mult_list = []
        ko_tko_win_rate_a_list, ko_tko_win_rate_b_list = [], []
        ko_tko_loss_rate_a_list, ko_tko_loss_rate_b_list = [], []
        slpm_decay_a_list, slpm_decay_b_list = [], []
        
        # Default parameter fallbacks if not present in df
        reaches = df['reach_a'] if 'reach_a' in df.columns else pd.Series([0.0]*len(df))
        reaches_b = df['reach_b'] if 'reach_b' in df.columns else pd.Series([0.0]*len(df))
        slpms_a = df['slpm_a'] if 'slpm_a' in df.columns else pd.Series([3.0]*len(df))
        slpms_b = df['slpm_b'] if 'slpm_b' in df.columns else pd.Series([3.0]*len(df))
        sapms_a = df['sapm_a'] if 'sapm_a' in df.columns else pd.Series([3.0]*len(df))
        sapms_b = df['sapm_b'] if 'sapm_b' in df.columns else pd.Series([3.0]*len(df))
        
        for idx, row in df.iterrows():
            fa = row['fighter_a']
            fb = row['fighter_b']
            
            state_a = get_fighter_state(fa)
            state_b = get_fighter_state(fb)
            
            # 1. Elo calculations before the fight
            elo_a = state_a['elo']
            elo_b = state_b['elo']
            elo_a_list.append(elo_a)
            elo_b_list.append(elo_b)
            
            elo_diff = elo_a - elo_b
            elo_diff_list.append(elo_diff)
            
            expected_a = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
            expected_b = 1.0 - expected_a
            expected_win_elo_list.append(expected_a)
            
            # 2. Reach advantage combined with volume
            reach_a = reaches.iloc[idx] if not pd.isna(reaches.iloc[idx]) else 0.0
            reach_b = reaches_b.iloc[idx] if not pd.isna(reaches_b.iloc[idx]) else 0.0
            reach_diff = reach_a - reach_b
            
            slpm_a_val = slpms_a.iloc[idx] if not pd.isna(slpms_a.iloc[idx]) else 3.0
            slpm_b_val = slpms_b.iloc[idx] if not pd.isna(slpms_b.iloc[idx]) else 3.0
            slpm_diff = slpm_a_val - slpm_b_val
            
            reach_advantage_mult = reach_diff * slpm_diff
            reach_advantage_mult_list.append(reach_advantage_mult)
            
            # 3. Dynamic KO/TKO rates based on historical fights before this date
            def calc_ko_tko_rates(fights_history):
                if not fights_history:
                    return 0.0, 0.0
                win_ko = sum(1 for f in fights_history if f['outcome'] == 'win' and 'ko' in f['method'].lower())
                loss_ko = sum(1 for f in fights_history if f['outcome'] == 'loss' and 'ko' in f['method'].lower())
                total = len(fights_history)
                return win_ko / total, loss_ko / total
                
            ko_win_a, ko_loss_a = calc_ko_tko_rates(state_a['fights'])
            ko_win_b, ko_loss_b = calc_ko_tko_rates(state_b['fights'])
            
            ko_tko_win_rate_a_list.append(ko_win_a)
            ko_tko_loss_rate_a_list.append(ko_loss_a)
            ko_tko_win_rate_b_list.append(ko_win_b)
            ko_tko_loss_rate_b_list.append(ko_loss_b)
            
            # 4. Form/decay: recent 3-fight slpm vs historical slpm
            def calc_decay(fights_history, current_slpm):
                if not fights_history:
                    return 1.0
                hist_slpms = [f['slpm'] for f in fights_history if f['slpm'] is not None]
                if not hist_slpms:
                    return 1.0
                avg_hist = sum(hist_slpms) / len(hist_slpms)
                recent_fights = fights_history[-3:]
                recent_slpms = [f['slpm'] for f in recent_fights if f['slpm'] is not None]
                avg_recent = sum(recent_slpms) / len(recent_slpms) if recent_slpms else avg_hist
                return avg_recent / avg_hist if avg_hist > 0 else 1.0
                
            slpm_decay_a_list.append(calc_decay(state_a['fights'], slpm_a_val))
            slpm_decay_b_list.append(calc_decay(state_b['fights'], slpm_b_val))
            
            # 5. Chronological State Update AFTER the fight
            winner = row['winner']
            method = str(row['method']).lower() if not pd.isna(row['method']) else ""
            
            actual_a, actual_b = 0.5, 0.5
            outcome_a, outcome_b = 'draw', 'draw'
            if winner == fa:
                actual_a, actual_b = 1.0, 0.0
                outcome_a, outcome_b = 'win', 'loss'
            elif winner == fb:
                actual_a, actual_b = 0.0, 1.0
                outcome_a, outcome_b = 'loss', 'win'
                
            # Update Elos
            K = 32
            state_a['elo'] = elo_a + K * (actual_a - expected_a)
            state_b['elo'] = elo_b + K * (actual_b - expected_b)
            
            # Record fights
            state_a['fights'].append({
                'outcome': outcome_a,
                'method': method,
                'slpm': slpm_a_val,
                'sapm': sapms_a.iloc[idx] if not pd.isna(sapms_a.iloc[idx]) else 3.0
            })
            state_b['fights'].append({
                'outcome': outcome_b,
                'method': method,
                'slpm': slpm_b_val,
                'sapm': sapms_b.iloc[idx] if not pd.isna(sapms_b.iloc[idx]) else 3.0
            })
            
        # Add computed features to df
        df['elo_a'] = elo_a_list
        df['elo_b'] = elo_b_list
        df['elo_diff'] = elo_diff_list
        df['expected_win_elo'] = expected_win_elo_list
        df['reach_advantage_mult'] = reach_advantage_mult_list
        df['ko_tko_win_rate_a'] = ko_tko_win_rate_a_list
        df['ko_tko_loss_rate_a'] = ko_tko_loss_rate_a_list
        df['ko_tko_win_rate_b'] = ko_tko_win_rate_b_list
        df['ko_tko_loss_rate_b'] = ko_tko_loss_rate_b_list
        df['slpm_decay_a'] = slpm_decay_a_list
        df['slpm_decay_b'] = slpm_decay_b_list
        
        return df
