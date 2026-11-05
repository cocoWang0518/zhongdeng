#!/usr/bin/env bash
set -euo pipefail

IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TMP_DIR=""

EXPORT_PATHS=(
  "api"
  "web"
  "ketiyi_yewushifan.py"
  "main.py"
  "new_main.py"
  "api.py"
  "run.py"
)

usage() {
  cat >&2 <<'EOF'
Usage:
  export_source.sh save
  export_source.sh load xxx.tar some/path/source
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${TMP_DIR}" && -d "${TMP_DIR}" ]]; then
    rm -rf -- "${TMP_DIR}"
  fi
}

trap cleanup EXIT

abs_file_path() {
  local path="$1"
  local dir
  local base

  dir="$(dirname -- "${path}")"
  base="$(basename -- "${path}")"
  dir="$(cd -- "${dir}" && pwd -P)"

  printf '%s/%s\n' "${dir}" "${base}"
}

require_paths() {
  local root="$1"
  local rel

  for rel in "${EXPORT_PATHS[@]}"; do
    if [[ ! -e "${root}/${rel}" ]]; then
      die "missing required path: ${root}/${rel}"
    fi
  done
}

validate_tar_entries() {
  local archive="$1"
  local entry
  local entries

  entries="$(LC_ALL=C tar -tf "${archive}")" || die "cannot read tar archive: ${archive}"

  while IFS= read -r entry; do
    [[ -z "${entry}" ]] && continue

    case "${entry}" in
      /*|..|../*|*/..|*/../*)
        die "unsafe tar entry: ${entry}"
        ;;
    esac
  done <<< "${entries}"
}

save_source() {
  if [[ "$#" -ne 0 ]]; then
    usage
    die "save does not accept extra arguments"
  fi

  require_paths "${SCRIPT_DIR}"

  local output_tar
  output_tar="$(pwd -P)/source_export_$(date +%Y%m%d_%H%M%S).tar"

  if [[ -e "${output_tar}" ]]; then
    die "output file already exists: ${output_tar}"
  fi

  LC_ALL=C COPYFILE_DISABLE=1 tar -cf "${output_tar}" \
    --exclude='*/__pycache__' \
    --exclude='*/__pycache__/*' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='*/.DS_Store' \
    -C "${SCRIPT_DIR}" \
    "${EXPORT_PATHS[@]}"

  printf '%s\n' "${output_tar}"
}

load_source() {
  if [[ "$#" -ne 2 ]]; then
    usage
    die "load requires a tar archive and a target project root"
  fi

  local archive="$1"
  local target_root="$2"
  local rel

  [[ -f "${archive}" ]] || die "tar archive does not exist: ${archive}"
  [[ -d "${target_root}" ]] || die "target project root does not exist: ${target_root}"

  archive="$(abs_file_path "${archive}")"
  target_root="$(cd -- "${target_root}" && pwd -P)"

  validate_tar_entries "${archive}"

  TMP_DIR="$(mktemp -d)"
  LC_ALL=C tar -xf "${archive}" -C "${TMP_DIR}" || die "failed to extract tar archive: ${archive}"

  require_paths "${TMP_DIR}"

  for rel in "${EXPORT_PATHS[@]}"; do
    rm -rf -- "${target_root}/${rel}"

    if [[ -d "${TMP_DIR}/${rel}" && ! -L "${TMP_DIR}/${rel}" ]]; then
      cp -Rp -- "${TMP_DIR}/${rel}" "${target_root}/${rel}"
    else
      cp -p -- "${TMP_DIR}/${rel}" "${target_root}/${rel}"
    fi
  done

  echo "Loaded source into: ${target_root}"
}

main() {
  if [[ "$#" -lt 1 ]]; then
    usage
    exit 1
  fi

  local command="$1"
  shift

  case "${command}" in
    save)
      save_source "$@"
      ;;
    load)
      load_source "$@"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      usage
      die "unknown command: ${command}"
      ;;
  esac
}

main "$@"
