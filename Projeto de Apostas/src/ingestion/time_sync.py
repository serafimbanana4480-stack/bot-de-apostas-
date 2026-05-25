import logging
import time

logger = logging.getLogger("time_sync")

class TimeSyncCorrector:
    """
    Measures clock drift offset between local server and bookmaker API server.
    Prevents placing late bets on already started games.
    """
    def __init__(self):
        self.clock_offset_seconds = 0.0

    def synchronize_clock(self, api_ping_func: lambda: float) -> float:
        """
        Calculates clock offset using NTP-like round trip calculation.
        Offset = ServerTime - (ClientTime + RTT/2)
        """
        # Step 1: Measure start time
        t_start = time.time()
        
        # Step 2: Query server time
        server_timestamp = api_ping_func()
        
        # Step 3: Measure end time
        t_end = time.time()
        
        rtt = t_end - t_start
        client_midpoint = t_start + (rtt / 2.0)
        
        # Calculate deviation offset
        self.clock_offset_seconds = server_timestamp - client_midpoint
        logger.info(f"Clock synchronization complete. Offset: {self.clock_offset_seconds:.3f}s. RTT: {rtt:.3f}s")
        return self.clock_offset_seconds

    def adjust_kickoff_limit(self, scheduled_kickoff_timestamp: float, safety_margin_seconds: float = 30.0) -> float:
        """
        Adjusts scheduled kickoff timestamp taking clock drift offset into account.
        Returns the adjusted limit timestamp.
        """
        # Adjusted kickoff = ScheduledKickoff - Offset - Safety Margin
        # If server time is ahead (offset > 0), we must submit bets earlier.
        return scheduled_kickoff_timestamp - self.clock_offset_seconds - safety_margin_seconds
