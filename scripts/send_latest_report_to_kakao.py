import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from kakao_client import update_github_secret


MAX_KAKAO_TEXT_LEN = 2000
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
        new_refresh_token = payload["refresh_token"]
        gh_pat = os.environ.get("GH_PAT")
        if gh_pat:
            try:
                update_github_secret(
                    "KAKAO_REFRESH_TOKEN",
                    new_refresh_token,
                    os.environ["GITHUB_REPOSITORY"].split("/")[0],
                    os.environ["GITHUB_REPOSITORY"].split("/")[1],
                    gh_pat,
                )
            except Exception as e:
                print(f"WARNING: Failed to update GitHub secret: {e}")
        else:
            print("WARNING: New refresh token received but GH_PAT not set.")

    return payload["access_token"]


def build_github_file_url(report_path: str) -> str:
    repository = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ["GITHUB_SHA"]
    encoded_path = quote(report_path, safe="/")
    return f"https://github.com/{repository}/blob/{sha}/{encoded_path}"


def clean_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        line = re.sub(r"^#+\s*", "", line)
        line = line.replace("**", "")
        line = line.replace("`", "")
        line = re.sub(r"^\*\s+", "- ", line)
        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    return "\n".join(lines)


def extract_sections(report_text: str) -> tuple[str, str]:
    cleaned = clean_markdown(report_text)

    paper_pattern = r"(1\.\s*On-device AI 논문[\s\S]*?)(?=\n2\.\s*AI Agent 활용 아이템|$)"
    agent_pattern = r"(2\.\s*AI Agent 활용 아이템[\s\S]*)"

    paper_match = re.search(paper_pattern, cleaned)
    agent_match = re.search(agent_pattern, cleaned)

    if not paper_match:
        raise ValueError("On-device AI 논문 섹션을 찾지 못했습니다.")

    if not agent_match:
        raise ValueError("AI Agent 활용 아이템 섹션을 찾지 못했습니다.")

    paper_section = paper_match.group(1).strip()
    agent_section = agent_match.group(1).strip()

    return paper_section, agent_section


def trim_message(text: str, file_url: str) -> str:
    if len(text) <= MAX_KAKAO_TEXT_LEN:
        return text

    suffix = "\n\n…전체 내용은 버튼에서 확인"
    limit = MAX_KAKAO_TEXT_LEN - len(suffix)

    return text[:limit].rstrip() + suffix


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


def send_kakao(report_path: str) -> None:
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    report_text = path.read_text(encoding="utf-8")
    access_token = refresh_access_token()
    file_url = build_github_file_url(report_path)

    paper_section, agent_section = extract_sections(report_text)

    paper_message = trim_message(
        "[AI Morning Brief - On-device AI 논문]\n\n" + paper_section,
        file_url,
    )

    agent_message = trim_message(
        "[AI Morning Brief - AI Agent 활용 아이템]\n\n" + agent_section,
        file_url,
    )

    # 정확히 2개 메시지만 발송합니다.
    send_one_message(access_token, paper_message, file_url)
    time.sleep(SEND_INTERVAL_SECONDS)
    send_one_message(access_token, agent_message, file_url)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python send_latest_report_to_kakao.py <report_path>")

    send_kakao(sys.argv[1])
