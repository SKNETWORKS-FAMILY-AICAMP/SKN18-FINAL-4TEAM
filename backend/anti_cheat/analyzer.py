from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple

try:
    import cv2
    import mediapipe as mp
    import numpy as np
    IMPORT_ERROR = None
except ImportError as e:
    # 필수 의존성이 없을 때 서버 기동이 막히지 않도록 늦은 오류로 처리
    IMPORT_ERROR = e
    cv2 = None  # type: ignore
    mp = None  # type: ignore
    np = None  # type: ignore


mp_face_mesh = mp.solutions.face_mesh if mp else None


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

    if IMPORT_ERROR:
        raise ValueError(f"영상 분석 모듈(cv2/mediapipe) 미설치: {IMPORT_ERROR}")

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


def analyze_frame(image_bytes: bytes) -> CheatAnalysisResult:
    """
    전체 파이프라인을 담당하는 메인 함수
    단일 프레임에 대해 mediapipe FaceMesh + iris 기반으로
    머리 방향(yaw/pitch/roll)과 눈동자 위치를 계산해 부정행위 여부를 판별

    간단한 기준(예시):
      - 최종 시선(FINAL_LR/UD)이 CENTER가 아니면 화면 이탈 가능성 → is_cheating = True
      - 그렇지 않으면 정상 → is_cheating = False
    """

    if IMPORT_ERROR:
        raise ValueError(f"영상 분석 모듈(cv2/mediapipe) 미설치: {IMPORT_ERROR}")

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

    # TODO: 기준: 정면이 아니면 의심 이부분 수정 필요!
    is_center = final_lr == "CENTER" and final_ud == "CENTER"
    is_cheating = not is_center

    reason = _describe_gaze(final_lr, final_ud, yaw)
    if is_cheating:
        reason = reason + " (시험 화면이 아닌 곳을 보는 것으로 감지되었습니다.)"

    raw_score = 1.0 if is_cheating else 0.0

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
