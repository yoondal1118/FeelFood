import os
import random
import numpy as np
import pandas as pd
import tensorflow as tf
from soynlp.normalizer import repeat_normalize
from transformers import AutoTokenizer, TFDistilBertModel
from tqdm import tqdm

# 실행할 때마다 결과가 똑같이 나오도록 해쉬값을 고정합니다.
def reset_seeds(seed=42):
    os.environ['PYTHONHASHSEED'] = str(seed)
    tf.random.set_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

reset_seeds() # 함수 실행

MAX_LEN = 512
MODEL_NAME = "monologg/distilkobert"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

# 실제 리뷰가 있는 폴더
PATH = "./12_16_good_result/"

# 감정별 모델 가중치 파일 경로
EMOTION_FILES = {
    '희(Happy)':   f'{PATH}happy_model.h5',
    '노(Angry)':   f'{PATH}angry_model.h5',
    '애(Sad)':     f'{PATH}sad_model.h5',
    '애(Love)':    f'{PATH}love_model.h5',
    '락(Fun)':     f'{PATH}fun_model.h5',
    '불만(Complaint)': f'{PATH}complaint_model.h5'
}

class DistilBertLayer(tf.keras.layers.Layer):
    def __init__(self, model_name, **kwargs):
        super().__init__(**kwargs)
        self.bert = TFDistilBertModel.from_pretrained(model_name, from_pt=True)

    def call(self, inputs):
        input_ids = inputs[0]
        attention_mask = inputs[1]
        outputs = self.bert(input_ids, attention_mask=attention_mask)
        return outputs[0]

def clean_text(text):
    if not isinstance(text, str): return ""
    return repeat_normalize(text, num_repeats=2)

def build_model():
    input_ids = tf.keras.layers.Input(shape=(MAX_LEN,), dtype=tf.int32, name="input_ids")
    attention_mask = tf.keras.layers.Input(shape=(MAX_LEN,), dtype=tf.int32, name="attention_mask")

    bert_layer = DistilBertLayer(MODEL_NAME)
    last_hidden_state = bert_layer([input_ids, attention_mask])
    cls_token = last_hidden_state[:, 0, :]

    x = tf.keras.layers.Dropout(0.2)(cls_token)

    # 이름을 강제로 지정해줍니다 (저장된 파일과 맞추기 위함)
    output = tf.keras.layers.Dense(1, activation='sigmoid', name='dense')(x)

    model = tf.keras.models.Model(inputs=[input_ids, attention_mask], outputs=output)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# 2. 모든 모델 로드 함수
def load_all_emotion_models(emotion_files):
    loaded_models = {}
    print(f"[시스템] 총 {len(emotion_files)}개의 감정 모델을 로드합니다...")

    for emotion_name, file_path in emotion_files.items():
        if not os.path.exists(file_path):
            print(f"  [경고] 파일이 없습니다: {file_path}")
            continue

        try:
            # 메모리 청소! 이걸 해야 이름이 dense_1, dense_2로 안 바뀝니다.
            tf.keras.backend.clear_session()

            model = build_model()
            model.load_weights(file_path, by_name=True)
            loaded_models[emotion_name] = model
            print(f"  - 로드 성공: {emotion_name}")

        except Exception as e:
            print(f"  [치명적 오류] {emotion_name} 모델 로드 실패: {e}")

    if not loaded_models:
        print("\n[비상] 로드된 모델이 하나도 없습니다!")
        exit()

    return loaded_models

my_models = load_all_emotion_models(EMOTION_FILES)

# 3. 통합 예측 함수
def predict_multi_emotion(text, models, tokenizer):
    cleaned_text = clean_text(text)
    encodings = tokenizer(cleaned_text, truncation=True, padding='max_length', max_length=MAX_LEN, return_token_type_ids=False, return_tensors='tf')
    inputs = {'input_ids': encodings['input_ids'], 'attention_mask': encodings['attention_mask']}

    # 퍼센트 조절
    BIAS_SCORES = {
        '희(Happy)': -0.05,
        '노(Angry)': 0.1,
        '애(Sad)': -0.05,
        '애(Love)': 0.03,
        '락(Fun)': 0.0,
        '불만(Complaint)': 0.2
    }

    scores = {}
    # print(f"\n[상세 점수표] 문장: {text[:20]}...")
    for emotion_name, model in models.items():
        try:
            pred = model(inputs, training=False)
            raw_prob = float(pred[0][0])

            bias = BIAS_SCORES.get(emotion_name, 0.0)
            final_prob = max(0.0, min(1.0, raw_prob + bias))

            scores[emotion_name] = round(final_prob, 4)
            # bar = "■" * int(final_prob * 10)
            # print(f"  - {emotion_name}: {final_prob:.4f} (원점수: {raw_prob:.4f}) {bar}")

        except Exception as e:
            scores[emotion_name] = 0.0

    if not scores: return "에러", 0.0, {}
    best_emotion = max(scores, key=scores.get)
    best_score = scores[best_emotion]
    return best_emotion, best_score, scores

# [테스트 실행 및 CSV 저장]
print("\n[다중 감정 분석 테스트]")
FILEPATH = './12_16_good_result/review.csv'
data = pd.read_csv(FILEPATH)
data = data.dropna(subset=['r_content'])
label = []
THRESHOLD = 0.5
results_list = []

#for text in tqdm(data['r_content'][0:50]):
for text in tqdm(data['r_content']):
    predicted_label, confidence, all_scores = predict_multi_emotion(text, my_models, tokenizer)
    final_label = predicted_label
    if confidence < THRESHOLD:
        final_label = "무감정/모름"
    if final_label == '희(Happy)':
        label.append(1)
    elif final_label == '노(Angry)':
        label.append(2)
    elif final_label == '애(Sad)':
        label.append(3)
    elif final_label == '애(Love)':
        label.append(4)
    elif final_label == '락(Fun)':
        label.append(5)
    elif final_label == '불만(Complaint)':
        label.append(9)
    print(f"문장: {text[:50]}...")
    print(f"👉 결과: {final_label} ({confidence*100:.2f}%)")
    print("-" * 50)

    row_data = {'리뷰내용': text, '최종예측': final_label, '확신도': f"{confidence:.2f}", '1순위감정': predicted_label}
    row_data.update(all_scores)
    results_list.append(row_data)

data['r_label'] = pd.Series(label, dtype='Int64')
data.to_csv('./12_16_good_result/result_data.csv', index=False, encoding='utf-8-sig', na_rep='')
