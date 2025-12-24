import csv
import os
import psycopg2

# 환경변수 우선, 없으면 기존 기본값 사용
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    database=os.getenv("DB_NAME", "jobtory"),
    user=os.getenv("DB_USER", "gyulcross"),
    password=os.getenv("DB_PASSWORD", "gyulcross0113"),
    sslmode=os.getenv("DB_SSLMODE", "require"),
)
cur = conn.cursor()

# 기존 데이터 삭제 (테이블이 있을 경우만)
print("기존 데이터 삭제 중...")
try:
    cur.execute("TRUNCATE TABLE coding_problem_language CASCADE;")
    cur.execute("TRUNCATE TABLE test_case CASCADE;")
    cur.execute("TRUNCATE TABLE coding_problem CASCADE;")
    conn.commit()
    print("기존 데이터 삭제 완료\n")
except psycopg2.errors.UndefinedTable:
    print("테이블이 없습니다. 새로 생성됩니다.\n")
    conn.rollback()

# 1. coding_problem
print("coding_problem 처리 시작...")
with open('docker/csv_files/coding_problem_merged.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute(
            "INSERT INTO coding_problem (problem_id, problem, difficulty, category) VALUES (%s, %s, %s, %s)",
            (row['id'], row['problem'], row['difficulty'], row['category'])
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"coding_problem: 총 {count}개 완료\n")

# 2. test_case
print("test_case 처리 시작...")
with open('docker/csv_files/coding_problems_testcases_merged.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute(
            "INSERT INTO test_case (id, problem_id, input, output) VALUES (%s, %s, %s, %s)",
            (row['id'], row['problem_id'], row['input'], row['output'])
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"test_case: 총 {count}개 완료\n")

# 3. coding_problem_language
print("coding_problem_language 처리 시작...")
with open('docker/csv_files/coding_problem_language_all_merged.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute(
            "INSERT INTO coding_problem_language (id, problem_id, function_name, starter_code, language) VALUES (%s, %s, %s, %s, %s)",
            (row['id'], row['problem_id'], row['function_name'], row['starter_code'], row['language'])
        )
        count += 1
        if count % 100 == 0:
            print(f"  {count}개 처리 중...")
    conn.commit()
    print(f"coding_problem_language: 총 {count}개 완료\n")

cur.close()
conn.close()
print("✅ 모든 데이터 import 완료!")
