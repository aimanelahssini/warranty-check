@echo off
rem Warranty Check: reads this PC's brand, model and serial number and opens the result. Nothing is installed.
powershell -NoProfile -Command "function q($x) { [uri]::EscapeDataString(([string]$x).Trim()) }; $p = Get-CimInstance Win32_ComputerSystemProduct; $m = if ($p.Vendor -match 'lenovo') { $p.Version } else { $p.Name }; $s = (Get-CimInstance Win32_BIOS).SerialNumber; if (-not $s) { $s = $p.IdentifyingNumber }; Start-Process ('https://warranty-check-alpha.vercel.app/es/?vendor=' + (q $p.Vendor) + '&model=' + (q $m) + '&serial=' + (q $s))"
