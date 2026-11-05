import os
import re
import subprocess
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

db_bp = Blueprint("db", __name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "sql"
TERMINAL_STATUSES = {"success", "error", "canceled"}

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env.local", override=True)

_job_lock = threading.Lock()
_jobs = {}
_current_job_id = None


class JobCanceled(RuntimeError):
    pass


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get_db_config():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "db"),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
    }


def _validate_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", identifier):
        raise ValueError(f"invalid database identifier: {identifier}")
    return identifier


def _validate_charset(charset: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", charset):
        raise ValueError(f"invalid charset: {charset}")
    return charset


def _serialize_job(job):
    if not job:
        return None
    return {key: value for key, value in job.items() if not key.startswith("_")}


def _get_current_job():
    with _job_lock:
        if not _current_job_id:
            return None
        return _serialize_job(_jobs.get(_current_job_id))


def _get_job(job_id):
    with _job_lock:
        return _serialize_job(_jobs.get(job_id))


def _set_job_fields(job_id, **fields):
    with _job_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job.update(fields)


def _job_cancel_requested(job_id):
    with _job_lock:
        job = _jobs.get(job_id)
        return bool(job and job.get("cancel_requested"))


def _complete_job(job_id, status, message="", **fields):
    global _current_job_id

    with _job_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job.update(
            {
                "status": status,
                "message": message,
                "finished_at": _now_iso(),
                "_process": None,
                "pid": None,
                **fields,
            }
        )
        if _current_job_id == job_id:
            _current_job_id = None
        _prune_finished_jobs_unlocked()


def _prune_finished_jobs_unlocked():
    finished_job_ids = [
        job_id
        for job_id, job in _jobs.items()
        if job.get("status") in TERMINAL_STATUSES
    ]
    for job_id in finished_job_ids[:-20]:
        _jobs.pop(job_id, None)


def _read_log_tail(log_path: Path, limit=8192):
    if not log_path.exists():
        return ""
    return log_path.read_bytes()[-limit:].decode("utf-8", errors="replace").strip()


def _resolve_sql_file(filename: str) -> Path:
    if not filename or Path(filename).name != filename:
        raise ValueError("invalid sql filename")

    sql_file = SQL_DIR / filename
    if sql_file.suffix.lower() != ".sql" or not sql_file.is_file():
        raise FileNotFoundError(f"sql file not found: {filename}")
    return sql_file


def _resolve_sql_files(filename=None, filenames=None):
    raw_filenames = filenames if filenames is not None else [filename]
    if not isinstance(raw_filenames, list):
        raise ValueError("filenames must be a list")

    sql_files = []
    seen = set()
    for raw_filename in raw_filenames:
        if not isinstance(raw_filename, str):
            raise ValueError("invalid sql filename")

        sql_file = _resolve_sql_file(raw_filename)
        if sql_file.name in seen:
            continue

        seen.add(sql_file.name)
        sql_files.append(sql_file)

    if not sql_files:
        raise ValueError("请选择要运行的 SQL 文件")

    return sql_files


def _list_sql_files():
    if not SQL_DIR.exists():
        return []

    scripts = []
    for index, sql_file in enumerate(
        sorted(
            (path for path in SQL_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".sql"),
            key=lambda path: path.name,
        ),
        start=1,
    ):
        stat = sql_file.stat()
        scripts.append(
            {
                "index": index,
                "name": sql_file.name,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ).isoformat(timespec="seconds"),
                "is_empty": stat.st_size == 0,
            }
        )
    return scripts


def _reset_database(cfg: dict):
    db_name = _validate_identifier(cfg["database"])
    db_charset = _validate_charset(cfg["charset"])
    admin_conn = None

    try:
        admin_conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            charset=cfg["charset"],
            autocommit=True,
        )

        with admin_conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET {db_charset}")
            cursor.execute("SET GLOBAL max_allowed_packet = 268435456")
    finally:
        if admin_conn is not None:
            admin_conn.close()


def _set_max_allowed_packet(cfg: dict):
    admin_conn = None
    try:
        admin_conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            charset=cfg["charset"],
            autocommit=True,
        )
        with admin_conn.cursor() as cursor:
            cursor.execute("SET GLOBAL max_allowed_packet = 268435456")
    finally:
        if admin_conn is not None:
            admin_conn.close()


def _import_sql_file_with_client(cfg: dict, db_name: str, sql_file: Path, job_id: str):
    env = os.environ.copy()
    if cfg["password"]:
        env["MYSQL_PWD"] = cfg["password"]

    cmd = [
        "mariadb",
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--user={cfg['user']}",
        f"--default-character-set={cfg['charset']}",
        "--binary-mode",
        "--max_allowed_packet=256M",
        db_name,
    ]

    log_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as log_fp:
            log_path = Path(log_fp.name)
            with sql_file.open("rb") as fp:
                process = subprocess.Popen(
                    cmd,
                    stdin=fp,
                    stdout=log_fp,
                    stderr=log_fp,
                    env=env,
                )
                _set_job_fields(job_id, _process=process, pid=process.pid)
                return_code = process.wait()
                log_fp.flush()

        log_tail = _read_log_tail(log_path)
        _set_job_fields(job_id, return_code=return_code, log_tail=log_tail)

        if return_code != 0:
            if _job_cancel_requested(job_id):
                raise JobCanceled("已取消运行")
            raise RuntimeError(log_tail or f"mariadb import failed: exit code {return_code}")

        if _job_cancel_requested(job_id):
            raise JobCanceled("已取消运行")
    finally:
        _set_job_fields(job_id, _process=None, pid=None)
        if log_path is not None:
            log_path.unlink(missing_ok=True)


