import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests


def refresh_access_token() -> str:
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_API_KEY"],
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }

    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")
    if client_secret:
        data["client_secret"] = client_secret

    res = requests.post(
        "https://kauth.kakao.com/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data=data,
        timeout=20,
    )
    res.raise_for_status()

    payload = res.json()

    if "refresh_token" in payload:
        print("WARNING: Kakao returned a new refresh_token.")
        print("Update GitHub Secret KAKAO_REFRESH_TOKEN with the new value.")

    return payload["access_token"]


def build_github_file_url(report_path: str) -> str:
    repository = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["GITHUB_SHA"]
    encoded_path = quote(report_path, safe="/")
    return f"https://github.com/{repository}/blob/{sha}/{encoded_path}"


def compact_markdown(text: str) -> str:
    lines = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        line = line.replace("#", "").replace("*", "").replace("`", "")
        lines.append(line)

    body = "\n".join(lines)

    if len(body) > 430:
        body = body[:430].rstrip() + "\n…전체 내용은 GitHub에서 확인"

    return body


def send_kakao(report_path: str) -> None:
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report_text = path.read_text(encoding="utf-8")
    access_token = refresh_access_token()
    file_url = build_github_file_url(report_path)

    description = compact_markdown(report_text) or f"새 리포트가 업로드되었습니다: {report_path}"

    template_object = {
        "object_type": "feed",
        "content": {
            "title": "AI Morning Brief",
            "description": description,
            "link": {
                "web_url": file_url,
                "mobile_web_url": file_url,
            },
        },
        "button_title": "리포트 보기",
    }

    res = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        timeout=20,
    )
    res.raise_for_status()
    print(res.json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python send_latest_report_to_kakao.py <report_path>")

    send_kakao(sys.argv[1])
