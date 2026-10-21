# Warranty Check

Check a laptop's warranty from its serial number in about a second, without clicking through the brand's support site.

```
./install.sh     # adds the `warranty` command and an app-grid launcher
warranty         # starts the local server (127.0.0.1:8765) and opens the page
```

| Brand | What you get |
|---|---|
| Lenovo / ThinkPad | Full warranty status, every coverage line with dates, build/ship/purchase dates |
| HP | Model confirmed from the serial, then one click to HP's warranty page (HP puts the dates behind a captcha) |
| Dell | Opens Dell's page for that service tag (Dell blocks direct lookups) |
| Apple | Copies the serial and opens Apple's coverage page (Apple requires a captcha) |

"This computer" reads the brand from the firmware and the serial through `pkexec`, then checks it.

A tiny Python server (standard library only) is needed because browsers can't call the brands' APIs directly (CORS).
Logos come from [Simple Icons](https://simpleicons.org) (CC0); the brand names and logos belong to their owners.
