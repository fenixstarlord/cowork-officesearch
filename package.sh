#!/bin/bash
set -e

echo "Packaging Office Search Cowork plugin..."

# Sync VERSION → plugin.json
VERSION=$(cat VERSION)
TMPFILE=$(mktemp)
jq --arg v "$VERSION" '.version = $v' .claude-plugin/plugin.json > "$TMPFILE" && mv "$TMPFILE" .claude-plugin/plugin.json
echo "Version: $VERSION"

zip -r officesearch.zip \
    .claude-plugin \
    CLAUDE.md \
    VERSION \
    commands/ \
    skills/ \
    agents/ \
    data/generate_html_report.py \
    data/generate_report.py \
    -x "*.pyc" "__pycache__/*" ".DS_Store" "data/output/*"

echo ""
echo "Created: officesearch.zip"
echo ""
echo "Upload this file in Claude Desktop:"
echo "  Cowork > Add Plugin > Personal > + > Upload plugin"
echo ""
echo "After install, add your Google Maps API key:"
echo "  echo 'GOOGLE_MAPS_API_KEY=your_key' > data/.env"
