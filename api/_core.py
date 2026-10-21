"""Brand lookups shared by the local server and the Vercel functions."""
import json
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"


def fetch(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def lenovo(serial):
    d = fetch("https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo",
              {"serialNumber": serial, "country": "us", "language": "en"})
    if d.get("code") != 0 or not d.get("data"):
        return {"ok": False, "error": "Lenovo doesn't know this serial. Check it on the sticker under the laptop."}
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
        "facts": {"Built": m.get("buildDate"), "Shipped": m.get("shipDate"), "Ship country": m.get("shipToCountry"),
                  "Purchase date": m.get("popDate"), "Lenovo support until": m.get("eosDate")},
        "items": items,
        "link": f"https://pcsupport.lenovo.com/products/{urllib.parse.quote(serial)}/warranty",
    }


def hp(serial):
    q = urllib.parse.urlencode({"q": serial, "context": "pdp", "authState": "anonymous",
                                "template": "SupportSearchResults"})
    d = fetch(f"https://support.hp.com/wcc-services/searchresult/us-en?{q}")
    v = ((d.get("data") or {}).get("verifyResponse") or {}).get("data")
    if not v or not v.get("productName"):
        return {"ok": False, "error": "HP doesn't know this serial. Check it on the sticker or with Fn+Esc."}
    return {
        "ok": True, "full": False,
        "model": v["productName"], "product": v.get("productNumber"), "serial": v.get("serialNumber"),
        "facts": {"Product number": v.get("productNumber"), "Description": v.get("description")},
        "note": "HP keeps the warranty dates behind a captcha. The model is confirmed; HP's page shows the dates.",
        "link": "https://support.hp.com/us-en" + v["targetUrl"] if v.get("targetUrl") else "https://support.hp.com/us-en/check-warranty",
    }


BRANDS = {"lenovo": lenovo, "hp": hp}


def lookup(brand, serial):
    """Return the JSON-ready result for a brand and a raw serial from the query string."""
    serial = (serial or "").strip().upper().replace(" ", "")
    if not serial.isalnum() or len(serial) > 20:
        return {"ok": False, "error": "That doesn't look like a serial number."}
    try:
        return BRANDS[brand](serial)
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
        return {"ok": False, "error": f"Couldn't reach the brand's server ({e})."}
