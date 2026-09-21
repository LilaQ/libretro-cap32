# CAP32 mit CPC-/Plus-Korrekturen

Vollständiger Windows-x64-Core auf Basis von libretro/libretro-cap32 `e9ad182`, mit Korrekturen für Plus-Spritekoordinaten, Plus-Rasterinterrupts und SEEK/RECALIBRATE bei ausgeschaltetem Diskettenmotor. Alle bisherigen emulierten Modelle bleiben enthalten.

## In RetroArch verwenden

RetroArch schließen, die bisherige `cores/cap32_libretro.dll` sichern und durch die mitgelieferte Datei ersetzen. Vorhandene Core-Info, LaunchBox-Aufrufe und Einstellungen weiterverwenden. Für CPR-Cartridges weiterhin das Plus-Modell auswählen. Die Dateien des Nutzers wurden nicht verändert und sind nicht im Paket enthalten.

## Windows-x64-Build

In einer MSYS2-MINGW64-Shell im entpackten Quellverzeichnis:

```sh
pacman -S --needed make mingw-w64-x86_64-gcc
make -j8 platform=win CC=gcc CXX=g++ AR=ar GIT_VERSION=-e9ad182-cpcfix all
strip --strip-unneeded cap32_libretro.dll
```

Der mitgelieferte Core wurde auf macOS ARM64 mit MinGW-w64/GCC 16.2.0 erzeugt:

```sh
mkdir -p work/tmp
env TMPDIR="$PWD/work/tmp" make -j12 platform=win \
  CC=x86_64-w64-mingw32-gcc CXX=x86_64-w64-mingw32-g++ \
  AR=x86_64-w64-mingw32-ar GIT_VERSION=-e9ad182-cpcfix all
x86_64-w64-mingw32-strip --strip-unneeded cap32_libretro.dll
```

Bei einem Plattformwechsel vorher `make clean-objs` verwenden. Der vollständige Quellcode samt ursprünglichen Lizenzhinweisen liegt im beiliegenden `cap32-source.tar.gz`. Die kombinierte Änderung liegt zusätzlich als `cap32-fixes.patch` bei.

## Fokussierte Hardwareprüfungen auf macOS

Der ROM-freie Prüflauf verwendet die im nativen Core exportierten internen Symbole und benötigt weder RetroArch noch Spieldateien:

```sh
make clean-objs
make -j8 platform=osx all
clang -O2 -Icap32 unit-tests/cpc-hardware.c -o cpc-hardware
./cpc-hardware "$PWD/cap32_libretro.dylib"
```

## Lizenz

Ursprüngliche Lizenz- und Copyright-Hinweise gelten unverändert. Siehe `cap32/COPYING.txt`, die Dateiköpfe unter `libretro/`, `libretro-common/` und die übrigen Hinweise im vollständigen Quellcode. Der libretro-Teil enthält insbesondere eine Beschränkung kommerzieller Weiterverwendung. Dieses Paket enthält keine vom Nutzer bereitgestellten Spiele.
