from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / "skills" / "social-media" / "xurl" / "SKILL.md"
# The website/docs tree is maintained out-of-band and not populated in every
# checkout.  When it IS present, keep it consistent with the skill; when it is
# absent (current state of this repo), don't fail CI on a file that doesn't
# exist.
DOC_MD = (
    REPO_ROOT
    / "website"
    / "docs"
    / "user-guide"
    / "skills"
    / "bundled"
    / "social-media"
    / "social-media-xurl.md"
)

# The "X Articles must use raw API mode" guidance.  These exact phrases are the
# contract -- if a future edit rewrites the section, the test fails loudly.
RAW_MODE_PHRASES = (
    "For X Articles, use raw API mode",
    "`xurl read`",
    "do not put `read` before a `/2/tweets/...`",
    "tweet.fields=created_at,lang,public_metrics",
    "referenced_tweets,article",
    "data.article.plain_text",
)
FORBIDDEN_PHRASE = "read '/2/tweets/"


def test_xurl_article_ingestion_uses_raw_api_mode():
    skill_text = SKILL_MD.read_text(encoding="utf-8")

    for phrase in RAW_MODE_PHRASES:
        assert phrase in skill_text
    assert FORBIDDEN_PHRASE not in skill_text


def test_xurl_article_ingestion_docs_matches_skill_when_present():
    if not DOC_MD.exists():
        # website/docs is not checked into this repo -- nothing to verify.
        return

    docs_text = DOC_MD.read_text(encoding="utf-8")
    for phrase in RAW_MODE_PHRASES:
        assert phrase in docs_text
    assert FORBIDDEN_PHRASE not in docs_text
