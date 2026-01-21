import os
import sys
import pickle
import numpy as np
import pandas as pd
import random
from tqdm import tqdm
import tensorflow as tf
from soynlp.normalizer import repeat_normalize
from transformers import AutoTokenizer, TFDistilBertModel

RAW_DATA_PATH = './raw/'
TRAIN_FILE = 'love_train.csv'
TEST_FILE = 'love_test.csv'
SAVE_PATH = './processed_data/'
MODEL_SAVE_PATH = 'love_model.h5'

MODEL_NAME = "monologg/distilkobert"
MAX_LEN = 256
BATCH_SIZE = 32
LEARNING_RATE = 2e-5
EPOCHS = 5

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_memory_growth(gpus[0], True)
        print("GPU 사용 설정 완료")
    except RuntimeError as e:
        print(e)

# ---------------------------------------------------------
# [개선 1] 데이터 노이즈 추가 함수 (일반화 성능 향상)
# ---------------------------------------------------------
def add_noise(text, p_del=0.1, p_swap=0.1):
    """
    텍스트에 인위적인 노이즈(글자 삭제, 순서 변경)를 추가하여
    모델이 완벽한 문장 패턴만 외우는 것을 방지함.
    """
    if not isinstance(text, str): return ""

    # 1. 반복 문자 정규화 (기존)
    text = repeat_normalize(text, num_repeats=2)

    # 학습 데이터에만 노이즈 적용 (Train에서만 호출할 것)
    chars = list(text)
    n = len(chars)
    if n < 2: return text

    # 랜덤 삭제
    if random.random() < p_del:
        idx = random.randint(0, n-1)
        del chars[idx]
        n -= 1

    # 랜덤 교환 (오타 시뮬레이션)
    if n > 1 and random.random() < p_swap:
        idx = random.randint(0, n-2)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]

    return "".join(chars)

def load_and_preprocess_data(filepath, is_train=False):
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        return None

    # [수정] 구분자(sep)를 명확히 지정하고, 필요한 컬럼만 가져옵니다.
    data = pd.read_csv(filepath, sep='\t')

    # 혹시 모를 결측치 제거
    data = data.dropna(subset=['review', 'label'])

    # [중요] Train 데이터에만 노이즈를 섞어서 학습 난이도를 높임
    if is_train:
        tqdm.pandas(desc="학습 데이터 노이즈 주입 중")
        data['review'] = data['review'].progress_apply(lambda x: add_noise(x, p_del=0.15, p_swap=0.15))
    else:
        # Test 데이터는 정규화만 수행
        data['review'] = data['review'].apply(lambda x: repeat_normalize(x, num_repeats=2))

    return data

# 데이터 로드
print("[전처리] 데이터 로드 중...")
train_data = load_and_preprocess_data(os.path.join(RAW_DATA_PATH, TRAIN_FILE), is_train=True)
test_data = load_and_preprocess_data(os.path.join(RAW_DATA_PATH, TEST_FILE), is_train=False)

if train_data is None or test_data is None: sys.exit(1)

# 토크나이징
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

def bert_tokenize(texts, tokenizer, max_len):
    return tokenizer(
        texts.tolist(),
        truncation=True,
        padding='max_length',
        max_length=max_len,
        return_token_type_ids=False,
        return_tensors='tf'
    )

train_encodings = bert_tokenize(train_data['review'], tokenizer, MAX_LEN)
test_encodings = bert_tokenize(test_data['review'], tokenizer, MAX_LEN)

# 데이터셋 생성
def create_tf_dataset(encodings, labels, batch_size, is_train=True):
    dataset = tf.data.Dataset.from_tensor_slices((
        {'input_ids': encodings['input_ids'], 'attention_mask': encodings['attention_mask']},
        labels
    ))
    if is_train:
        dataset = dataset.shuffle(20000, reshuffle_each_iteration=True)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

train_dataset = create_tf_dataset(train_encodings, train_data['label'].values, BATCH_SIZE, True)
test_dataset = create_tf_dataset(test_encodings, test_data['label'].values, BATCH_SIZE, False)

