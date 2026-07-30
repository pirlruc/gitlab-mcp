#!/usr/bin/env bash
# Pin Dockerfile FROM lines to current dhi.io digests (requires: docker login dhi.io).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKERFILE="${ROOT}/Dockerfile"
DEV_REF="${DHI_PYTHON_DEV:-dhi.io/python:3.13-debian13-dev}"
RT_REF="${DHI_PYTHON_RUNTIME:-dhi.io/python:3.13-debian13}"

digest_for() {
  local ref="$1"
  docker buildx imagetools inspect "${ref}" --format '{{.Manifest.Digest}}'
}

echo "Pulling ${DEV_REF} and ${RT_REF} ..."
docker pull "${DEV_REF}"
docker pull "${RT_REF}"

DEV_DIGEST="$(digest_for "${DEV_REF}")"
RT_DIGEST="$(digest_for "${RT_REF}")"
[[ "${DEV_DIGEST}" == sha256:* ]] || { echo "error: bad dev digest: ${DEV_DIGEST}" >&2; exit 1; }
[[ "${RT_DIGEST}" == sha256:* ]] || { echo "error: bad runtime digest: ${RT_DIGEST}" >&2; exit 1; }

python3 - "${DOCKERFILE}" "${DEV_REF}" "${DEV_DIGEST}" "${RT_REF}" "${RT_DIGEST}" <<'PY'
import pathlib, re, sys
path, dev_ref, dev_d, rt_ref, rt_d = sys.argv[1:]
text = pathlib.Path(path).read_text(encoding="utf-8")
text2, n1 = re.subn(
    r"^FROM dhi\.io/python:3\.13-debian13-dev(?:@sha256:[0-9a-f]+)? AS builder\s*$",
    f"FROM {dev_ref}@{dev_d} AS builder",
    text,
    count=1,
    flags=re.M,
)
text3, n2 = re.subn(
    r"^FROM dhi\.io/python:3\.13-debian13(?:@sha256:[0-9a-f]+)? AS runtime\s*$",
    f"FROM {rt_ref}@{rt_d} AS runtime",
    text2,
    count=1,
    flags=re.M,
)
if n1 != 1 or n2 != 1:
    sys.exit(f"error: expected one builder and one runtime FROM (got {n1}, {n2})")
pathlib.Path(path).write_text(text3, encoding="utf-8")
print(f"Pinned builder  {dev_ref}@{dev_d}")
print(f"Pinned runtime  {rt_ref}@{rt_d}")
PY
