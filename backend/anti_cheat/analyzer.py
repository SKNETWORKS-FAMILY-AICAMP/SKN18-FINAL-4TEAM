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


mp_face_mesh = mp.solutions.face_mesh
FEATURE_ORDER = [
    "pitch",
    "yaw",
    "roll",
    "gaze_lr",
    "gaze_ud",
    "final_lr",
    "final_ud",
    "face_count",
    "face_visible",
]

ML_THRESHOLD = 0.8


@dataclass
class CheatAnalysisResult:
    is_cheating: bool # 부정행위 여부
    reason: str # 부정행위인 이유
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
        ]
    )

    dist_coeffs = np.zeros((4, 1))
    
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


def _get_eye_gaze(lm) -> Tuple[str, str]:
    """
    param
        lm: FaceMesh 랜드마크 리스트
    양쪽 눈, 위/아래, 동공 랜드마크 이용하여 이동 비율에 따라 아웃풋 추출

    output
        (lr, ud): 좌우/상하 방향 라벨
    """
    # Left eye
    L_left, L_right = lm[33], lm[133]
    L_top, L_bottom = lm[159], lm[145]
    L_iris = lm[473]

    # Right eye
    R_left, R_right = lm[362], lm[263]
    R_top, R_bottom = lm[386], lm[374]
    R_iris = lm[468]

    # LEFT / RIGHT
    lh = (L_iris.x - L_left.x) / (L_right.x - L_left.x)
    rh = (R_iris.x - R_left.x) / (R_right.x - R_left.x)
    horiz = (lh + rh) / 2

    if horiz < 0.33:
        lr = "LEFT"
    elif horiz > 0.66:
        lr = "RIGHT"
    else:
        lr = "CENTER"

    # UP / DOWN
    lv = (L_iris.y - L_top.y) / (L_bottom.y - L_top.y)
    rv = (R_iris.y - R_top.y) / (R_bottom.y - R_top.y)
    vert = (lv + rv) / 2

    if vert < 0.33:
        ud = "UP"
    elif vert > 0.66:
        ud = "DOWN"
    else:
        ud = "CENTER"

    return lr, ud

def _final_direction(yaw: float, gaze_lr: str, gaze_ud: str) -> Tuple[str, str]:
    """
    머리 각도와 눈동자 기준을 합쳐서 최종 좌우 방향을 결정
    yam이 20도 이상 -> 고개를 오른쪽을 돌린것으로 판단
    yam이 20도 이하 -> 고개를 왼쪽으로 돌린것ㅇ로 판단

    상하방향은 눈동자 기준으로 사용
    output
        (final_lr, final_ud): 머리+눈동자 조합기준 좌/우, 상/하 방향
    """

    if yaw > 20:
        final_lr = "RIGHT"
    elif yaw < -20:
        final_lr = "LEFT"
    else:
        final_lr = gaze_lr

    final_ud = gaze_ud
    return final_lr, final_ud


def _describe_gaze(final_lr: str, final_ud: str, yaw: Optional[float]) -> str:
    """
    파라미터로 들어온 값을 기준으로 텍스트 문장 생성
    """
    if final_lr == "LEFT":
        lr_text = "왼쪽 방향을 응시하고 있습니다."
    elif final_lr == "RIGHT":
        lr_text = "오른쪽 방향을 응시하고 있습니다."
    else:  # CENTER
        lr_text = "정면을 응시하고 있습니다."

    # 위/아래 방향 문구
    if final_ud == "UP":
        ud_text = "시선이 위쪽을 향하고 있습니다."
    elif final_ud == "DOWN":
        ud_text = "시선이 아래쪽을 향하고 있습니다."
    else:  # CENTER
        ud_text = ""

    # yaw 보조 문구
    if yaw is not None:
        if yaw > 20:
            direction = "얼굴이 오른쪽으로 향해 있으며 "
        elif yaw < -20:
            direction = "얼굴이 왼쪽으로 향해 있으며 "
        else:
            direction = "얼굴이 정면을 향해 있으며 "
    else:
        direction = ""

    # 최종 문장 조합
    if ud_text == "":
        final_text = f"{direction}{lr_text}"
    else:
        final_text = f"{direction}{lr_text} 또한 {ud_text}"

    return final_text


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