def _run_job(job_id: str):
    job = _get_job(job_id)
    if not job:
        return

    try:
        cfg = _get_db_config()
        db_name = _validate_identifier(cfg["database"])

        if _job_cancel_requested(job_id):
            raise JobCanceled("已取消运行")

        if job["action"] == "clear_db":
            _set_job_fields(job_id, message="正在清空并重建数据库")
            _reset_database(cfg)
            _complete_job(job_id, "success", "数据库已清空并重建")
            return

        if job["action"] == "run_sql":
            sql_files = _resolve_sql_files(filenames=job.get("filenames"))
            completed_filenames = []
            packet_configured = False
            total = len(sql_files)

            for index, sql_file in enumerate(sql_files, start=1):
                if _job_cancel_requested(job_id):
                    raise JobCanceled("已取消运行")

                _set_job_fields(
                    job_id,
                    filename=sql_file.name,
                    message=f"正在运行第 {index}/{total} 个：{sql_file.name}",
                )

                if sql_file.stat().st_size == 0:
                    completed_filenames.append(sql_file.name)
                    _set_job_fields(
                        job_id,
                        completed_filenames=completed_filenames.copy(),
                        message=f"{sql_file.name} 为空，已跳过",
                    )
                    continue

                if not packet_configured:
                    _set_max_allowed_packet(cfg)
                    packet_configured = True

                _import_sql_file_with_client(cfg, db_name, sql_file, job_id)
                completed_filenames.append(sql_file.name)
                _set_job_fields(
                    job_id,
                    completed_filenames=completed_filenames.copy(),
                )

            _complete_job(job_id, "success", f"已完成 {total} 个 SQL 文件")
            return

        raise ValueError(f"unsupported job action: {job['action']}")
    except JobCanceled as exc:
        _complete_job(job_id, "canceled", str(exc))
    except Exception as exc:
        _complete_job(job_id, "error", str(exc))


def _start_job(action: str, filename=None, filenames=None):
    global _current_job_id

    cfg = _get_db_config()
    db_name = _validate_identifier(cfg["database"])
    resolved_filenames = []

    if action == "run_sql":
        sql_files = _resolve_sql_files(filename=filename, filenames=filenames)
        resolved_filenames = [sql_file.name for sql_file in sql_files]
        filename = resolved_filenames[0] if len(resolved_filenames) == 1 else None
    elif action != "clear_db":
        raise ValueError(f"unsupported job action: {action}")

    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "action": action,
        "filename": filename,
        "filenames": resolved_filenames,
        "completed_filenames": [],
        "database": db_name,
        "status": "running",
        "message": "任务已创建",
        "started_at": _now_iso(),
        "finished_at": None,
        "cancel_requested": False,
        "pid": None,
        "return_code": None,
        "log_tail": "",
        "_process": None,
    }

    with _job_lock:
        if _current_job_id:
            current_job = _jobs.get(_current_job_id)
            if current_job and current_job.get("status") not in TERMINAL_STATUSES:
                return None
            _current_job_id = None

        _jobs[job_id] = job
        _current_job_id = job_id

    thread = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    thread.start()
    return _serialize_job(job)


@db_bp.route("/init/db/api/scripts", methods=["GET"])
def list_db_scripts():
    try:
        cfg = _get_db_config()
        db_name = _validate_identifier(cfg["database"])
        return jsonify(
            {
                "status": "success",
                "database": db_name,
                "scripts": _list_sql_files(),
                "current_job": _get_current_job(),
            }
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@db_bp.route("/init/db/api/jobs", methods=["POST"])
def create_db_job():
    try:
        payload = request.get_json(silent=True) or {}
        action = payload.get("action")
        filename = payload.get("filename")
        filenames = payload.get("filenames")

        job = _start_job(action, filename=filename, filenames=filenames)
        if job is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "已有数据库任务正在运行",
                        "current_job": _get_current_job(),
                    }
                ),
                409,
            )

        return jsonify({"status": "success", "job": job}), 202
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@db_bp.route("/init/db/api/jobs/<job_id>", methods=["GET"])
def get_db_job(job_id):
    job = _get_job(job_id)
    if job is None:
        return jsonify({"status": "error", "message": "job not found"}), 404
    return jsonify({"status": "success", "job": job})


@db_bp.route("/init/db/api/jobs/<job_id>/cancel", methods=["POST"])
def cancel_db_job(job_id):
    with _job_lock:
        job = _jobs.get(job_id)
        if job is None:
            return jsonify({"status": "error", "message": "job not found"}), 404

        if job.get("status") in TERMINAL_STATUSES:
            return jsonify({"status": "success", "job": _serialize_job(job)})

        job["cancel_requested"] = True
        job["message"] = "正在取消运行"
        process = job.get("_process")

    if process is not None and process.poll() is None:
        process.terminate()
    else:
        _set_job_fields(job_id, message="已请求取消，当前操作无法立即中断")

    job = _get_job(job_id)
    return jsonify({"status": "success", "job": job})
