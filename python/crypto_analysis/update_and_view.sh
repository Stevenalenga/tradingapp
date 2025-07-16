#!/bin/bash
echo "Updating cryptocurrency analysis..."
python3 update_crypto_analysis.py
echo "Opening analysis in browser..."

# Detect operating system and open browser accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open > /dev/null; then
        xdg-open index.html
    elif command -v gnome-open > /dev/null; then
        gnome-open index.html
    else
        echo "Could not detect the web browser to use. Please open index.html manually."
    fi
else
    echo "Unknown operating system. Please open index.html manually."
fi

echo "Done!"