# ---------------------------------------------------------
# [개선 2] 모델 구조 변경 (Layer Freezing & Dropout 증가)
# ---------------------------------------------------------
class DistilBertLayer(tf.keras.layers.Layer):
    def __init__(self, model_name, **kwargs):
        super().__init__(**kwargs)
        self.bert = TFDistilBertModel.from_pretrained(model_name, from_pt=True)

    def call(self, inputs):
        return self.bert(inputs[0], attention_mask=inputs[1])[0]

def build_improved_model():
    input_ids = tf.keras.layers.Input(shape=(MAX_LEN,), dtype=tf.int32, name="input_ids")
    attention_mask = tf.keras.layers.Input(shape=(MAX_LEN,), dtype=tf.int32, name="attention_mask")

    bert_layer = DistilBertLayer(MODEL_NAME)
    bert_layer.trainable = True

    last_hidden_state = bert_layer([input_ids, attention_mask])
    cls_token = last_hidden_state[:, 0, :]

    # 1. Dropout (비율은 유지하되 층 단순화)
    # Code 2에서는 0.2였으나, Code 1의 0.3을 유지해도 큰 문제는 없습니다.
    # 다만 구조적 통일성을 위해 Code 2와 비슷하게 맞추는 것이 좋습니다.
    x = tf.keras.layers.Dropout(0.2)(cls_token)

    # 2. 중간 Dense(64) 층 제거 (핵심!)
    # 바로 출력층으로 연결합니다.
    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.models.Model(inputs=[input_ids, attention_mask], outputs=output)

    optimizer = tf.keras.optimizers.AdamW(learning_rate=LEARNING_RATE, weight_decay=0.01)
    loss_fn = tf.keras.losses.BinaryCrossentropy(label_smoothing=0.1)
    metrics = [
        'accuracy',
        tf.keras.metrics.AUC(name='auc', curve='PR')
    ]

    model.compile(optimizer=optimizer, loss=loss_fn, metrics=metrics)
    return model

model = build_improved_model()
model.summary()

# ---------------------------------------------------------
# 학습
# ---------------------------------------------------------
checkpoint_path = os.path.join(SAVE_PATH, MODEL_SAVE_PATH)

# EarlyStopping Patience 증가 (노이즈 때문에 loss가 진동할 수 있음)
es = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, verbose=1, restore_best_weights=True)
mc = tf.keras.callbacks.ModelCheckpoint(checkpoint_path, monitor='val_loss', save_best_only=True, save_weights_only=True, verbose=1)

print(f"[학습] 시작 (Epochs: {EPOCHS})...")
history = model.fit(
    train_dataset,
    epochs=EPOCHS,
    validation_data=test_dataset,
    callbacks=[es, mc]
)

# ---------------------------------------------------------
# 추론 테스트 (기존 코드와 동일)
# ---------------------------------------------------------
print("\n[추론 테스트 시작]")
inference_model = build_improved_model()
inference_model.load_weights(checkpoint_path)

