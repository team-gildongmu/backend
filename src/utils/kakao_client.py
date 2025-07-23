import requests
from typing import Dict, Optional

class KakaoClient:
    def __init__(self, client_id: str, client_secret: Optional[str], redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = "https://kauth.kakao.com/oauth/token"
        self.user_info_url = "https://kapi.kakao.com/v2/user/me"
        
    def get_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        # Only add client_secret if it's provided
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information using access token"""
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(self.user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def unlink(self, access_token: str) -> Dict:
        """Unlink user from Kakao"""
        unlink_url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(unlink_url, headers=headers)
        response.raise_for_status()
        return response.json() 