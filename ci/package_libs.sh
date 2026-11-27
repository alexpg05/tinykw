#!/bin/bash
set -e

VERSION_TAG=$1

for plat_dir in libs/*/; do
    plat_dir="${plat_dir%/}" 
    plat_name="${plat_dir##*/}"
    DEPLOY_DIR="deploy_$plat_name"

    # copy header (cortex-m platforms have one per float ABI, all identical)
    mkdir -p "$DEPLOY_DIR/include"
    cp "$(find "$plat_dir" -name tinykw.h | head -1)" "$DEPLOY_DIR/include/"

    # copy lib (<lang>/ folders, or hard/ and soft/ folders for cortex-m platforms)
    mkdir -p "$DEPLOY_DIR/lib"
    for lang_dir in ${plat_dir}/*/; do
        lang_dir="${lang_dir%/}" 
        cp -r "$lang_dir" "$DEPLOY_DIR/lib/"
    done
    find "$DEPLOY_DIR/lib" -name tinykw.h -delete

    # copy license
    cp LICENSE "$DEPLOY_DIR/"

    cd $DEPLOY_DIR
    zip -r "../tinykw-${plat_name}-${VERSION_TAG}.zip" . -x "*.DS_Store"
    cd ..

    rm -rf "$DEPLOY_DIR"
done
