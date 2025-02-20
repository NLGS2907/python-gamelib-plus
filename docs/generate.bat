:: Generate html documentation from source code
pdoc3 --force --html --template-dir docs/templates gamelib -o docs

:: post process -- remove unnecessary class prefix and rename index file
bash -c "sed -i 's/_GameThread\.//g' docs/gamelib.html > docs/index.html && mv -f docs/gamelib.html docs/index.html"
