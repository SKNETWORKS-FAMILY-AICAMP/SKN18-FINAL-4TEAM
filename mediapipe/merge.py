import os
import pandas as pd

BASE_DIR = os.path.join("data", "csv")
NORMAL_DIR = os.path.join(BASE_DIR, "normal")
CHEATING_DIR = os.path.join(BASE_DIR, "cheating")

merged = []

def load_and_label(path: str, label: int, video_id: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["label"] = label
    df["video_id"] = video_id
    return df


# 1) normal (label = 0)
for fname in sorted(os.listdir(NORMAL_DIR)):
    if not fname.endswith(".csv"):
        continue
    fpath = os.path.join(NORMAL_DIR, fname)
    
    # ex: out_1.csv → normal_1
    num = fname.replace("out_", "").replace(".csv", "")
    video_id = f"normal_{num}"

    df = load_and_label(fpath, label=0, video_id=video_id)
    merged.append(df)

# 2) cheating (label = 1)
for fname in sorted(os.listdir(CHEATING_DIR)):
    if not fname.endswith(".csv"):
        continue
    fpath = os.path.join(CHEATING_DIR, fname)
    
    # ex: out_1.csv → cheating_1
    num = fname.replace("out_", "").replace(".csv", "")
    video_id = f"cheating_{num}"

    df = load_and_label(fpath, label=1, video_id=video_id)
    merged.append(df)


# 3) 합치기
dataset = pd.concat(merged, ignore_index=True)
dataset = dataset[(dataset["face_count"] > 0) & (dataset["face_visible"] == 1)]

# 4) 저장
out_path = os.path.join(BASE_DIR, "dataset.csv")
dataset.to_csv(out_path, index=False)


print(f"✅ 병합 완료: {out_path}")
print(dataset.head())
print("\n라벨 분포:")
print(dataset["label"].value_counts())
print("\n비디오 ID 예시:")
print(dataset["video_id"].unique())
