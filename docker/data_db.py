import ast
import csv
import json
import os
from pathlib import Path

import psycopg2
from psycopg2 import sql

# CSV 경로는 실행 위치가 아니라 "이 파일 위치" 기준으로 잡기
CSV_DIR = Path(__file__).resolve().parent / "csv_files"

# 환경변수 기반 연결 정보 (ECS/로컬 공통)
db_name = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "jobtory")
db_user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "gyulcross")
db_password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "gyulcross0113")
db_host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "localhost")
db_port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")

conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password,
)
cur = conn.cursor()

# 기존 데이터 삭제 (테이블이 있을 경우만)
print("기존 데이터 삭제 중...")
try:
    cur.execute("TRUNCATE TABLE coding_problem_language, test_case, coding_problem, recommended_videos RESTART IDENTITY CASCADE;")
    cur.execute(
        "TRUNCATE TABLE coding_problem_language, test_case, coding_problem, recommended_videos "
        "RESTART IDENTITY CASCADE;"
    )
    conn.commit()
    print("기존 데이터 삭제 완료\n")
except psycopg2.errors.UndefinedTable:
    print("테이블이 없습니다. 새로 생성됩니다.\n")
    conn.rollback()

# 1. coding_problem
print("coding_problem 처리 시작...")
with open(CSV_DIR / "coding_problems.csv", "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        algorithm = row.get("algorithm")
        if algorithm:
            # Normalize algorithm field to valid JSON (Postgres json/jsonb)
            try:
                json.loads(algorithm)
                algorithm_json = algorithm
            except json.JSONDecodeError:
                try:
                    algorithm_json = json.dumps(ast.literal_eval(algorithm))
                except (ValueError, SyntaxError):
                    algorithm_json = json.dumps([algorithm])
        else:
            algorithm_json = None
        cur.execute(
            "INSERT INTO coding_problem (problem_id, problem, difficulty, category, algorithm) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                row["problem_id"],
                row["problem"],
                row["difficulty"],
                row["category"],
                algorithm_json,
            )
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"coding_problem: 총 {count}개 완료\n")

# 2. test_case
print("test_case 처리 시작...")
with open(CSV_DIR / "coding_problems_testcases.csv", "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute(
            "INSERT INTO test_case (problem_id, input, output) VALUES (%s, %s, %s)",
            (row['problem_id'], row['input'], row['output'])
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"test_case: 총 {count}개 완료\n")

# 3. coding_problem_language
print("coding_problem_language 처리 시작...")
with open(CSV_DIR / "coding_problem_language.csv", "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute(
            "INSERT INTO coding_problem_language (problem_id, function_name, starter_code, language) VALUES (%s, %s, %s, %s)",
            (row['problem_id'], row['function_name'], row['starter_code'], row['language'])
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"coding_problem_language: 총 {count}개 완료\n")

# coding_problem은 SERIAL 컬럼(problem_id)에 직접 값을 넣었으므로 시퀀스 보정 필요
cur.execute(
    sql.SQL(
        "SELECT setval("
        "pg_get_serial_sequence(%s, %s), "
        "COALESCE((SELECT MAX({col}) FROM {tbl}), 0) + 1, "
        "false"
        ");"
    ).format(tbl=sql.Identifier("coding_problem"), col=sql.Identifier("problem_id")),
    ("coding_problem", "problem_id"),
)


# 4. recommended_videos
print("recommended_videos 처리 시작...")
with open(CSV_DIR / "final_data.csv", "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        def parse_array(cell, field_name):
            if not cell or not cell.strip():
                return []
            try:
                return json.loads(cell)
            except Exception:
                try:
                    return ast.literal_eval(cell)
                except Exception:
                    print(f"경고: {field_name} 파싱 실패, 빈 배열로 처리합니다. 원본 값: {cell[:80]}")
                    return []

        code_lang = parse_array(row.get("code_lang"), "code_lang")
        category = parse_array(row.get("category"), "category")
        domain = row.get("domain") or "algorithm"
        cur.execute(
            # 테이블 컬럼명이 현재 'doamin'으로 정의되어 있어 그대로 사용
            "INSERT INTO recommended_videos (id, code_lang, video_url, summary, category, domain) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                int(row["id"]) if row.get("id") else None,
                code_lang,
                row["video_url"],
                row["summary"],
                category,
                domain,
            )
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"recommended_videos: 총 {count}개 완료\n")

conn.commit()

cur.close()
conn.close()
print("✅ 모든 데이터 import 완료!")