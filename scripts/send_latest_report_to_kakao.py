import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests


MAX_KAKAO_TEXT_LEN = 190


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


def clean_markdown(text: str) -> str:
    lines = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        line = (
            line.replace("#", "")
            .replace("**", "")
            .replace("*", "")
            .replace("`", "")
        )

        lines.append(line)

    return "\n".join(lines)


def split_text_by_limit(text: str, max_len: int = MAX_KAKAO_TEXT_LEN) -> list[str]:
    chunks = []
    current = ""

    for line in text.splitlines():
        candidate = line if not current else current + "\n" + line

        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        # 한 줄 자체가 너무 길면 강제로 자릅니다.
        while len(line) > max_len:
            chunks.append(line[:max_len])
            line = line[max_len:]

        current = line

    if current:
        chunks.append(current)

    return chunks


def send_one_kakao_message(access_token: str, text: str, file_url: str) -> None:
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": file_url,
            "mobile_web_url": file_url,
        },
        "button_title": "전체 리포트 보기",
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


def send_kakao(report_path: str) -> None:
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report_text = path.read_text(encoding="utf-8")
    cleaned_text = clean_markdown(report_text)

    access_token = refresh_access_token()
    file_url = build_github_file_url(report_path)

    chunks = split_text_by_limit(cleaned_text)

    if not chunks:
        chunks = [f"새 리포트가 업로드되었습니다: {report_path}"]

    total = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):
        prefix = f"[AI Morning Brief {idx}/{total}]\n"
        allowed_body_len = MAX_KAKAO_TEXT_LEN - len(prefix)

        message = prefix + chunk[:allowed_body_len]

        send_one_kakao_message(access_token, message, file_url)

        # 너무 빠르게 연속 호출하지 않도록 약간 쉬어갑니다.
        time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python send_latest_report_to_kakao.py <report_path>")

    send_kakao(sys.argv[1])