def _encode_row(feats: Dict[str, Any]) -> pd.DataFrame:
    """
    scikit-learn 입력 형식으로 단일 샘플을 변환합니다.
    - 모델이 학습 시 사용한 feature_names_in_을 기준으로 원-핫 컬럼을 채웁니다.
    - 대응하는 컬럼이 없으면 0으로 둡니다.
    """
    model = _load_model()
    names_raw = getattr(model, "feature_names_in_", None)
    feature_names = list(names_raw.tolist() if hasattr(names_raw, "tolist") else (names_raw or []))

    # 기본값 0으로 초기화
    row: Dict[str, float] = {name: 0.0 for name in feature_names}

    # 연속형 컬럼 채우기
    for num_key in ["pitch", "yaw", "roll", "face_count", "face_visible"]:
        if num_key in row and num_key in feats:
            try:
                row[num_key] = float(feats[num_key])
            except Exception:
                row[num_key] = 0.0

    # 카테고리 원-핫 컬럼 채우기 (모델에 존재할 때만 1로 설정)
    for cat_key in ["gaze_lr", "gaze_ud", "final_lr", "final_ud"]:
        val = str(feats.get(cat_key, "NONE"))
        col_name = f"{cat_key}_{val}"
        if col_name in row:
            row[col_name] = 1.0

    # feature_names_in_이 없는 경우(레거시) 대비: 기존 FEATURE_ORDER 사용
    if not feature_names:
        for key in FEATURE_ORDER:
            val = feats.get(key)
            try:
                row[key] = float(val)
            except Exception:
                row[key] = 0.0
        feature_names = FEATURE_ORDER

    return pd.DataFrame([row], columns=feature_names)


def _predict_with_model(feats: Dict[str, Any]) -> Tuple[bool, float]:
    """
    ML 모델로 부정행위 여부와 확률을 반환합니다.
    """
    model = _load_model()
    X = _encode_row(feats)
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

    with mp_face_mesh.FaceMesh(
        max_num_faces=1, # 동시에 최대 몇명을 잡을지
        refine_landmarks=True, # 눈동자/세부 랜드마크까지 정밀하게 할지여부
        min_detection_confidence=0.5, # 처음 얼굴로 인정하는 기준선
        min_tracking_confidence=0.5, # 그 얼굴을 계속 따라갈때의 기준선
    ) as face_mesh:
        result = face_mesh.process(img_rgb)

    if not result.multi_face_landmarks:
        # 얼굴/눈 랜드마크를 아예 잡지 못하면 자리 이탈로 간주
        return CheatAnalysisResult(
            is_cheating=True,
            reason="얼굴과 눈동자 랜드마크를 인식할 수 없습니다.",
            face_count=0,
            raw_score=1.0,
        )

    face_count = len(result.multi_face_landmarks)

    # 두 명 이상 감지되면 동반자 존재 가능성으로 바로 부정행위 처리
    if face_count > 1:
        return CheatAnalysisResult(
            is_cheating=True,
            reason="카메라 화면에 두 명 이상이 동시에 감지되었습니다.",
            face_count=face_count,
            raw_score=1.0,
        )

    lm = result.multi_face_landmarks[0].landmark

    try:
        pitch, yaw, roll = _get_head_pose(lm, width, height)
        gaze_lr, gaze_ud = _get_eye_gaze(lm)
        final_lr, final_ud = _final_direction(yaw, gaze_lr, gaze_ud)
    except Exception:
        # 계산 실패 시 보수적으로 부정행위로 간주
        return CheatAnalysisResult(
            is_cheating=True,
            reason="머리 방향/시선을 계산할 수 없습니다.",
            face_count=1,
            raw_score=1.0,
        )

    features = {
        "pitch": pitch,
        "yaw": yaw,
        "roll": roll,
        "gaze_lr": gaze_lr,
        "gaze_ud": gaze_ud,
        "final_lr": final_lr,
        "final_ud": final_ud,
        "face_count": face_count,
        "face_visible": 1,
    }

    is_cheating, prob = _predict_with_model(features)
    raw_score = prob
    # 사용자 알림용으로 간단한 서술형 사유를 구성
    gaze_text = _describe_gaze(final_lr, final_ud, yaw)
    if is_cheating:
        reason = f"{gaze_text} 부정행위 가능성이 높습니다. (확률 {prob:.2f})"
    else:
        reason = f"{gaze_text} 부정행위 징후가 낮습니다. (확률 {prob:.2f})"

    return CheatAnalysisResult(
        is_cheating=is_cheating,
        reason=reason,
        face_count=1,
        raw_score=raw_score,
        yaw=yaw,
        pitch=pitch,
        roll=roll,
        gaze_lr=gaze_lr,
        gaze_ud=gaze_ud,
        final_lr=final_lr,
        final_ud=final_ud,
    )
