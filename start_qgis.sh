#!/usr/bin/env bash
echo "🪛 Running QGIS with the GEA profile:"
echo "--------------------------------"
# Default to interactive unless overridden


DEBUG_MODE=0
SHOW_HELP=0

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--debug)
      DEBUG_MODE=1
      shift
      ;;
    --no-debug)
      DEBUG_MODE=0
      shift
      ;;
    -h|--help)
      SHOW_HELP=1
      shift
      ;;
    *)
      echo "❌ Unknown option: $1"
      SHOW_HELP=1
      shift
      ;;
  esac
done

if [[ $SHOW_HELP -eq 1 ]]; then
  echo "Usage: $0 [--debug | --no-debug] [--help]"
  exit 1
fi

# Interactive debug prompt if not passed via args
if [ -z "$DEBUG_MODE" ]; then
  echo "Do you want to enable debug mode?"
  choice=$(gum choose "🪲 Yes" "🐞 No" )
  case $choice in
    "🪲 Yes") DEBUG_MODE=1 ;;
    "🐞 No") DEBUG_MODE=0 ;;
  esac
fi

python admin.py --qgis-profile=GEA build
python admin.py --qgis-profile=GEA install

# Running on local used to skip tests that will not work in a local dev env
GEA_LOG=$HOME/GEA.log
rm -f $GEA_LOG
#nix-shell -p \
#  This is the old way using default nix packages with overrides
#  'qgis.override { extraPythonPackages = (ps: [ ps.pyqtwebengine ps.jsonschema ps.debugpy ps.future ps.psutil ]);}' \
#  --command "GEEST_LOG=${GEEST_LOG} GEEST_DEBUG=${DEBUG_MODE} RUNNING_ON_LOCAL=1 qgis --profile GEA"

# This is the new way, using Ivan Mincik's nix spatial project and a flake
# see flake.nix for implementation details
GEA_LOG=${GEA_LOG} GEA_DEBUG=${DEBUG_MODE} RUNNING_ON_LOCAL=1 \
      nix run .#default -- --profile GEA
