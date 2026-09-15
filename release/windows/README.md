# Windows desktop build

Assets:

- `CalligraphyStudio-Setup-0.4.0-x64.exe` — NSIS installer with Start Menu and desktop shortcuts.
- `CalligraphyStudio-Portable-0.4.0-x64.exe` — portable executable.

Direct download:

- Installer: https://github.com/styayur/calligraphy-studio/releases/latest/download/CalligraphyStudio-Setup-0.4.0-x64.exe
- Portable: https://github.com/styayur/calligraphy-studio/releases/latest/download/CalligraphyStudio-Portable-0.4.0-x64.exe

The desktop build is an Electron shell around the offline static Glyph Store. Search, batch typesetting, layers, similarity recommendations, JSON export and PNG export work without a server.

The current binaries are not code-signed with a commercial certificate, so Windows SmartScreen may show an unknown-publisher warning. Verify `SHA256SUMS.txt` before running.
