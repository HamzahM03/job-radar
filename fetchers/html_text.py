import html as html_module
import re
from html.parser import HTMLParser

# Tags whose boundaries must become line breaks - otherwise adjacent text
# (e.g. a "Requirements" heading followed immediately by its first bullet)
# silently fuses into one run-on line, which breaks deterministic parsing
# downstream (e.g. years-of-experience matching).
_BLOCK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "blockquote", "hr",
    "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "table",
}
_SKIP_TAGS = {"script", "style"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "br":
            self._parts.append("\n")
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")
            if tag == "li":
                self._parts.append("- ")

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and not self._skip_depth:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def html_to_text(raw_html: str) -> str:
    # Greenhouse's `content` field comes back HTML-entity-encoded (e.g. a
    # real "<p>" is literally the six characters "&lt;p&gt;"), so the actual
    # tags are invisible to HTMLParser until they're unescaped first.
    parser = _TextExtractor()
    parser.feed(html_module.unescape(raw_html))
    parser.close()
    text = html_module.unescape(parser.get_text())

    # Collapse horizontal whitespace and drop blank lines, but keep the line
    # breaks inserted above - those are what keep block/list/heading text
    # from concatenating into a single unparseable run-on line.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
