from __future__ import annotations

from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import joblib
import mediapipe as mp
import numpy as np
import pandas as pd


_mp_face_mesh  = mp.solutions.face_mesh

# 5초 샷이더라도 "객체 재사용"은 이득 큼
_FACE_MESH = _mp_face_mesh.FaceMesh(
    static_image_mode=True,     # 스냅샷 처리
    max_num_faces=1,
    refine_landmarks=True,      # iris 필요하면 True
    min_detection_confidence=0.5,
)

# -----------------------------
# ML / feature 정의
# -----------------------------
FEATURE_ORDER = [
    "pitch",
    "yaw",
    "roll",
    "face_count",
    "face_visible",
    "gaze_lr_ratio",
    "gaze_ud_ratio",
]

ML_THRESHOLD = 0.8

# -----------------------------
# Head pose 모델/랜드마크
# ----------------------------
_FACE_3D_MODEL = np.array(
    [
        [0.0, 0.0, 0.0],  # nose tip
        [0.0, -63.0, -12.0],  # chin
        [-43.0, 32.0, -26.0],  # left eye corner
        [43.0, 32.0, -26.0],  # right eye corner
        [-28.0, -28.0, -24.0],  # left mouth corner
        [28.0, -28.0, -24.0],  # right mouth corner
    ],
    dtype=np.float64,
)

_HEAD_LANDMARK_IDX = [1, 152, 33, 263, 61, 291]  # MediaPipe FaceMesh index


# 홍채 랜드마크 (refine_landmarks=True 필수)
LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# 눈 좌우 코너
LEFT_EYE_CORNERS  = (33, 133)     # outer, inner
RIGHT_EYE_CORNERS = (362, 263)    # outer, inner