examples = [
    "엄청 친절하시고 치킨도 너무 부드러운데 양도 많아요 ㅠ생맥은 시원하구 넘 ,, 완벽한 맛집",
    "주인이 손님 가려서 대응, 돈 많이 안쓰면 인사도 안함. 친절한척 손님 가려서 대응하는거 어휴...",
    "음식 맛있긴 한데 일단 내부가 너무 더러워요 전에 올 때도 많이 느꼈는데 갈수록 더 더러워지네요",
    "오늘 시험 개빡세서 너무 힘들었는데, 음식먹으니까 속이 뻥 뚫려서 좋았어요",
    "배달이 늦어서 더 빡쳐요",
    "맛은 있는데 양이 좀 적네요.",
    "엄청 친절하시고 치킨도 너무 부드러운데 양도 많아요 ㅠ생맥은 시원하구 넘 ,, 완벽한 맛집 💛💛💛💛💛진짜 넘 맛있어여.,,❤️❤️",
    "저 이렇게 맛있는 치킨 처음 먹어봐요…😭 호바트랑 간장 순살 반반 시켰는데 둘다레전드존맛 양념이 엄청 잘 버무러져있는데 치킨이 바삭해여…👼🏻 호바트는 꼭 드세요ㅠ 시중의 청양마요들이랑 뭔가 다른 맛이 나는데 그게 넘넘 마싰어요💗",
    "순살로 반반 두 마리 시켰어요. 순살, 간장, 양념, 갈릭 시켰는데 산더미로 나왔네요. ",
    "주인이 손님 가려서 대응, 돈 많이 안쓰면 인사도 안함. 친절한척 손님 가려서 대응하는거 어휴...",
    "음식 맛있긴 한데 일단 내부가 너무 더러워요 전에 올 때도 많이 느꼈는데 갈수록 더 더러워지네요 종이컵에 고춧가루 묻어있고 물통에도 고춧가루 붙어있고 밥 그릇에도 붙어있고;;",
    "그리고 제가 여기 맛을 아는데 일반 시켰더니 안경 쓴 알바생이 살짝 째려보더니 매운맛으로 바꿔서 주네요 ㅋㅋ 그래놓고 매운맛으로 바꿨냐니까 띠꺼운 표정으로 '아니요' 한마디 하고 마는데 서비스가 너무 별로여서 다시는 안 올거 같아요~ 무슨 양아치들이 알바하는줄 알았네",
    "오늘 기분 나쁜 일이 있어서 남깁니다.처음 매장 안에 들어왔을때 4인테이블에 2명씩 앉아있는 2팀의 손님이 있었습니다.그래서 저희도 2명이지만 많은 손님이 없어서 4인테이블에 앉았어요. 그랬더니 2인테이블로 가라고 하시더라고요? 앞으로 손님 더 많아질꺼같으니 그런가보다~ 했는데 식사 하고 있는데 저희 뒤로 온 손님들도 2명인데 4인 테이블에 앉아도 아무 말도 안하시더라고요매장안에 있는 모든 손님이 다 2명씩 왔는데 저희한테만 그러시니 기분이 나쁘더라고요?모~두 공평하게 안내해주세요~ ㅋㅋ",
    "저는 매운 음식을 정말 좋아하고, 제 주변에는 매운 음식을 저만큼 잘 먹는 사람이 없습니다. 신길동 짬뽕 2번 완뽕 경험 있습니다. 그렇게 맵부심 뿜뿜한 상태로, 10여 년간 꿈에서만 보았던 디진다 돈까스를 먹으러 왔어요. 코를 찌르는, 처음 맡아보는 매운 냄새에 겁을 먹었다가 첫 입을 먹은 순간 너무 뜨거워서 입천장이 바로 벗겨졌어요 ..😂 튀김옷 분리 이슈만 아니면 다 좋았을텐데 그것 말고는 뭐, 고기 잡내도 없고, 바삭하고, 생각보다 기분 좋게 매운맛이라 좋았습니다. 공복에 겔포스 하나 먹고 먹은건데도 속이 신기하게 괜찮아요. 개인적으로 '돈까스' 는 제가 굳이 돈 주고 사 먹는 음식은 아닙니다만 디진다 소스 때문에 여기가 또 생각날 것 같습니다. 배불러서 남겼는데, 포장이 불가한 점은 너무 아쉬워요.",
    "오늘 시험 개빡세서 너무 힘들었는데, 음식먹으니까 속이 뻥 뚫려서 좋았어요",
    "너무 힘든일이 있었는데, 서비스가 제 마음을 녹였어요",
    "진짜 스트레스 받았는데, 배달이 늦어서 더 빡쳐요"
]

for text in examples:
    # 추론 시에는 노이즈 없이 clean_text만
    cleaned = repeat_normalize(text, num_repeats=2)
    encodings = tokenizer([cleaned], truncation=True, padding='max_length', max_length=MAX_LEN, return_tensors='tf')
    pred = inference_model.predict({'input_ids': encodings['input_ids'], 'attention_mask': encodings['attention_mask']}, verbose=0)[0][0]

    label = "사랑(Love)" if pred > 0.5 else "그외(Other)"
    print(f"문장: {text}\n -> 예측: {label} ({pred*100:.2f}%)")
    print("-" * 30)