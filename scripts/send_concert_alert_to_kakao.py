"""concerts/YYYY-MM-DD.md 의 공연 알림을 카카오톡 '나에게 보내기'로 발송한다."""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from kakao_client import update_github_secret

MAX_KAKAO_TEXT_LEN = 200
MAX_MESSAGES = 5
SEND_INTERVAL_SECONDS = 1

LINK_PATTERN = re.compile(r"^-?\s*링크\s*[:：]\s*(\S+)", re.MULTILINE)


def mask_in_logs(value: str) -> None:
    if value:
        print(f"::add-mask::{value}")


def refresh_access_token() -> tuple[str, Exception | None]:
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
    if resp.status_code != 200:
        raise RuntimeError(
            f"Kakao token refresh failed: {resp.status_code} {resp.text}\n"
            "invalid_grant 이면 리프레시 토큰이 만료/폐기된 것이므로 재발급해야 합니다."
        )

    payload = resp.json()

    # 카카오가 리프레시 토큰을 회전시키면 옛 토큰은 즉시 폐기된다.
    # 새 토큰 저장에 실패하면 다음 실행부터 무조건 실패하므로, 발송 후 job 을 실패시킨다.
    rotation_error: Exception | None = None
    new_refresh_token = payload.get("refresh_token")
    if new_refresh_token:
        mask_in_logs(new_refresh_token)
        print("Kakao issued a new refresh token; the previous one is now revoked.")
        gh_pat = os.environ.get("GH_PAT")
        if not gh_pat:
            rotation_error = RuntimeError("GH_PAT 이 없어 회전된 리프레시 토큰을 저장하지 못했습니다.")
            print(f"ERROR: {rotation_error}")
        else:
            owner, _, repo = os.environ["GITHUB_REPOSITORY"].partition("/")
            try:
                update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh_token, owner, repo, gh_pat)
            except Exception as exc:
                rotation_error = exc
                print(f"ERROR: failed to persist the rotated refresh token: {exc}")

    access_token = payload["access_token"]
    mask_in_logs(access_token)
    return access_token, rotation_error


def build_github_file_url(file_path: str) -> str:
    repository = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["GITHUB_SHA"]
    return f"https://github.com/{repository}/blob/{sha}/{quote(file_path, safe='/')}"


def clean_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = line.replace("**", "").replace("`", "")
        line = re.sub(r"^\*\s+", "- ", line)
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def trim_message(text: str) -> str:
    if len(text) <= MAX_KAKAO_TEXT_LEN:
        return text
    suffix = "\n…자세히는 버튼에서"
    return text[: MAX_KAKAO_TEXT_LEN - len(suffix)].rstrip() + suffix


def split_concert_blocks(report_text: str) -> list[str]:
    normalized = report_text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"^##\s+", normalized, flags=re.MULTILINE)[1:]
    return [b.strip() for b in blocks if b.strip()]


def build_message(block: str) -> tuple[str, str | None]:
    link_match = LINK_PATTERN.search(block)
    link_url = link_match.group(1) if link_match else None
    body = clean_markdown(LINK_PATTERN.sub("", block))
    return "[콘서트 알림]\n" + body, link_url


def send_one_message(access_token: str, text: str, link_url: str, button_title: str) -> None:
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": link_url, "mobile_web_url": link_url},
        "button_title": button_title,
    }
    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Kakao message send failed: {resp.status_code} {resp.text}")
    payload = resp.json()
    if payload.get("result_code") != 0:
        raise RuntimeError(f"Kakao message send failed: {payload}")
    print(payload)


def send_concert_alert(report_path: str) -> None:
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Concert report file not found: {report_path}")

    blocks = split_concert_blocks(path.read_text(encoding="utf-8"))
    if not blocks:
        print("발송할 공연이 없습니다. 카카오톡을 보내지 않고 종료합니다.")
        return

    if len(blocks) > MAX_MESSAGES:
        print(f"공연 {len(blocks)}건 중 상위 {MAX_MESSAGES}건만 발송합니다.")
        blocks = blocks[:MAX_MESSAGES]

    access_token, rotation_error = refresh_access_token()
    fallback_url = build_github_file_url(report_path)

    for index, block in enumerate(blocks):
        text, link_url = build_message(block)
        send_one_message(
            access_token,
            trim_message(text),
            link_url or fallback_url,
            "예매 정보 보기" if link_url else "전체 알림 보기",
        )
        if index < len(blocks) - 1:
            time.sleep(SEND_INTERVAL_SECONDS)

    if rotation_error is not None:
        raise RuntimeError(
            "알림은 발송했지만 회전된 카카오 리프레시 토큰을 저장하지 못했습니다. "
            f"다음 실행부터 실패합니다. 원인: {rotation_error}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python send_concert_alert_to_kakao.py <concert_report_path>")
    send_concert_alert(sys.argv[1])
