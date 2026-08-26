import re
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent.parent / "templates")


def _linkify(text):
    escaped = str(escape(text))
    url_re = re.compile(r"(https?://[^\s<>]+)")
    result = url_re.sub(
        r'<a href="\1" target="_blank" '
        r'class="text-brand-400 hover:text-brand-300 underline">\1</a>',
        escaped,
    )
    return Markup(result)


templates.env.filters["linkify"] = _linkify
