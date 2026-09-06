# Prebuilt foreign binary: no build-id or debuginfo can be produced, and
# disabling the debug package also skips brp-strip, which would otherwise
# rewrite the upstream blob. The binary ships as-is from the release RPM.
%global debug_package %{nil}

# add-determinism's brp hook (add-det) would regenerate /usr/lib/.build-id
# links from the blob's ELF build-id notes and otherwise normalize the
# payload. The blob must ship byte-identical, so unset the hook (consistent
# with %%global debug_package %%{nil} above).
%undefine __brp_add_determinism

# The bundled Chromium libs under /opt/Bitwarden carry SONAMEs, so the
# dependency generator would advertise them as system providers
# (e.g. libvulkan.so.1). They are private to the bundle (resolved via the
# $ORIGIN RPATH on bitwarden-app, not the system loader path), so suppress
# Provides from /opt.
%global __provides_exclude_from ^/opt/Bitwarden/
# bitwarden-app links the bundled libffmpeg.so (found via its $ORIGIN
# RPATH). Nothing in Fedora provides it, and the bundle satisfies it
# internally, so exclude it. The generated require string carries the arch
# qualifier (libffmpeg.so()(64bit)), hence the prefix match without $.
# Every other DT_NEEDED entry is a system library and stays auto-detected.
%global __requires_exclude ^libffmpeg\.so

Name:           bitwarden
Version:        2026.8.0
Release:        %autorelease
Summary:        A secure and free password manager for all of your devices
License:        GPL-3.0-only
URL:            https://bitwarden.com
ExclusiveArch:  x86_64

Source0:        https://github.com/bitwarden/clients/releases/download/desktop-v%{version}/Bitwarden-%{version}-x86_64.rpm
# Upstream prebuilt RPM ships no GPL text (only Electron/Chromium notices
# under /opt). spectool fetches LICENSE_GPL.txt for the exact version being
# packaged from the release tag; a failed fetch fails the build, so the
# packaged license always matches the packaged version. The desktop sources
# default to GPL-3.0 per the repo's LICENSE.txt ("GPL-3.0 unless the header
# specifies another license"; Bitwarden-licensed files live only in
# /bitwarden_license).
Source1:        https://raw.githubusercontent.com/bitwarden/clients/desktop-v%{version}/LICENSE_GPL.txt
# Upstream ships no AppStream metadata at all, so this repo ships a curated
# file under the RDNS id com.bitwarden.desktop (the id Bitwarden itself
# uses; it matches the Icon and StartupWMClass in bitwarden.desktop). CI patches the
# <release> version/date on each new upstream release.
Source2:        com.bitwarden.desktop.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  cpio

# Runtime-only deps the ELF dependency generator cannot see. Everything
# linked (gtk3, nss, cups, alsa, at-spi2, dbus, ...) is auto-detected from
# DT_NEEDED and deliberately not duplicated here:
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libnotify, libXScrnSaver: declared by the upstream RPM; not in any
#   DT_NEEDED (loaded indirectly), kept at parity so notifications and idle
#   detection behave as upstream ships them.
# - (libXtst or libXtst6), (libuuid or libuuid1): upstream-declared with
#   distro alternatives; Fedora satisfies them via libXtst and libuuid.
Requires:       xdg-utils
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       (libXtst or libXtst6)
Requires:       (libuuid or libuuid1)

%description
Bitwarden is a secure and free password manager for all of your devices.
Store, share and sync logins, cards and identities with end-to-end
encryption. This package rewraps the upstream prebuilt Linux RPM for
Fedora (COPR only).

%prep
rpm2cpio %{SOURCE0} | cpio -idmu
cp %{SOURCE1} LICENSE_GPL.txt

%build
# Nothing to compile: the prebuilt upstream binary is unpacked in %%prep.
# The section exists so rpm's build hooks (e.g. macro-injected steps) run.

%install
cp -a opt %{buildroot}/
cp -a usr %{buildroot}/
install -Dm0644 %{SOURCE2} %{buildroot}%{_metainfodir}/com.bitwarden.desktop.metainfo.xml
# Upstream ships no /usr/bin entry (Exec= points at /opt directly). Add one
# symlink so `bitwarden` is on PATH. Safe by upstream's own design: the
# /opt/Bitwarden/bitwarden wrapper resolves `readlink -f "$0"` ("might be
# behind symlink") and execs the Electron binary by absolute path, so
# launching via the symlink behaves identically. The blob itself is
# untouched; this symlink is the single documented delta.
install -d %{buildroot}%{_bindir}
ln -s /opt/Bitwarden/bitwarden %{buildroot}%{_bindir}/bitwarden

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/bitwarden.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/com.bitwarden.desktop.metainfo.xml

%files
%license LICENSE_GPL.txt
%{_bindir}/bitwarden
/opt/Bitwarden/
%{_datadir}/applications/bitwarden.desktop
%{_datadir}/icons/hicolor/*/apps/bitwarden.png
%{_metainfodir}/com.bitwarden.desktop.metainfo.xml
# Release is %%autorelease: COPR's rpmautospec sets it to the changelog entry
# count. To rebuild the same upstream version with a spec change, append a new
# %%changelog entry — Release bumps automatically and the NVR stays unique.

%changelog
* Sun Sep 06 2026 Anudeep D <anudeepd2@gmail.com> - 2026.8.0-1
- Initial Fedora repackaging of upstream prebuilt RPM
