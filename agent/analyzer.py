import json
import time
import anthropic

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a real estate wholesaling intelligence analyst for Buying Hero,
a South Florida acquisition company specializing in distressed seller deals.
You analyze YouTube video content to extract actionable intelligence for the team.

The company's business:
- Wholesaling (assigning contracts), primarily Miami-Dade and surrounding areas
- Distressed seller acquisitions (cold calls, direct mail, motivated sellers)
- Assignment fees targeting $20K average
- Team of 4: two partners, lead manager, acquisitions manager"""

ANALYSIS_PROMPT = """Analyze this YouTube video content and extract intelligence for a real estate wholesaling team.

VIDEO TITLE: {title}
CHANNEL: {channel}
CONTENT SOURCE: {content_type}

CONTENT:
{content}

Return ONLY valid JSON with exactly this structure (no markdown, no explanation):
{{
  "summary": "2-3 sentence summary focused on wholesaling tactics and key takeaways",
  "key_lessons": ["max 5 most actionable lessons"],
  "trends": ["market or strategy trends mentioned - max 3"],
  "acquisition_one_liners": ["verbatim scriptable phrases a rep could say to a motivated seller - max 5"],
  "disposition_one_liners": ["verbatim scriptable phrases for talking to cash buyers or JV partners - max 3"],
  "tips_and_tricks": ["tactical operational tips - max 5"],
  "south_florida_relevance": "note if anything is specifically relevant to Miami-Dade / South Florida market, or N/A",
  "market_relevance": "High / Medium / Low",
  "confidence_score": 0.0
}}

Rules:
- acquisition_one_liners must be word-for-word phrases a person could say on a call, not descriptions
- confidence_score: 1.0 = pure wholesaling content, 0.5 = general investing, 0.0 = not relevant
- If content_source is 'description', do your best with limited info — lower confidence is expected
- If confidence_score < 0.35, still return valid JSON but minimize other fields
- Flag any mention of South Florida, Miami, Broward, Palm Beach, Florida markets"""


def analyze_video(title, channel, content, content_type='transcript', call_number=0):
    if call_number > 0 and call_number % 5 == 0:
        time.sleep(1)

    prompt = ANALYSIS_PROMPT.format(
        title=title,
        channel=channel,
        content_type=content_type,
        content=content
    )

    try:
        message = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = message.content[0].text.strip()

        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        if result.get('confidence_score', 0) < 0.35:
            print(f"  [SKIP] Low confidence ({result['confidence_score']:.2f}): {title[:60]}")
            return None

        return result

    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error for '{title[:60]}': {e}")
        return None
    except anthropic.APIError as e:
        print(f"  [WARN] Claude API error for '{title[:60]}': {e}")
        time.sleep(3)
        return None
