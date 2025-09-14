#!/usr/bin/env python3
"""
LLM prompt generation script for AppMagician pipeline.
Generates app specifications and prompts using ChatGPT or DeepSeek APIs.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import time


def main():
    # Configuration from environment variables
    provider = os.environ.get('LLM_PROVIDER', 'chatgpt').strip().lower()
    openai_model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    deepseek_model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    api_key = os.environ.get('OPENAI_API_KEY') if provider == 'chatgpt' else os.environ.get('DEEPSEEK_API_KEY')
    
    if not api_key:
        print("Missing API key for provider", provider, file=sys.stderr)
        sys.exit(1)

    url = "https://api.openai.com/v1/chat/completions" if provider == 'chatgpt' else "https://api.deepseek.com/chat/completions"
    model = openai_model if provider == 'chatgpt' else deepseek_model
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # Inputs from Jenkins params/env (all optional)
    prompt_hint = os.environ.get('APP_IDEA', '').strip()
    bundle_id = os.environ.get('BUNDLE_ID', 'com.example.generated').strip()
    locales_str = os.environ.get('LOCALES', '').strip()
    default_locale = os.environ.get('DEFAULT_LOCALE', 'en').strip()
    locales = [x.strip() for x in (locales_str.split(',') if locales_str else [default_locale]) if x.strip()]
    if not locales:
        locales = ['en']

    # ---- Validation helpers ----
    FORBIDDEN = [
        r'\bflutter\s+create\b',
        r'\bCreate\s+(a\s+)?Flutter\s+project\b',
        r'\bset\s+up\s+the\s+iOS\s+platform\b',
        r'\bUpdate\s+ios/Runner\.xcodeproj/project\.pbxproj\b'
    ]

    def prompt_is_valid(p):
        if not isinstance(p, str) or not p.strip():
            return False, "empty"
        if len(p) > 1000:
            return False, "too_long"
        s = p.lower()
        if '```' in p:
            return False, "code_fence"
        for pat in FORBIDDEN:
            if re.search(pat, p, re.I):
                return False, "forbidden:" + pat
        if not re.search(r'\b(pubspec\.yaml|analysis_options\.yaml|lib/[^\s]+\.dart|test/[^\s]+_test\.dart|ios/[^\s]+)\b', p):
            return False, "no_explicit_file_paths"
        return True, "ok"

    HINT_KEYWORDS = [w for w in re.findall(r'[a-z]{3,}', prompt_hint.lower())] or []

    def prompts_cover_hint(prompts):
        if not HINT_KEYWORDS:
            return True
        joined = " ".join(prompts).lower()
        return all(w in joined for w in set(HINT_KEYWORDS[:3]))  # require a few keywords appear

    def concrete_enough(prompts):
        joined = "\n".join(prompts)
        return bool(re.search(r'\blib/[^\s]+\.dart\b', joined) and re.search(r'\btest/[^\s]+_test\.dart\b', joined))

    def set_is_valid(prompts):
        if not isinstance(prompts, list) or not prompts:
            return False, ["prompts_missing"]
        problems = []
        if not (6 <= len(prompts) <= 10):
            problems.append(f"count:{len(prompts)}")
        for i, p in enumerate(prompts):
            ok, why = prompt_is_valid(p)
            if not ok:
                problems.append(f"p{i+1}:{why}")
        if not prompts_cover_hint(prompts):
            problems.append("idea_alignment")
        if not concrete_enough(prompts):
            problems.append("concreteness")
        return (len(problems) == 0), problems

    def strip_code_fences(text: str) -> str:
        text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.I)
        text = re.sub(r'```\s*$', '', text, flags=re.I)
        return text.strip()

    system_msg = (
        "You are a senior Flutter iOS lead working INSIDE an existing repo. "
        "Return STRICT JSON only. Do NOT suggest creating projects. "
        "Every step must edit explicit files under pubspec.yaml, analysis_options.yaml, lib/**, test/**, or ios/** (safe files only)."
    )

    # App spec scaffold we want the model to follow
    spec_hint = {
        "app_name": "app_generated",
        "spec": {"theme": "light", "locale": locales[0], "platforms": ["ios"], "features": ["utility"]},
        "cursor_prompts": [
            "Edit pubspec.yaml: add needed deps (e.g., flutter_localizations).",
            "Create lib/features/core/app_localizations.dart (if needed) or ARB/JSON setup.",
            "Create lib/main.dart and wire MaterialApp + supportedLocales.",
            "Create a feature under lib/features/<your_feature>/... with provider/service/widgets.",
            "Write at least one unit test under test/features/..._test.dart.",
            "Tighten analysis_options.yaml."
        ],
        "meta": {
            "requested_locales": locales,
            "bundle_id_hint": bundle_id,
            "feature_summary": prompt_hint or "Implement utility feature."
        }
    }

    # User message that forces alignment with the hint and forbids project creation
    user_msg = f"""
Create a small **iOS Flutter utility app idea** based on this hint (if any):
"{prompt_hint}"

STRICT requirements:
- DO NOT create projects or mention 'flutter create' or 'set up iOS platform'.
- Generate 6–10 concrete prompts. Each prompt must specify exact files to create/modify under: pubspec.yaml, analysis_options.yaml, lib/**, test/**, ios/Runner/Info.plist.
- Focus on the hinted idea (e.g., reminder/interval timer) and avoid unrelated "chat" features unless explicitly hinted.
- No secrets. Read API base URL / key via runtime placeholders only when needed by the idea.

Return JSON EXACTLY with keys:
{{
  "app_name": "lowercase_snake_case_name",
  "spec": {{"theme":"light|dark","locale":"{locales[0]}", "platforms":["ios"], "features":["feature_name"]}},
  "cursor_prompts": ["step 1 ...", "step 2 ...", "..."],
  "meta": {{"requested_locales": {json.dumps(locales)}, "bundle_id_hint": "{bundle_id}", "feature_summary": "1-line feature"}}
}}
"""

    def call_api(body):
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)

    attempts = 0
    obj = None
    while attempts < 3:
        attempts += 1
        body = {"model": model, "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]}
        try:
            data = call_api(body)
            content = strip_code_fences(data["choices"][0]["message"]["content"])
            obj = json.loads(content)
        except Exception as e:
            if provider == 'chatgpt' and model != 'gpt-4o-mini':
                model = 'gpt-4o-mini'
                continue
            print("LLM call/parse failed:", e, file=sys.stderr)
            sys.exit(1)

        prompts = obj.get("cursor_prompts", [])
        ok, why = set_is_valid(prompts)
        if ok:
            break
        # corrective re-ask
        user_msg += "\n\nFix these validation issues and resend JSON only: " + ", ".join(map(str, why))
    else:
        print("Failed to obtain valid prompts after retries.", file=sys.stderr)
        sys.exit(1)

    os.makedirs("out", exist_ok=True)
    with open("out/app_spec.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    with open("out/app_dir.txt", "w") as f:
        f.write((obj.get("app_name") or os.environ.get("APP_DIR", "generated_app")).strip())

    print("Provider:", provider)
    print("Model:", model)
    print("App name:", obj.get("app_name"))
    print("Prompts:", len(obj.get("cursor_prompts", [])))


if __name__ == "__main__":
    main()
