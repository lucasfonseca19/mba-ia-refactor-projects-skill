#!/bin/bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
HOME_ROOT="$(cd "$HOME" && pwd -P)"
TEMP_ROOT="$(mktemp -d /private/tmp/task-manager-tests.XXXXXXXX)"
trap 'rm -rf "$TEMP_ROOT"' EXIT
APP_ROOT="$TEMP_ROOT/app"
mkdir -p "$APP_ROOT"
if [[ ! -x "$SOURCE_ROOT/.venv/bin/python" ]]; then
  echo 'Prepare a .venv antes de executar os testes.' >&2
  exit 1
fi
COPYFILE_DISABLE=1 tar -C "$SOURCE_ROOT" --exclude=.venv --exclude=.agents --exclude=instance --exclude=__pycache__ --exclude=.DS_Store -cf - . | tar -C "$APP_ROOT" -xf -
cp -R "$SOURCE_ROOT/.venv" "$APP_ROOT/.venv"
cat > "$TEMP_ROOT/profile.sb" <<'EOF'
(version 1)
(allow default)
(deny file-read* file-write* (subpath (param "HOME_ROOT")))
(deny file-read* file-write* (subpath (param "SOURCE_ROOT")))
(deny file-write* (require-not (subpath (param "TEMP_ROOT"))))
(deny network*)
EOF
sandbox() {
  /usr/bin/sandbox-exec -D "HOME_ROOT=$HOME_ROOT" -D "SOURCE_ROOT=$SOURCE_ROOT" -D "TEMP_ROOT=$TEMP_ROOT" -f "$TEMP_ROOT/profile.sb" "$@"
}
sandbox /usr/bin/touch "$TEMP_ROOT/probe"
if sandbox /bin/cat "$SOURCE_ROOT/app.py" > /dev/null 2>&1; then
  echo 'A barreira não bloqueou o projeto original; testes interrompidos.' >&2
  exit 1
fi
cd "$APP_ROOT"
sandbox "$APP_ROOT/.venv/bin/python" -I -B "$APP_ROOT/tests/run_isolated.py"