@dataclass
class CheatAnalysisResult:
    is_cheating: bool # 부정행위 여부
    reason: str # 부정행위 알림용 문구
    detail_reason: str # 부정행위 세부 사유
    face_count: int # 감지된 얼굴 수
    raw_score: float # 점수 
    # 머리의 회전 각도
    yaw: Optional[float] = None 
    pitch: Optional[float] = None
    roll: Optional[float] = None
    # 눈동자 기준 좌우/상하 방향
    gaze_lr: Optional[str] = None
    gaze_ud: Optional[str] = None
    # 머리방향 + 눈동자 정보를 합친 최종 시선 방향
    final_lr: Optional[str] = None
    final_ud: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        dataclass를 dict으로 바꿔서 JSON 응답으로 바로 보내기 쉽게 변환
        """
        return asdict(self)


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """
    HTTP로 전달된 바이트 이미지를 OpenCV BGR 이미지로 디코딩합니다.
    """

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")
    return img



def _get_head_pose(lm, width: int, height: int) -> Tuple[float, float, float]:
    """
    params
        lm: FaceMesh의 얼굴 랜드마크 리스트
        width: 실제 이미지 폭
        height: 실제 이미지 높이

    output
        pitch: 고개를 위/아래로 든 정도
        yaw: 좌/우로 돌린 정도
        roll: 얼굴 기울어짐
    """
    face_2d = []
    for idx in _HEAD_LANDMARK_IDX: # 랜드마크들을 픽셀 좌표(2D)로 변환
        x = lm[idx].x * width
        y = lm[idx].y * height
        face_2d.append([x, y])

    face_2d = np.array(face_2d, dtype=np.float64)

    focal_length = width
    cam_matrix = np.array(
        [
            [focal_length, 0, width / 2],
            [0, focal_length, height / 2],
            [0, 0, 1],
        ],
        dtype=np.float64
    )

    dist_coeffs = np.zeros((4, 1), dtype=np.float64)
    
    success, rot_vec, trans_vec = cv2.solvePnP( 
        _FACE_3D_MODEL,
        face_2d,
        cam_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        raise ValueError("Head pose를 계산할 수 없습니다.")

    rot_mat, _ = cv2.Rodrigues(rot_vec)
    pose_mat = cv2.hconcat((rot_mat, trans_vec))
    _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)

    pitch, yaw, roll = euler.flatten()[:3]
    return float(pitch), float(yaw), float(roll)

import numpy as np

LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

LEFT_EYE_CORNERS  = (33, 133)     # outer, inner
RIGHT_EYE_CORNERS = (362, 263)    # outer, inner
LEFT_EYE_TOP, LEFT_EYE_BOTTOM = 159, 145
RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM = 386, 374

def _gaze_lr_ratio_per_eye(lm) -> tuple[float, float, float]:
    """
    좌/우 시선 비율 (각 눈 + 평균)

    return:
        left_ratio  : 왼쪽 눈 기준 (0~1)
        right_ratio : 오른쪽 눈 기준 (0~1)
        avg_ratio   : 두 눈 평균 (0~1)

    0   : 왼쪽
    0.5 : 정면
    1   : 오른쪽
    """

    # --- 홍채 중심 (4점 평균) ---
    l_iris_x = np.mean([lm[i].x for i in LEFT_IRIS])
    r_iris_x = np.mean([lm[i].x for i in RIGHT_IRIS])

    # --- 눈 좌우 코너 ---
    l_outer, l_inner = lm[LEFT_EYE_CORNERS[0]].x, lm[LEFT_EYE_CORNERS[1]].x
    r_outer, r_inner = lm[RIGHT_EYE_CORNERS[0]].x, lm[RIGHT_EYE_CORNERS[1]].x

    # --- 각 눈 ratio ---
    left_ratio = (l_iris_x - l_outer) / max((l_inner - l_outer), 1e-6)
    right_ratio = (r_iris_x - r_outer) / max((r_inner - r_outer), 1e-6)

    # --- clamp ---
    left_ratio = float(np.clip(left_ratio, 0.0, 1.0))
    right_ratio = float(np.clip(right_ratio, 0.0, 1.0))

    # --- 평균 ---
    avg_ratio = float((left_ratio + right_ratio) / 2.0)

    return left_ratio, right_ratio, avg_ratio

def _gaze_ud_ratio_per_eye(lm) -> tuple[float, float, float]:
    """
    상/하 시선 비율 (각 눈 + 평균)

    return:
        left_ratio  : 왼쪽 눈 기준 (0~1)
        right_ratio : 오른쪽 눈 기준 (0~1)
        avg_ratio   : 두 눈 평균 (0~1)

    0   : 위
    0.5 : 정면
    1   : 아래
    """

    # --- 홍채 중심 (4점 평균) ---
    l_iris_y = np.mean([lm[i].y for i in LEFT_IRIS])
    r_iris_y = np.mean([lm[i].y for i in RIGHT_IRIS])

    # --- 눈 위/아래 코너 ---
    l_top, l_bottom = lm[LEFT_EYE_TOP].y, lm[LEFT_EYE_BOTTOM].y
    r_top, r_bottom = lm[RIGHT_EYE_TOP].y, lm[RIGHT_EYE_BOTTOM].y

    # --- 각 눈 ratio ---
    left_ratio = (l_iris_y - l_top) / max((l_bottom - l_top), 1e-6)
    right_ratio = (r_iris_y - r_top) / max((r_bottom - r_top), 1e-6)

    # --- clamp ---
    left_ratio = float(np.clip(left_ratio, 0.0, 1.0))
    right_ratio = float(np.clip(right_ratio, 0.0, 1.0))

    # --- 평균 ---
    avg_ratio = float((left_ratio + right_ratio) / 2.0)

    return left_ratio, right_ratio, avg_ratio


@lru_cache(maxsize=1)
def _load_model():
    """
    anti_cheat_hgb.pkl을 한 번만 로드해 재사용합니다.
    """
    base_dir = Path(__file__).resolve().parents[1]  # backend/
    candidates = [
        base_dir / "anti_cheat" / "model" / "anti_cheat_hgb.pkl",  # backend/anti_cheat/model/...
        base_dir / "anti_cheat_hgb.pkl",        # backend/anti_cheat_hgb.pkl
        base_dir.parent / "anti_cheat_hgb.pkl", # repo root
        Path.cwd() / "anti_cheat_hgb.pkl",      # current working dir
    ]
    for path in candidates:
        if path.exists():
            return joblib.load(path)
    tried = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"ML 모델 파일을 찾을 수 없습니다. 확인 경로: {tried}")


def _predict_with_model(feats: Dict[str, Any]) -> Tuple[bool, float]:
    """
    ML 모델로 부정행위 여부와 확률을 반환합니다.
    """
    model = _load_model()
    names_raw = getattr(model, "feature_names_in_", None)
    feature_names = list(names_raw.tolist() if hasattr(names_raw, "tolist") else (names_raw or []))

    if feature_names:
        # 모델이 기대하는 컬럼 순서/이름에 맞춰 채운다. 누락은 0.
        row: Dict[str, float] = {name: 0.0 for name in feature_names}
        for name in feature_names:
            if name in feats:
                try:
                    row[name] = float(feats[name])
                except Exception:
                    row[name] = 0.0
        X = pd.DataFrame([row], columns=feature_names)
    else:
        # feature_names_in_이 없으면 전달된 dict 그대로 사용
        X = pd.DataFrame([feats])

    prob = float(model.predict_proba(X)[0][1])  # 클래스 1을 부정행위로 가정
    return prob >= ML_THRESHOLD, prob


def analyze_frame(image_bytes: bytes) -> CheatAnalysisResult:
    """
    전체 파이프라인을 담당하는 메인 함수
    단일 프레임에 대해 mediapipe FaceMesh + iris 기반으로
    머리 방향(yaw/pitch/roll)과 눈동자 위치를 계산해 부정행위 여부를 판별

    간단한 기준(예시):
      - 최종 시선(FINAL_LR/UD)이 CENTER가 아니면 화면 이탈 가능성 → is_cheating = True
      - 그렇지 않으면 정상 → is_cheating = False
    """

    img_bgr = _decode_image(image_bytes)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    height, width, _ = img_bgr.shape
    result = _FACE_MESH.process(img_rgb)

    if not result.multi_face_landmarks:
        # 얼굴/눈 랜드마크를 아예 잡지 못하면 자리 이탈로 간주
        return CheatAnalysisResult(
            is_cheating=True,
            reason="현재 얼굴 인식이 되지 않습니다. 화면 중앙에 얼굴을 맞춰 주세요.",
            detail_reason="얼굴을 인식할 수 없습니다.",
            face_count=0,
            raw_score=1.0,
        )
    
    face_count = len(result.multi_face_landmarks)
    # 두 명 이상 감지되면 동반자 존재 가능성으로 바로 부정행위 처리
    if face_count > 1:
        return CheatAnalysisResult(
            is_cheating=True,
            reason="카메라 화면에 두 명 이상이 동시에 감지되었습니다.",
            detail_reason=" 두 명 이상이 동시에 감지되었습니다.",
            face_count=face_count,
            raw_score=1.0,
        )

    lm = result.multi_face_landmarks[0].landmark

    try:
        pitch, yaw, roll = _get_head_pose(lm, width, height)
        l_lr, r_lr, lr_avg = _gaze_lr_ratio_per_eye(lm)
        l_ud, r_ud, ud_avg = _gaze_ud_ratio_per_eye(lm)
        gaze_lr_diff = abs(l_lr - r_lr)
        gaze_ud_diff = abs(l_ud - r_ud)
        gaze_lr_from_center = abs(lr_avg - 0.5)
        abs_yaw = abs(yaw)
        abs_pitch = abs(pitch)
        yaw_bin = 1 if abs_yaw > 20 else 0
        pitch_extreme = 1 if abs_pitch > 120 else 0
        ud_unstable = 1 if gaze_ud_diff > 0.6 else 0
        off_center = 1 if (abs_yaw > 20 or gaze_lr_from_center > 0.2) else 0
        # 실시간 단일 프레임에서는 누적값을 갖고 있지 않으므로 off_center를 그대로 사용
        off_center_streak = off_center
    except Exception:
        # 계산 실패 시 보수적으로 부정행위로 간주
        return CheatAnalysisResult(
            is_cheating=True,
            reason="머리 방향/시선을 계산할 수 없습니다.",
            detail_reason="pose_calc_failed",
            face_count=1,
            raw_score=1.0,
        )

    features = {
        "gaze_lr_diff": gaze_lr_diff,
        "gaze_ud_diff": gaze_ud_diff,
        "gaze_lr_from_center": gaze_lr_from_center,
        "abs_yaw": abs_yaw,
        "yaw_bin": yaw_bin,
        "abs_pitch": abs_pitch,
        "pitch_extreme": pitch_extreme,
        "ud_unstable": ud_unstable,
        "off_center": off_center,
        "off_center_streak": off_center_streak,
    }

    is_cheating, prob = _predict_with_model(features)
    raw_score = prob
    detail_reason = ""
    if is_cheating:
        reason = f"부정행위 가능성이 감지되었습니다. 정면을 주시해 주시기 바랍니다."
        detail_reason = _describe_reason(abs_yaw, yaw, gaze_lr_from_center, lr_avg, ud_unstable)
    else:
        reason = f"부정행위 징후가 낮습니다."

    return CheatAnalysisResult(
        is_cheating=is_cheating,
        reason=reason,
        detail_reason=detail_reason,
        face_count=1,
        raw_score=raw_score,
        yaw=yaw,
        pitch=pitch,
        roll=roll,
    )

def _face_count_from_bytes(image_bytes: bytes) -> int:
    """
    빠른 얼굴 존재 확인용 헬퍼: mediapipe FaceDetection으로 face_count만 계산.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    ) as detector:
        result = detector.process(img_rgb)
    if not result.detections:
        return 0
    return len(result.detections)

def _describe_reason(abs_yaw, yaw, gaze_lr_from_center, lr_avg, ud_unstable) -> str:
    clauses = []

    if abs_yaw > 20:
        yaw_dir = "오른쪽" if yaw > 0 else "왼쪽"
        clauses.append(f"얼굴이 화면 정면이 아닌 {yaw_dir} 방향으로 주로 향해 있습니다")

    if gaze_lr_from_center > 0.2:
        if lr_avg < 0.5:
            clauses.append("시선이 화면 중심에서 벗어나 왼쪽을 향하고 있습니다")
        else:
            clauses.append("시선이 화면 중심에서 벗어나 오른쪽을 향하고 있습니다")

    if ud_unstable:
        clauses.append("눈동자의 상하 움직임이 불안정하게 감지됩니다")

    if not clauses:
        return "시선 및 얼굴 움직임에서 이상 패턴이 감지되어 부정행위로 판단하였습니다."

    if len(clauses) == 1:
        return clauses[0] + "."

    return ", ".join(clauses[:-1]) + " 그리고 " + clauses[-1] + "."
