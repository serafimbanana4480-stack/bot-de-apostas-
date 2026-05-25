"""
Betfair Authentication Module.
Handles OAuth2 login, token refresh, keep-alive heartbeat, and signed requests.
"""
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

class BetfairAuth:
    """Handles authentication for Betfair API."""
    
    def __init__(self):
        self.app_key = settings.BETFAIR_APP_KEY
        self.username = getattr(settings, "BETFAIR_USER", "")
        self.password = getattr(settings, "BETFAIR_PASS", "")
        self.session_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        self.login_url = "https://identitysso-cert.betfair.com/api/certlogin"
        self.keep_alive_url = "https://identitysso.betfair.com/api/keepAlive"
        
    async def login(self, certs_path: str = "certs/") -> bool:
        """Perform certificate-based login to Betfair."""
        if not self.app_key or not self.username or not self.password:
            logger.warning("Betfair credentials missing. Operating in unauthorized mode.")
            return False
            
        try:
            # Note: Requires certs configured locally
            async with httpx.AsyncClient(cert=(f"{certs_path}/client-2048.crt", f"{certs_path}/client-2048.key")) as client:
                data = {'username': self.username, 'password': self.password}
                headers = {
                    'X-Application': self.app_key,
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                response = await client.post(self.login_url, data=data, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                if result.get('loginStatus') == 'SUCCESS':
                    self.session_token = result.get('sessionToken')
                    self.token_expiry = datetime.utcnow() + timedelta(hours=4)
                    logger.info("Betfair login successful")
                    return True
                else:
                    logger.error(f"Betfair login failed: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during Betfair login: {str(e)}")
            return False
            
    async def keep_alive(self) -> bool:
        """Extend the lifetime of current session token."""
        if not self.session_token:
            return await self.login()
            
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Accept': 'application/json',
                    'X-Application': self.app_key,
                    'X-Authentication': self.session_token
                }
                
                response = await client.post(self.keep_alive_url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                if result.get('status') == 'SUCCESS':
                    self.token_expiry = datetime.utcnow() + timedelta(hours=4)
                    return True
                else:
                    return await self.login()
                    
        except Exception as e:
            logger.error(f"Betfair keep-alive failed: {str(e)}")
            return False
            
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers needed for authenticated requests."""
        if not self.session_token:
            raise ValueError("Not authenticated. Call login() first.")
            
        return {
            'X-Application': self.app_key,
            'X-Authentication': self.session_token,
            'Content-Type': 'application/json'
        }
