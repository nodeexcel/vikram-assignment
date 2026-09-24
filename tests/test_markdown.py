"""Tests for the small markdown renderer in the web layer.

The spec says decision-logic tests only, no UI tests. This is the exception on
purpose: render_markdown is a pure string function containing a parser and an
escaping path, and it already shipped one real bug — `"<pre>" + escape(x)`
invokes Markup.__radd__ and escapes the literal tags on the left, so fenced
blocks rendered as visible &lt;pre&gt;. That is not catchable by eye in a diff.
"""

from app.web.main import render_markdown


def test_fenced_block_becomes_a_real_pre_code_element():
    out = str(render_markdown("```\na | b\n```"))
    assert "<pre><code>" in out
    assert "&lt;pre&gt;" not in out, "tags were escaped by Markup.__radd__"


def test_fenced_content_is_escaped_not_executed():
    out = str(render_markdown("```\n<script>alert(1)</script>\n```"))
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_fenced_content_survives_verbatim():
    """A diagram's spacing and pipes must not be touched by the inline parser."""
    import html as htmllib
    import re

    src = "```\n  a |\n  *not italic*\n```"
    out = str(render_markdown(src))
    body = htmllib.unescape(re.search(r"<pre><code>(.*?)</code></pre>", out, re.S).group(1))
    assert body == "  a |\n  *not italic*"
    assert "<em>" not in out


def test_unterminated_fence_runs_to_end_rather_than_raising():
    out = str(render_markdown("```\nstill open"))
    assert "<pre><code>still open</code></pre>" in out


def test_a_fence_does_not_get_swallowed_into_a_preceding_list():
    out = str(render_markdown("- item\n```\ncode\n```"))
    assert "</ul>" in out
    assert out.index("</ul>") < out.index("<pre><code>")


def test_headings_lists_and_inline_still_work():
    out = str(render_markdown("# Title\n\n- **bold** and `code`\n- second"))
    assert "<h1>Title</h1>" in out
    assert out.count("<li>") == 2
    assert "<strong>bold</strong>" in out
    assert "<code>code</code>" in out


def test_inline_html_in_prose_is_escaped():
    out = str(render_markdown("a <script>bad()</script> b"))
    assert "<script>" not in out
