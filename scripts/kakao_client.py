import os
import base64
import nacl.public
import nacl.utils
import nacl.encoding
import requests

GITHUB_API_URL = "https://api.github.com"


def update_github_secret(secret_name: str, secret_value: str, repo_owner: str, repo_name: str, gh_pat: str) -> None:
    """GitHub Secrets API로 시크릿 업데이트"""
    url = f"{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"

    headers = {
        "Authorization": f"Bearer {gh_pat}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # 퍼블릭 키 가져오기
    key_url = f"{GITHUB_API_URL}/repos/{repo_orets/public-key"
    key_resp = requests.get(key_url, headers=h
    key_resp.raise_for_status()
    key_data = key_resp.json()
    public_key = key_data["key"]
    key_id = key_data["key_id"]

    # sodium 라이브러리로 암호화
    public_key_obj = nacl.public.PublicKey(pubg.Base64Encoder)
    sealed_box = nacl.public.SealedBox(public_
    encrypted = sealed_box.encrypt(secret_valu
    encrypted_b64 = base64.b64encode(encrypted

    payload = {
        "encrypted_value": encrypted_b64,
        "key_id": key_id,
    }

    response = requests.put(url, headers=heade
    response.raise_for_status()
    print(f"GitHub secret '{secret_name}' updated successfully.")
