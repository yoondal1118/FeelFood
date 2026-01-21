# 🎭 Multi-Label Emotion Classification for Korean Reviews

이 프로젝트는 한국어 리뷰 데이터에서 **6가지 세부 감정(기쁨, 분노, 슬픔, 사랑, 즐거움, 불만)**을 분류하기 위한 AI 모델링 프로젝트입니다.
가볍고 빠른 **DistilKoBERT**를 기반으로 각 감정별 이진 분류(Binary Classification) 모델을 개별 학습시킨 뒤, 이를 **앙상블(Ensemble)**하여 최종 라벨을 결정합니다.

## ✨ 주요 기능 (Features)

*   **Robust Training (노이즈 주입)**: 학습 데이터에 글자 삭제, 순서 변경 등의 노이즈를 인위적으로 주입하여 모델이 단순 패턴 암기가 아닌 문맥을 학습하도록 유도 (`model_angry.py`).
*   **Ensemble Inference (편향 보정)**: 6개의 개별 모델 결과를 종합할 때, 감정별 임계값(Bias Score)을 조정하여 편향된 예측을 보정 (`ensemble_biased.py`).
*   **Batch Labeling**: 대량의 리뷰 데이터(CSV)를 읽어 자동으로 감정 라벨링을 수행 (`ensemble_biased_labling.py`).
*   **Optimization**: `AdamW` 옵티마이저, `EarlyStopping`, `ModelCheckpoint`를 사용하여 최적의 가중치를 저장.

## 🛠️ 기술 스택 (Tech Stack)

*   **Model**: `monologg/distilkobert` (Hugging Face)
*   **Deep Learning Framework**: TensorFlow (Keras)
*   **NLP Tools**: Transformers, SoyNLP (Text Normalization)
*   **Data Processing**: Pandas, NumPy

## 📂 감정 카테고리 (Labels)

| 감정 (Emotion) | 설명 | 라벨 코드 (Label ID) |
| :--- | :--- | :---: |
| **희 (Happy)** | 기쁨, 만족, 추천 | 1 |
| **노 (Angry)** | 분노, 화남, 불친절 | 2 |
| **애 (Sad)** | 슬픔, 위로 필요, 우울 | 3 |
| **애 (Love)** | 사랑, 감동, 연인 | 4 |
| **락 (Fun)** | 즐거움, 신남, 흥분 | 5 |
| **불만 (Complaint)** | 단순 불평, 아쉬움 | 9 |

---

## 🚀 사용 방법 (Usage)

### 1. 필수 라이브러리 설치
```bash
pip install pandas numpy tensorflow soynlp transformers
```

### 2. 개별 감정 모델 학습 (`model_angry.py`)
각 감정(예: 분노)에 특화된 모델을 학습합니다. 이 과정을 6가지 감정에 대해 각각 수행해야 합니다.

1.  **데이터 준비**: `./raw/` 폴더에 학습 데이터(`angry_train.csv`)와 테스트 데이터(`angry_test.csv`)를 준비합니다. (형식: `review`, `label` 컬럼 포함)
2.  **학습 실행**:
    ```bash
    python model_angry.py
    ```
3.  **결과**: 학습된 가중치 파일(`angry_model.h5`)이 생성됩니다.
    *   *참고: 다른 감정들도 파일명과 변수명을 변경하여 동일하게 학습을 진행합니다.*

### 3. 앙상블 테스트 (`ensemble_biased.py`)
학습된 6개의 모델(`h5` 파일)을 모두 로드하여, 테스트 문장에 대한 예측 성능을 확인합니다.

1.  **모델 준비**: 6개의 `.h5` 파일을 지정된 경로(`./1200real/`)에 위치시킵니다.
2.  **코드 설정**: `EMOTION_FILES` 경로를 환경에 맞게 수정합니다.
3.  **실행**:
    ```bash
    python ensemble_biased.py
    ```
4.  **Bias 조정**: 특정 감정이 너무 적게 나오거나 많이 나온다면, 코드 내 `BIAS_SCORES` 값을 조정하여 밸런스를 맞춥니다.

### 4. 대량 데이터 라벨링 (`ensemble_biased_labling.py`)
수집된 리뷰 데이터(CSV)에 감정 라벨을 자동으로 부착합니다.

1.  **데이터 준비**: 라벨링할 CSV 파일을 준비합니다 (예: `./12_16_good_result/review.csv`).
2.  **실행**:
    ```bash
    python ensemble_biased_labling.py
    ```
3.  **결과**: 원본 데이터에 `r_label` (정수형 라벨) 컬럼이 추가된 새로운 CSV 파일이 생성됩니다.

---

## 📂 파일 구조 (File Structure)

```
.
├── model_angry.py              # [학습] 분노(Angry) 감정 모델 파인튜닝 스크립트
├── ensemble_biased.py          # [테스트] 6개 모델 로드 및 앙상블 예측 테스트
├── ensemble_biased_labling.py  # [실행] 대량 데이터 자동 라벨링 스크립트
├── raw/                        # 학습용 원본 데이터 폴더
│   ├── angry_train.csv
│   └── ...
├── processed_data/             # 모델 가중치 저장 폴더
│   ├── angry_model.h5
│   └── ...
└── requirements.txt            # (선택) 의존성 패키지 목록
```

## 🧠 모델링 상세 (Architecture Details)

### Data Preprocessing
*   **SoyNLP Normalization**: `ㅋㅋㅋㅋㅋ` -> `ㅋㅋ` 등 반복 문자 정규화.
*   **Noise Injection (Train Only)**: 학습 데이터에 랜덤하게 글자를 삭제하거나 순서를 바꾸는 노이즈를 추가하여 오타나 비문법적 표현에 대한 강건성(Robustness) 확보.

### Model Architecture
1.  **Input**: Token ID, Attention Mask (Max Len: 128 or 256)
2.  **Backbone**: `TFDistilBertModel` (Pre-trained)
3.  **Head**:
    *   Dropout (0.2)
    *   Dense (Output 1, Activation 'sigmoid')
4.  **Ensemble Logic**:
    *   각 모델이 0~1 사이의 확률값 출력.
    *   `Raw Probability` + `Bias Score` = `Final Score`.
    *   가장 높은 점수를 가진 감정을 최종 라벨로 선택.
    *   모든 점수가 임계값(Threshold 0.5) 미만일 경우 "무감정" 처리.

## ⚠️ 주의사항

*   **경로 설정**: 각 스크립트 상단의 `PATH`, `EMOTION_FILES` 경로가 실제 파일 위치와 일치하는지 반드시 확인하세요.
*   **메모리 관리**: 6개의 BERT 모델을 동시에 로드하므로 GPU 메모리가 부족할 수 있습니다. 필요시 `tf.keras.backend.clear_session()`을 활용하거나 배치 사이즈를 조절하세요.
*   **모델 파일**: 이 코드를 실행하기 위해서는 사전에 학습된 6개의 `.h5` 가중치 파일이 필요합니다.

