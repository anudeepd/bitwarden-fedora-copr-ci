# bitwarden-fedora-copr-ci

[Bitwarden](https://github.com/bitwarden/clients) is a secure and free password manager for all of your devices.

This repo packages Bitwarden Desktop for Fedora by rewrapping the upstream prebuilt Linux RPM (`Bitwarden-X.Y.Z-x86_64.rpm`) with a Fedora spec. Currently x86_64 only, matching upstream's prebuilt release artifacts. A GitHub Actions workflow runs daily at 12AM UTC to check the latest `desktop-v*` release from https://github.com/bitwarden/clients (a monorepo, so tags are filtered by the `desktop-v` prefix) and rebuilds COPR only when a new version is published. The downloaded RPM is verified against the sha512 published for that asset in the upstream release's `latest-linux.yml` before submission.

The COPR project repository is available from: https://copr.fedorainfracloud.org/coprs/anudeepd/bitwarden

## Packaging compliance

This package is distributed via COPR only. It rewraps the upstream prebuilt
binary RPM, so it is **not eligible for the official Fedora repositories**:
the Fedora Packaging Guidelines require all binaries to be built from source
in the Fedora build system, and this repo intentionally ships the upstream
blob as-is (see `specs/bitwarden.spec`).

Everything else follows the guidelines:

- `ExclusiveArch: x86_64` — matches upstream's prebuilt artifacts.
- `%build` present (empty — nothing to compile) so rpm's build hooks run.
- `%check` runs `desktop-file-validate` and `appstreamcli validate` on the
  packaged files inside the build.
- `rpmlint` runs in CI on the built RPM with **0 errors, 0 warnings**:
  every flagged pattern is inherent to rewrapping the Electron blob
  (the `/opt` layout, required `$ORIGIN` RPATHs, unstripped prebuilt
  binaries, the non-setuid `chrome-sandbox` tripping the setgroups pattern,
  Chromium's legacy `gethostbyname` call, dictionary misses, GUI app
  without man page, docs not bundled by design, and the two
  upstream-declared lib deps invisible to the generator) and is filtered
  in `rpmlintrc` with per-filter rationales.
- `%{_bindir}`, `%{_datadir}`, `%{_metainfodir}` macros used in `%files`.
- License provenance: the GPL license text is fetched from the upstream
  release tag by `spectool` (the prebuilt RPM ships only Electron/Chromium
  notices); a fetch failure fails the build, so the packaged license always
  matches the packaged version. `License: GPL-3.0-only` (SPDX) matches the
  upstream RPM (`GPL-3.0`) and the desktop sources, which default to GPL-3.0
  per the repo's `LICENSE.txt`. Nothing else is bundled: upstream payload
  plus license and curated metainfo.
- `%global debug_package %{nil}` with an explicit rationale: the prebuilt
  foreign binary cannot produce debuginfo, and disabling the debug package
  also skips `brp-strip`, which would otherwise rewrite the upstream blob.
  The `add-det` brp hook is disabled for the same reason: the blob must ship
  byte-identical.
- One minimal, documented transformation: upstream ships no `/usr/bin`
  entry (`Exec=` points at `/opt` directly), so the spec adds a single
  `/usr/bin/bitwarden` symlink so the app is on PATH. Safe by upstream's
  own design: the `/opt/Bitwarden/bitwarden` wrapper resolves
  `readlink -f "$0"` ("might be behind symlink") and execs the Electron
  binary by absolute path, so launching via the symlink behaves identically.
- Upstream ships no AppStream metadata at all, so this repo ships a curated
  `com.bitwarden.desktop.metainfo.xml` (RDNS id matching
  `Icon`/`StartupWMClass`); the upstream desktop file and icons are kept
  as-is.
- Dependencies: everything the blob links (gtk3, nss, cups, alsa, at-spi2,
  dbus, …) is auto-detected from `DT_NEEDED`. Explicitly listed are only
  what the generator cannot see: `xdg-utils` (shelled out to at runtime),
  `libnotify` and `libXScrnSaver` (upstream-declared, loaded indirectly),
  and upstream's distro-alternative deps `(libXtst or libXtst6)` and
  `(libuuid or libuuid1)`. Two generator exclusions, both documented in the
  spec: `Provides` from `/opt/Bitwarden` are suppressed (bundled Chromium
  libs carry SONAMEs but are private, resolved via `$ORIGIN`), and the
  `libffmpeg.so` requirement is excluded (bundled lib satisfied in-bundle
  via the same `$ORIGIN` RPATH). No network access inside the buildroot.
- The downloaded RPM is verified against the sha512 published for that
  asset in the upstream release's `latest-linux.yml` before submission to
  COPR. Note this is same-origin integrity (guards corruption/mismatch, not
  a signing boundary): upstream publishes no detached checksums or
  signatures for the RPM.

# Instructions

Enable the COPR repository then install the package.

<pre>
sudo dnf copr enable anudeepd/bitwarden
sudo dnf install bitwarden
</pre>

## Credits

Pattern and workflow structure adapted from
[anudeepd/ente-auth-fedora-copr-ci](https://github.com/anudeepd/ente-auth-fedora-copr-ci)
(which itself was adapted from
[anudeepd/iloader-fedora-copr-ci](https://github.com/anudeepd/iloader-fedora-copr-ci),
in turn adapted from
[DeltaCopy/waterfox-fedora-copr-ci](https://github.com/DeltaCopy/waterfox-fedora-copr-ci))
— thanks for the clean reference implementation.

<h3> COPR build status </h3>

[![Copr build status](https://copr.fedorainfracloud.org/coprs/anudeepd/bitwarden/package/bitwarden/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/anudeepd/bitwarden/package/bitwarden/)

<h3> GitHub action workflow status </h3>

[![bitwarden Fedora COPR CI](https://github.com/anudeepd/bitwarden-fedora-copr-ci/actions/workflows/bitwarden-ci.yml/badge.svg)](https://github.com/anudeepd/bitwarden-fedora-copr-ci/actions/workflows/bitwarden-ci.yml)

## Latest version
<a href="https://github.com/bitwarden/clients/releases?q=desktop-v&expanded=true">
  <img src="https://img.shields.io/github/v/release/bitwarden/clients?filter=desktop-v*&label=bitwarden-desktop" alt="bitwarden desktop latest release">
</a>
