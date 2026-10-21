"""Brand lookups shared by the local server and the Vercel functions."""
import html
import json
import re
import urllib.error
from datetime import date, timedelta
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"


def fetch(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lenovo(serial, lang=None):
    d = fetch("https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo",
              {"serialNumber": serial, "country": "us", "language": "en"})
    if d.get("code") != 0 or not d.get("data"):
        return {"ok": False, "error": "notFound"}
    data, m = d["data"], d["data"]["machineInfo"]
    items = []
    for kind in ("baseWarranties", "upgradeWarranties", "contractWarranties"):
        for w in data.get(kind) or []:
            items.append({"name": w.get("name"), "type": w.get("deliveryTypeName") or w.get("type"),
                          "start": w.get("startDate"), "end": w.get("endDate")})
    items.sort(key=lambda w: w["end"] or "", reverse=True)
    status = data.get("warrantyStatus") or ""
    return {
        "ok": True, "full": True,
        "model": m.get("productName"), "product": m.get("product"), "serial": m.get("serial"),
        "image": m.get("productImage"),
        "inWarranty": status.lower() == "in warranty", "status": status,
        "end": (data.get("currentWarranty") or {}).get("endDate"),
        "facts": {"built": m.get("buildDate"), "shipped": m.get("shipDate"), "shippedTo": m.get("shipToCountry"),
                  "purchased": m.get("popDate"), "supportEnds": m.get("eosDate")},
        "items": items,
        "link": f"https://pcsupport.lenovo.com/products/{urllib.parse.quote(serial)}/warranty",
    }


def hp(serial, lang=None):
    q = urllib.parse.urlencode({"q": serial, "context": "pdp", "authState": "anonymous",
                                "template": "SupportSearchResults"})
    d = fetch(f"https://support.hp.com/wcc-services/searchresult/us-en?{q}")
    v = ((d.get("data") or {}).get("verifyResponse") or {}).get("data")
    if not v or not v.get("productName"):
        return {"ok": False, "error": "notFound"}
    return {
        "ok": True, "full": False, "brand": "hp",
        "model": v["productName"], "product": v.get("productNumber"), "serial": v.get("serialNumber"),
        "facts": {"productNumber": v.get("productNumber"), "description": v.get("description")},
        "link": "https://support.hp.com/us-en" + v["targetUrl"] if v.get("targetUrl") else "https://support.hp.com/us-en/check-warranty",
    }


# Apple 12-character serials (2010-2020): 4th character = year and half, 5th = week within that half.
APPLE_YEARS = "CDFGHJKLMNPQRSTVWXYZ"
APPLE_WEEKS = "123456789CDFGHJKLMNPQRTVWXY"
APPLE_LOCALES = {"en": "en_US", "fr": "fr_FR", "de": "de_DE", "es": "es_ES", "it": "it_IT", "nl": "nl_NL", "pt": "pt_PT",
                 "pl": "pl_PL", "sv": "sv_SE", "cs": "cs_CZ", "ro": "ro_RO", "tr": "tr_TR", "ru": "ru_RU", "uk": "uk_UA",
                 "ar": "ar_AE", "hi": "en_IN", "zh": "zh_CN", "ja": "ja_JP", "ko": "ko_KR", "id": "id_ID", "vi": "vi_VN"}


def apple_made(serial):
    """Approximate manufacturing date (ISO) of a 12-character Apple serial, or None."""
    if len(serial) != 12 or serial[3] not in APPLE_YEARS or serial[4] not in APPLE_WEEKS:
        return None
    i = APPLE_YEARS.index(serial[3])
    week = APPLE_WEEKS.index(serial[4]) + 26 * (i % 2)
    return (date(2010 + i // 2, 1, 1) + timedelta(weeks=week)).isoformat()


def apple_model(code, lang):
    for loc in dict.fromkeys([APPLE_LOCALES.get(lang or "en", "en_US"), "en_US"]):
        req = urllib.request.Request(f"https://support-sp.apple.com/sp/product?cc={code}&lang={loc}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            m = re.search(r"<configCode>([^<]+)</configCode>", r.read().decode("utf-8", "replace"))
        if m:
            return html.unescape(m.group(1))
    return None


def apple(serial, lang=None):
    if len(serial) not in (10, 11, 12):
        return {"ok": False, "error": "badFormat"}
    model = apple_model(serial[-4:] if len(serial) == 12 else serial[-3:], lang) if len(serial) > 10 else None
    return {
        "ok": True, "full": False, "brand": "apple",
        "model": model, "serial": serial, "random": len(serial) == 10,
        "facts": {"made": apple_made(serial)},
        "link": "https://checkcoverage.apple.com/",
    }


def dell(serial, lang=None):
    if len(serial) not in (5, 7):
        return {"ok": False, "error": "badFormat"}
    code = str(int(serial, 36))
    return {
        "ok": True, "full": False, "brand": "dell",
        "model": None, "serial": serial,
        "facts": {"serviceTag": serial, "expressCode": " ".join(code[i:i + 3] for i in range(0, len(code), 3))},
        "link": f"https://www.dell.com/support/home/en-us/product-support/servicetag/{urllib.parse.quote(serial)}/overview",
    }


BRANDS = {"lenovo": lenovo, "hp": hp, "dell": dell, "apple": apple}


def lookup(brand, serial, lang=None):
    """Return the JSON-ready result for a brand and a raw serial from the query string."""
    serial = (serial or "").strip().upper().replace(" ", "")
    if not serial.isalnum() or len(serial) > 20:
        return {"ok": False, "error": "badSerial"}
    try:
        return BRANDS[brand](serial, (lang or "en")[:5])
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
        return {"ok": False, "error": "unreachable", "detail": str(e)}
