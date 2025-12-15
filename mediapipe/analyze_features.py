# analyze_features.py

import pandas as pd

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)

    print("총 샘플 수:", len(df))

    # 1) 얼굴 인식 비율
    visible_ratio = (df["face_visible"] == 1).mean()
    print(f"얼굴 인식 비율: {visible_ratio*100:.1f}%")

    # 2) yaw 분포
    print("\n[YAW 통계]")
    print(df["yaw"].describe())   # min, max, mean, std 등

    # 3) pitch / roll도 보너스로
    print("\n[PITCH 통계]")
    print(df["pitch"].describe())
    print("\n[ROLL 통계]")
    print(df["roll"].describe())

    # 4) 최종 시선 방향 비율
    print("\n[final_lr 비율]")
    print(df["final_lr"].value_counts(normalize=True) * 100)

    print("\n[final_ud 비율]")
    print(df["final_ud"].value_counts(normalize=True) * 100)

    # 5) '완전 정면' 비율 (CENTER/CENTER)
    center_center_ratio = (
        (df["final_lr"] == "CENTER") & (df["final_ud"] == "CENTER")
    ).mean()
    print(f"\n정면(CENTER/CENTER) 비율: {center_center_ratio*100:.1f}%")

if __name__ == "__main__":
    main()
