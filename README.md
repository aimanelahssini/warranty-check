<p align="center"><img src="docs/logo.svg" width="96" alt="Warranty Check logo"></p>

<h1 align="center">Warranty Check</h1>

<p align="center">Check a laptop's warranty from its serial number in about a second, without clicking through the brand's support site.<br>Handy when you buy second-hand laptops.</p>

<p align="center"><img src="docs/preview.svg" width="680" alt="Illustration: brand logos, a serial number field, and a result card saying In warranty"></p>

## What it does

| Brand | Result |
|---|---|
| **Lenovo / ThinkPad** | Instant: in or out of warranty, every coverage line with dates, product picture, build, ship and purchase dates |
| **HP** | Confirms the exact model from the serial, then one click to HP's warranty page (HP hides the dates behind a captcha) |
| **Dell** | Opens Dell's page for that Service Tag (Dell blocks direct lookups) |
| **Apple** | Copies the serial and opens Apple's coverage page (Apple requires a captcha) |

Extras: it guesses the brand from the serial's shape, keeps your recent checks, has a "Copy summary" button for sending to a seller, and links like `?brand=lenovo&serial=PF1AB2CD` open straight on the result. "Where do I find the serial?" shows the one-line command for Windows and Linux.

## Run it on the web (Vercel)

The repo deploys to Vercel as is: `public/` is the page, `api/` holds the Python functions that call the brands. Import the repo on [vercel.com/new](https://vercel.com/new) or run `npx vercel --prod`.

## Run it on your own computer (Linux)

```bash
./install.sh     # adds the `warranty` command and an app-grid launcher
warranty         # starts the local server on 127.0.0.1:8765 and opens the page
```

Locally you also get **Check my computer**, which reads this machine's brand and serial (through `pkexec`) and checks it.
Only Python's standard library is needed.

## Why a server?

Browsers refuse to call another site's API from a web page (CORS), so a small backend makes the request: the Vercel functions online, `warranty_server.py` locally. Both use the same code in `api/_core.py`.

Lenovo's lookup uses the same JSON endpoint as Lenovo's own support site. These endpoints are unofficial and can change.

## Credits

Logos from [Simple Icons](https://simpleicons.org) (CC0). Brand names and logos belong to their owners; this project isn't affiliated with any of them.

## License

MIT. Made by [eNamia](https://www.enamia.eu).
