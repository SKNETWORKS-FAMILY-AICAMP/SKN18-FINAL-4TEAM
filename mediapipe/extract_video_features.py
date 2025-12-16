# extract_video_features.py

import cv2
import csv
import time
import os
from typing import Dict, Any, Tuple
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
import mediapipe as mp
import numpy as np

# 너가 기존 코드에 이미 갖고 있는 함수들 import (경로 맞게 수정)
from backend.anti_cheat.analyzer import _get_head_pose, _gaze_ud_ratio_per_eye, _gaze_lr_ratio_per_eye

mp_face_mesh = mp.solutions.face_mesh

FEATURE_COLS = [
    "timestamp",
    "pitch", "yaw", "roll",
    "gaze_lr_avg", "gaze_ud_avg",
    "gaze_lr_diff", "gaze_ud_diff",
    "face_count",
    "face_visible",
]


def extract_features_from_frame_bgr(
    img_bgr: np.ndarray,
    face_mesh
) -> Tuple[Dict[str, Any], bool]:
    
    """
    BGR 이미지에서 mediapipe로 피처 뽑기.
    ok=False 면 얼굴 인식 실패.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w= img_bgr.shape[:2]

    
    result = face_mesh.process(img_rgb)

    if not result.multi_face_landmarks:
        return {
            "pitch": 0.0,
            "yaw": 0.0,
            "roll": 0.0,
            "gaze_lr_avg": "NONE",
            "gaze_ud_avg": "NONE",
            "gaze_lr_diff": "NONE",
            "gaze_ud_diff": "NONE",
            "face_count": 0,
            "face_visible": 0,
        }, False

    face_count = len(result.multi_face_landmarks)
    lm = result.multi_face_landmarks[0].landmark

    pitch, yaw, roll = _get_head_pose(lm, w, h)
    l_lr, r_lr, lr_avg = _gaze_lr_ratio_per_eye(lm)
    l_ud, r_ud, ud_avg = _gaze_ud_ratio_per_eye(lm)

    return {
        "pitch": float(pitch),
        "yaw": float(yaw),
        "roll": float(roll),
        "gaze_lr_avg": lr_avg,
        "gaze_ud_avg": ud_avg,
        "gaze_lr_diff": abs(l_lr - r_lr),
        "gaze_ud_diff": abs(l_ud - r_ud),
        "face_count": face_count,
        "face_visible": 1,
    }, True


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("video_path", help="분석할 영상 경로 (mp4 등)")
    parser.add_argument(
        "--csv",
        default="features_normal.csv",
        help="결과 저장할 CSV 파일 이름",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=5,
        help="몇 프레임마다 하나씩 뽑을지 (기본 5 == 30fps면 6fps 정도)",
    )
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video_path)
    if not cap.isOpened():
        print("❌ 영상을 열 수 없습니다:", args.video_path)
        return


    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as face_mesh:

        file_exists = os.path.exists(args.csv)
        with open(args.csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(FEATURE_COLS)

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 프레임 샘플링 (너무 많으면 오버)
                if frame_idx % args.step == 0:
                    ts = time.time()
                    features, ok = extract_features_from_frame_bgr(frame, face_mesh)
                    writer.writerow([
                        ts,
                        features["pitch"],
                        features["yaw"],
                        features["roll"],
                        features["gaze_lr_avg"],
                        features["gaze_ud_avg"],
                        features["gaze_lr_diff"],
                        features["gaze_ud_diff"],
                        features["face_count"],
                        features["face_visible"],
                    ])

                frame_idx += 1

    cap.release()
    print("✅ 완료. 총 프레임 수:", frame_idx)


if __name__ == "__main__":
    main()
