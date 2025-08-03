import requests
from typing import Dict, Optional
import os

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
    
    def _get_kakao_access_token(self, authorization_code: str) -> str:
        """Exchange authorization code for Kakao access token"""
        client_id = os.getenv("KAKAO_CLIENT_ID")
        client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
        
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    
    def _get_kakao_user_profile(self, access_token: str) -> dict:
        """Get user profile from Kakao API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_url = "https://kapi.kakao.com/v2/user/me"
        
        response = requests.get(profile_url, headers=headers)
        response.raise_for_status()
        return response.json() 