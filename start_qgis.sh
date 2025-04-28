#!/usr/bin/env bash
echo "🪛 Running QGIS with the GEA profile:"
echo "--------------------------------"
echo "Do you want to enable debug mode?"
choice=$(gum choose "🪲 Yes" "🐞 No" )
case $choice in
	"🪲 Yes") DEBUG_MODE=1 ;;
	"🐞 No") DEBUG_MODE=0 ;;
esac

python admin.py --qgis-profile=GEA build
python admin.py --qgis-profile=GEA install

# Running on local used to skip tests that will not work in a local dev env
GEA_LOG=$HOME/GEA.log
rm -f $GEA_LOG
#nix-shell -p \
#  This is the old way using default nix packages with overrides
#  'qgis.override { extraPythonPackages = (ps: [ ps.pyqtwebengine ps.jsonschema ps.debugpy ps.future ps.psutil ]);}' \
#  --command "GEEST_LOG=${GEEST_LOG} GEEST_DEBUG=${DEBUG_MODE} RUNNING_ON_LOCAL=1 qgis --profile GEA"

# This is the new way, using Ivan Mincis nix spatial project and a flake
# see flake.nix for implementation details
GEA_LOG=${GEA_LOG} GEA_DEBUG=${DEBUG_MODE} RUNNING_ON_LOCAL=1 \
      nix run .#default -- qgis --profile GEA
