#!/usr/bin/env bash
# Stáhne písma s licencí SIL Open Font License z repozitáře google/fonts do src/assets/fonts.
# Když se stažení nepovede, aplikace použije výchozí písmo zařízení.
set -u
DIR="$(dirname "$0")/../src/assets/fonts"
mkdir -p "$DIR"
BASE="https://raw.githubusercontent.com/google/fonts/main/ofl"
curl -fsSL -o "$DIR/Cinzel.ttf" "$BASE/cinzel/Cinzel%5Bwght%5D.ttf" || echo "Cinzel se nestáhl"
curl -fsSL -o "$DIR/IMFellEnglishSC.ttf" "$BASE/imfellenglishsc/IMFeENsc28P.ttf" || echo "IM Fell se nestáhl"
curl -fsSL -o "$DIR/AlegreyaSans-Regular.ttf" "$BASE/alegreyasans/AlegreyaSans-Regular.ttf" || echo "Alegreya Sans se nestáhla"
ls -la "$DIR"
