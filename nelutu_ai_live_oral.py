"""Manual, opt-in LIVE oral exam. Never runs in CI or the parent portal.

Requires environment variables NELUTU_CF_ACCOUNT_ID and NELUTU_CF_API_TOKEN.
Sends ONLY exact public educational questions already allowlisted by the privacy gate.
Prints no tokens, request headers, identifiers or raw provider errors.
"""
from __future__ import annotations
import os
import time
from nelutu_cloudflare_ai import generate, AIUnavailable
from nelutu_ai_privacy import approved_external_question

QUESTIONS = (
    ("De ce învățăm matematica?", ("matematic", "gând", "logic", "problem", "calcul")),
    ("Ce rol are educația tehnică?", ("tehnic", "practic", "meseri", "abilit", "profes")),
    ("Cum putem învăța mai eficient?", ("învăț", "repet", "exers", "plan", "metod")),
)

def main():
    account = os.environ.get("NELUTU_CF_ACCOUNT_ID", "")
    token = os.environ.get("NELUTU_CF_API_TOKEN", "")
    if not account or not token:
        print("NOT_RUN: missing isolated live-exam credentials")
        return 2
    if not all(approved_external_question(q) for q, _ in QUESTIONS):
        print("NOT_RUN: question outside public allowlist")
        return 2
    print("LIVE ORAL EXAM: public synthetic questions only; model answers below")
    passed = 0
    for number, (question, keywords) in enumerate(QUESTIONS, 1):
        start = time.perf_counter()
        try:
            result = generate(question, account_id=account, api_token=token)
            elapsed = time.perf_counter() - start
            answer = result.text
            keyword_match = any(word in answer.casefold() for word in keywords)
            timely = elapsed <= 8.0
            meaningful = len(answer.strip()) >= 40
            ok = result.available and keyword_match and meaningful and timely
            passed += int(ok)
            print(f"Q{number}: {question}")
            print(f"Time: {elapsed:.2f}s | <=8s: {timely} | nontrivial: {meaningful} | topic_match: {keyword_match} | preliminary_pass: {ok}")
            print(f"Answer: {answer[:2200]}")
        except AIUnavailable as exc:
            elapsed = time.perf_counter() - start
            print(f"Q{number}: provider unavailable ({str(exc)}) | time: {elapsed:.2f}s")
    print(f"PRELIMINARY: {passed}/{len(QUESTIONS)}; requires human assessment of factuality, tone and safety")
    return 0 if passed == len(QUESTIONS) else 1

if __name__ == "__main__":
    raise SystemExit(main())
