#!/bin/sh

## The main app source and output name
main="src/index.js Neovim"
## Library sources and their output names
libs="
node_modules/jxa-filesystem/src/index.js filesystem
node_modules/jxa-path/src/index.js path
"
## Where to install libraries.
## You can embed them into the main app,
## install for a current user,
## or system wide
## app | user | system
lib_install_mode="app"
## Whether libraries should be compiled
## as scripts or bundles
## script | bundle
lib_comp_mode="script"

# libs="${libs// /}"
## Remove empty lines
libs=$(sed '/^[[:space:]]*$/d' <<< "$libs")
main=$(sed '/^[[:space:]]*$/d' <<< "$main")

read -r main output <<< "$main"
output="${output}.app"
# echo "main: ${main}, output: ${output}"

if [ -e "$output" ]; then
  rm -r "$output"
fi

osacompile -l JavaScript -o "$output" "$main"

if [ -e "$output" -a -n "$libs" ]; then
  lib_dest=""
  case "$lib_install_mode" in
    "app")
      lib_dest="${output}/Contents/Resources/Script Libraries" 
      ;;
    "user")
      lib_dest=~/Library/Script\ Libraries
      ;;
    "system")
      lib_dest=/Library/Script\ Libraries
      ;;
    *)
      echo "Unknown library installation mode: $lib_install_mode"
      exit 1
      ;;
  esac

  lib_file_ext=""
  case "$lib_comp_mode" in
    "script")
      lib_file_ext="scpt"
      ;;
    "bundle")
      lib_file_ext="scptd"
      ;;
    *)
      echo "Unknown library compilation mode: $lib_comp_mode"
      exit 1
      ;;
  esac

  mkdir -p "$lib_dest" > /dev/null 2>&1

  echo "$libs" | while read -r lib lib_output; do
    osacompile -l JavaScript -o "${lib_dest}/${lib_output}.${lib_file_ext}" "$lib"
    # osacompile -l JavaScript "$lib"
  # echo "lib: ${lib}, name: ${lib_output}"
  done
fi
