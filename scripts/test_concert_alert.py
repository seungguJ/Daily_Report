"""python scripts/test_concert_alert.py  — 외부 호출 없이 발송 경로를 검증한다."""

import base64
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import nacl.encoding
import nacl.public

import kakao_client
import send_concert_alert_to_kakao as cc

SAMPLE = """# 2026-08-23 콘서트

## 아이유 - The Golden Hour
- 날짜: 2026-09-12
- 장소: 올림픽공원 KSPO DOME
- 링크: https://tickets.example.com/iu

## 검정치마 - 단독 공연
- 날짜: 2026-09-20
- 장소: 무신사 개러지
"""

PRIVATE_KEY = nacl.public.PrivateKey.generate()


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def run_case(name, report_text, *, gh_pat, rotate, secret_put_ok=True):
    sent = []
    stored = {}

    def fake_post(url, **kwargs):
        if "kauth" in url:
            payload = {"access_token": "AT"}
            if rotate:
                payload["refresh_token"] = "RT_NEW"
            return FakeResponse(payload)
        sent.append(json.loads(kwargs["data"]["template_object"]))
        return FakeResponse({"result_code": 0})

    def fake_get(url, **kwargs):
        pub = PRIVATE_KEY.public_key.encode(nacl.encoding.Base64Encoder).decode()
        return FakeResponse({"key": pub, "key_id": "kid-1"})

    def fake_put(url, headers=None, json=None, **kwargs):
        if not secret_put_ok:
            raise RuntimeError("403 Forbidden")
        stored.update(json)
        return FakeResponse({})

    env = {
        "KAKAO_REST_API_KEY": "key",
        "KAKAO_REFRESH_TOKEN": "RT_OLD",
        "GITHUB_REPOSITORY": "seungguJ/Daily_Report",
        "GITHUB_SHA": "abc123",
    }
    if gh_pat:
        env["GH_PAT"] = "pat"

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "2026-08-23.md"
        report.write_text(report_text, encoding="utf-8")
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(cc.requests, "post", fake_post), \
             mock.patch.object(kakao_client.requests, "get", fake_get), \
             mock.patch.object(kakao_client.requests, "put", fake_put), \
             mock.patch.object(cc.time, "sleep", lambda _s: None):
            error = None
            try:
                cc.send_concert_alert(str(report))
            except Exception as exc:
                error = exc

    print(f"[{name}] 발송 {len(sent)}건, error={type(error).__name__ if error else None}")
    return sent, stored, error


sent, stored, error = run_case("공연 2건 + 토큰 회전", SAMPLE, gh_pat=True, rotate=True)
assert len(sent) == 2, sent
assert error is None, error
assert sent[0]["link"]["web_url"] == "https://tickets.example.com/iu"
assert sent[0]["button_title"] == "예매 정보 보기"
assert "링크" not in sent[0]["text"]
assert "아이유" in sent[0]["text"]
assert len(sent[0]["text"]) <= cc.MAX_KAKAO_TEXT_LEN
# 링크 없는 블록은 리포트 파일 URL 로 대체
assert sent[1]["link"]["web_url"].startswith("https://github.com/seungguJ/Daily_Report/blob/abc123/")
assert sent[1]["button_title"] == "전체 알림 보기"
# 회전된 리프레시 토큰이 GitHub 공개키로 정확히 암호화됐는지 복호화로 확인
decrypted = nacl.public.SealedBox(PRIVATE_KEY).decrypt(base64.b64decode(stored["encrypted_value"])).decode()
assert decrypted == "RT_NEW", decrypted
print("  회전 토큰 복호화:", decrypted)

sent, _, error = run_case("공연 0건", "# 2026-08-23 콘서트\n\n오늘 새 공연 없음.\n", gh_pat=True, rotate=False)
assert sent == [] and error is None

sent, _, error = run_case("회전됐지만 GH_PAT 없음", SAMPLE, gh_pat=False, rotate=True)
assert len(sent) == 2, "알림은 발송돼야 한다"
assert isinstance(error, RuntimeError) and "다음 실행부터 실패" in str(error)

sent, _, error = run_case("회전됐지만 시크릿 저장 실패", SAMPLE, gh_pat=True, rotate=True, secret_put_ok=False)
assert len(sent) == 2
assert isinstance(error, RuntimeError) and "403 Forbidden" in str(error)

print("전부 통과")
