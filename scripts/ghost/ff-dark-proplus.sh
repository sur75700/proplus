#!/bin/bash

set -e

echo "🔎 Քայլ 1 — փնտրում եմ default Firefox profile-ը..."

PROFILES_INI="$HOME/.mozilla/firefox/profiles.ini"

if [ ! -f "$PROFILES_INI" ]; then
    echo "❌ ~/.mozilla/firefox/profiles.ini չկա — Firefox բացի մեկ անգամ, հետո փակի, նորից փորձենք։"
    exit 1
fi

PROFILE_PATH=$(awk -F= '
  /^\[Profile/ {p++}
  $1=="Path" {path[p]=$2}
  $1=="Default" && $2==1 {print path[p]}
' "$PROFILES_INI")

if [ -z "$PROFILE_PATH" ]; then
  PROFILE_PATH=$(awk -F= '$1=="Path" {print $2; exit}' "$PROFILES_INI")
fi

if [ -z "$PROFILE_PATH" ]; then
    echo "❌ Չհաջողվեց գտնել profile Path-ը profiles.ini-ից։"
    exit 1
fi

PROFILE_DIR="$HOME/.mozilla/firefox/$PROFILE_PATH"

echo "✅ Firefox profile: $PROFILE_DIR"

if [ ! -d "$PROFILE_DIR" ]; then
    echo "❌ Profile directory գոյություն չունի: $PROFILE_DIR"
    exit 1
fi

echo "📁 Քայլ 2 — ստեղծում եմ chrome/ պանակը..."
mkdir -p "$PROFILE_DIR/chrome"

CSS_FILE="$PROFILE_DIR/chrome/userContent.css"

echo "✍️ Քայլ 3 — գրում եմ GLOBAL DARK MODE CSS-ը -> $CSS_FILE"

cat > "$CSS_FILE" << 'EOF'
/* ===== ProPlus Global Dark Mode for ALL sites ===== */

:root, html, body {
    background-color: #000000 !important;
    color: #e0e0e0 !important;
}

body, div, section, article, main, header, footer, nav, aside {
    background-color: #000000 !important;
    color: #e0e0e0 !important;
}

[class*="card"], [class*="panel"], [class*="popup"], [class*="modal"],
[class*="content"], [class*="container"], [class*="wrapper"] {
    background-color: #050505 !important;
    color: #e5e5e5 !important;
    border-color: #222 !important;
}

a, a span {
    color: #4ea3ff !important;
}
a:hover {
    color: #82c4ff !important;
}

button, [role="button"], input[type="button"],
input[type="submit"], input[type="reset"] {
    background-color: #111 !important;
    color: #f5f5f5 !important;
    border: 1px solid #333 !important;
}
button:hover {
    background-color: #222 !important;
}

input, textarea, select {
    background-color: #050505 !important;
    color: #f0f0f0 !important;
    border: 1px solid #333 !important;
}

input::placeholder, textarea::placeholder {
    color: #777 !important;
}

table, thead, tbody, tr, th, td {
    background-color: #000 !important;
    color: #dedede !important;
    border-color: #333 !important;
}

* {
    box-shadow: none !important;
}

img, video, canvas {
    background-color: transparent !important;
}

*[style*="background: #fff"],
*[style*="background: #ffffff"],
*[style*="background-color: #fff"],
*[style*="background-color: #ffffff"] {
    background-color: #050505 !important;
    color: #e0e0e0 !important;
}
EOF

echo "🧠 Քայլ 4 — միացնում եմ stylesheet–ների support-ը user.js–ով..."

USER_JS="$PROFILE_DIR/user.js"

if grep -q "toolkit.legacyUserProfileCustomizations.stylesheets" "$USER_JS" 2>/dev/null; then
  sed -i 's/user_pref("toolkit.legacyUserProfileCustomizations.stylesheets".*/user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);/' "$USER_JS"
else
  echo 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' >> "$USER_JS"
fi

echo "✅ Ամեն ինչ OK!"
echo "♻️ Փակիր Firefox-ը լրիվ (բոլոր պատուհանները) ու նորից բացիր։"
echo "Instagram / ChatGPT / Telegram Web / GitHub պիտի լինեն սև ֆոնի վրա։"
