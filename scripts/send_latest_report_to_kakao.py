import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests


# 실사용 기준: 2,000자 수신이 확인된 경우를 반영해 1,900자로 전송
# 단, 공식 문서상 기본 text template은 200자 제한이므로 실패 시 180자 fallback
PRIMARY_MAX_LEN = 1900
FALLBACK_MAX_LEN = 180
SEND_INTERVAL_SECONDS = 1


def refresh_access_token() -> str:
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_API_KEY"],
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }

    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")
    if client_secret:
        data["client_secret"] = client_secret

    resp = requests.post(
        "https://kauth.kakao.com/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data=data,
        timeout=20,
    )
    resp.raise_for_status()

    payload = resp.json()

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
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        line = re.sub(r"^#+\s*", "", line)
        line = line.replace("**", "")
        line = line.replace("`", "")
        line = re.sub(r"^\*\s+", "- ", line)
        line = re.sub(r"\s+", " ", line)

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def split_text(text: str, max_len: int) -> list[str]:
    chunks = []
    current = ""

    for line in text.split("\n"):
        line = line.strip()

        while len(line) > max_len:
            if current:
                chunks.append(current)
                current = ""

            chunks.append(line[:max_len])
            line = line[max_len:].strip()

        if not line:
            continue

        candidate = line if not current else f"{current}\n{line}"

        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = line

    if current:
        chunks.append(current)

    return chunks


def send_one_message(access_token: str, text: str, file_url: str) -> None:
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": file_url,
            "mobile_web_url": file_url,
        },
        "button_title": "전체 리포트 보기",
    }

    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        data={
            "template_object": json.dumps(template_object, ensure_ascii=False)
        },
        timeout=20,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Kakao message send failed: {resp.status_code} {resp.text}")

    payload = resp.json()

    if payload.get("result_code") != 0:
        raise RuntimeError(f"Kakao message send failed: {payload}")

    print(payload)


def send_chunks(access_token: str, chunks: list[str], file_url: str) -> None:
    total = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):
        if total == 1:
            message = chunk
        else:
            prefix = f"[AI Morning Brief {idx}/{total}]\n"
            message = prefix + chunk

        send_one_message(access_token, message, file_url)
        time.sleep(SEND_INTERVAL_SECONDS)


def send_kakao(report_path: str) -> None:
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report_text = path.read_text(encoding="utf-8")
    cleaned_text = clean_markdown(report_text)

    if not cleaned_text:
        cleaned_text = f"새 리포트가 업로드되었습니다: {report_path}"

    access_token = refresh_access_token()
    file_url = build_github_file_url(report_path)

    primary_chunks = split_text(cleaned_text, PRIMARY_MAX_LEN)

    try:
        print(f"Trying Kakao send with max_len={PRIMARY_MAX_LEN}")
        send_chunks(access_token, primary_chunks, file_url)
        return
    except Exception as exc:
        print(f"Primary send failed. Falling back to {FALLBACK_MAX_LEN}-character chunks.")
        print(str(exc))

    fallback_chunks = split_text(cleaned_text, FALLBACK_MAX_LEN)
    send_chunks(access_token, fallback_chunks, file_url)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python send_latest_report_to_kakao.py <report_path>")

    send_kakao(sys.argv[1])
