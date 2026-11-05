import builtins
import keyword
import re

_PYTHON = (
    keyword.kwlist
    + [n for n in dir(builtins) if not n.startswith("_")]
    + """self __init__ __name__ __main__ __str__ __repr__ django models CharField TextField IntegerField
    FloatField BooleanField DateField DateTimeField ForeignKey ManyToManyField OneToOneField SlugField
    EmailField ImageField FileField JSONField on_delete CASCADE objects filter exclude get all order_by
    create save delete HttpResponse JsonResponse render redirect get_object_or_404 reverse path include
    urlpatterns admin request response context template forms serializers settings INSTALLED_APPS
    MIDDLEWARE DATABASES STATIC_URL ALLOWED_HOSTS DEBUG login_required csrf_exempt""".split()
)

_JS = """break case catch class const continue debugger default delete do else export extends finally
for function if import in instanceof let new return super switch this throw try typeof var void while
with yield async await of static null undefined true false console log error warn document window
getElementById querySelector querySelectorAll addEventListener createElement appendChild innerHTML
textContent classList localStorage sessionStorage setTimeout setInterval fetch Promise then catch JSON
parse stringify Array Object String Number Boolean Math Date map filter reduce forEach find includes
push pop slice splice join split length require module exports useState useEffect useRef useMemo
useCallback useContext useReducer React ReactDOM props children className onClick onChange onSubmit
key ref style defaultProps Fragment""".split()

_HTML_TAGS = """html head body title meta link script style div span p a img ul ol li table thead tbody
tr td th form input button label select option textarea h1 h2 h3 h4 h5 h6 header footer nav main section
article aside figure figcaption video audio source canvas iframe br hr strong em small code pre
blockquote""".split()
_HTML_ATTRS = """class id href src alt title type name value placeholder style rel charset content lang
width height target action method for checked disabled readonly required data-id onclick onchange
onsubmit autofocus""".split()

_CSS = """display position top right bottom left width height margin padding border background color
font-size font-family font-weight line-height text-align text-decoration flex flex-direction
justify-content align-items gap grid grid-template-columns overflow opacity transition transform
animation box-shadow border-radius cursor z-index content visibility max-width min-width max-height
min-height none block inline inline-block flex absolute relative fixed sticky center solid important
@media @keyword @import @font-face :hover :focus :active ::before ::after""".split()

_WORDS = {
    "python": _PYTHON,
    "javascript": _JS + _HTML_TAGS,
    "html": _HTML_TAGS + _HTML_ATTRS + ["block", "endblock", "extends", "include", "load", "static",
                                         "url", "csrf_token", "for", "endfor", "if", "elif", "else", "endif"],
    "css": _CSS,
}

_WORD_RE = re.compile(r"[A-Za-z_$][\w$-]{2,}")
MAX_SCAN = 300_000


def static_words(lang):
    return sorted(set(_WORDS.get(lang, [])))


def completions(lang, text):
    """Til kalit so'zlari + hujjatdagi so'zlar."""
    words = set(_WORDS.get(lang, []))
    if len(text) <= MAX_SCAN:
        words.update(_WORD_RE.findall(text))
    return sorted(words, key=str.lower)
