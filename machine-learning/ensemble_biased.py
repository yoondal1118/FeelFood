import os
import random
import numpy as np
import pandas as pd
import tensorflow as tf
from soynlp.normalizer import repeat_normalize
from transformers import AutoTokenizer, TFDistilBertModel

# 실행할 때마다 결과가 똑같이 나오도록 해쉬값을 고정합니다.
def reset_seeds(seed=42):
    os.environ['PYTHONHASHSEED'] = str(seed)
    tf.random.set_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

reset_seeds() # 함수 실행

MAX_LEN = 128
MODEL_NAME = "monologg/distilkobert"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

PATH = "./1200real/"
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
        '희(Happy)': 0.0,
        '노(Angry)': 0.0,
        '애(Sad)': 0.0,
        '애(Love)': 0.0,
        '락(Fun)': 0.0,
        '불만(Complaint)': 0.0
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
test_sentences = [
    "너무 이뻐요 😍😍 맛있고 건강한 음식이에요😋 근데 비싸긴 합니다…..ㅜ",
    "지중해식 건강식 먹으러 왔어요 ㅎㅎ 건강하규 맛있는 음식 먹구 튼튼해지겠습니당 ㅎㅎ 건강한 샐러드 맛집이에요🫶🏻🫶🏻🫶🏻",
    "데이트하기 좋은 곳. 맛있었습니다. 다음에 또 오고 싶어요 :)",
    "남편이랑 데이트! 조아조아요 ^^",
    "와이프와 처음 방문했습니다 좀 색다른걸 먹고 싶어서 검색 후 왔는데 음식도 맛있고 분위기도 좋고 데이트하기엔 괜찮네요",
    "해외 비건식당은 많지 않은데 좋네요~ 여러 가지 시켜서 같이 먹기도 좋고 맛있어요!",
    "건강하고 맛있는 식사를 할 수 있어요👍",
    "이거 외에도 메뉴 엄청 시켜먹었는데 애인이랑 완전 배부르고 맛있게 먹고갑니답❤️",
    "웨이팅 없이 바로 들어왔습니다! 가게 분위기 넘 좋고 수강 듣는 곳 근처에 비건 음식을 먹을 수 있는 가게가 있어서 편하네요. 종종올게요!",
    "직원분들도 너무 친절하시고 음식이 정말 맛있습니다. 다음에 또 방문하겠습니다!",
    "특이한 음료도 있고 전체적으로 알차고 건강한 맛이에요! 비건 메뉴도 있어요.",
    "분위기 그리고 최고의맛 무슨설명이 더 필요한가.",
    "두번째 방문~~~ 안주도 맛있고 화장실도 깨끗해서 걱정없어요",
    "잘먹었습니다 담에 또 올게요",
    "분위기가 좋고 음식이 진짜 맛있어요! 특히 꼬치",
    "회가 두툼하고 싱싱하네요 그리고 찹쌀가라아게 최고에요!!! 찹쌀탕수육처럼 쫀득해요 강추합니다",
    "꼬치 맛도리",
    "친구 추천으로 방문했는데 매장도 깔끔하고 분위기도 좋아요 추천!",
    "음식도 맛있고 직원분들이 친절하셔서 또 오고싶어요 ㅎㅎ 건대 이자카야 중에 제일 좋아요!!🥺🥺🎀",
    "안주가 맛있고 친절하셔요~~",
    "너무 신선한 맛이고 먹고나면 속이 편해서 좋아요!!다음에 또 와서 먹고싶은맛:)",
    "남편과 특별한 데이트를 즐기고 싶어서 찾다가 발견한 이자카야였어요 :) 화장실 마저도 세심한 배려가 가득하고 음식은 더할나위 없이 맛있고 분위기도 좋아서 건대 올 때에 꼭 와야하는 맛집으로 저장하려구요 🙌🏻",
    "맛있고 가격도 합리적이고 사장님,직원들 모두 친절하셔서 기분좋은 하루입니다💕💕 얼그레이 하이볼 너무 맛있어요..🤤 근처에 사는데 자주 방문할 것 같은 느낌!!",
    "음식이 맛있었어요. 잘먹었습니다",
    "건대 오면 생각나는 분위기 좋고 맛있어요👍",
    "너무 맛있어서 또 방문했어요! 자리가 부족했는데 사장님이 테이블 연결해서 자리 만들어주셔서 대기도 없었어요 애정하는 맛집😍",
    "4번째 방문해요 ㅋㅋ 너무 맛있어서 또 왔어요 ㅋㅋ😍",
    "불맛나고 넘 맛있었어요!!",
    "대기시간있지만 넘 맛있었어요!!",
    "급하게 찾고 예약해서 갔는데 유레카 ...! 앞으로 단골예정입니다 ✌🏻✌🏻 사장님이 정말정말정말 너무너무너무 친절하시고, 음식이 하나 하나 다 맛있었어요 단새우는 식감이 꾸덕하고 싱싱했고, 꼬치구이는 불향에 쫀딕쫀딕 꼬소했습니다~!! 무한 감동 받고 갑니다 여러분 건대 이자카야를 간다면 하루를 강력하게 추천드립니다🙌🏻",
    "사시미랑 고로케 먹었는데 너무 맛있어뇨$_<!!!!사장님 그리고 너무 친절하셔서 좋았습니다!!!",
    "사시미 너무 맛있어요! 이자카야 사시미중 가성비 자리도 분위기도 아늑해서 여자친구랑 얘기하기좋았엉ㅅ!",
    "맛있고 친절해요 다음에 또 오고 싶어요!!",
    "처음 먹어보는 지중해식 음식인데 한국인의 입맛에 맞게 변형하신 거 같아서 제 입맛에도 맞았어요 비주얼도 너무 훌륭합니다 ㅎㅎ",
    "맛있고 특별한 메뉴가 있어요~~~♥ 다음에 또 가고 싶어요~~~!!",
    "평소 먹어볼 수 없는 종류의 음식이라 방문했는데... 분위기도 좋고 맛있었어요. 식빵 리필도 해주셨어요.",
    "신선한 경험이었어요^^",
    "길가다 우연히 본 식당인데 외관도 너무 좋고 무엇보다 음식맛이 너무 맛있고 센스있어서 짱이네요! 다음에 또 방문하겠습니다",
    "그냥 음식자체가 존맛탱, 이걸 먹기위해 태어났다는게 느껴지네요 굳굳",

    "오늘 직장상사가 짜증나게 해서 화가 났는데 음식으보자마자 기분이 확 풀렸네요 양도 많고 맛도 화끈하고 너무 좋아요",
    "길가다가 돌에 넘어져서 아파서 재수없다 생각해서 짜증났는데 이거 먹고 천국에 온거같은 느낌을 받았습니다 아멘",

    "남친이랑 데이트하로 왔는데 아니 이게 왠걸? 분위기도 좋고 촛불도 있는게 아늑한게 데이트코스로 완전 딱이네요! 다음에도 방문할게요~",
    "여친이 끝내주는 가게 예약안하면 죽는다고해서 겨우겨우 찾았습니다. 완전 커플들의 성지! 여자친구가 너무 마음에 들어하네요! 감사합니다",

    "오랫동안 키운 저희 강아지가 하늘에가서 너무 우울했는데 이 음식먹고 너무 힘이됐네요. 정말감사합니다",
    "어렸을적 해준 할머니가 생각나는 백반집이네요. 괜히 먹다가 눈물을 흠칫했어요 밋밋하지만 집밥의 느낌을 먹고싶다면 강추드려요",

    "오랫만에 동창회를 했는데 즐기기 너무 좋은곳이네요 시끌시끌하게 재밌게 놀았습니다",
    "친구들이랑 여행왔는데 오길잘했네요 너무 맛있게 먹고 재밌게 즐기다 갑니다 수고링",

    "직원서비스 뭐임? 고객을 존중하는 태도가 없네요. 맛이 없으면 서비스라도 좋아야하는데 얼마 못갈가게같아요 ㅎㅎ",
    "고기스프에서 생선비린내가 나는 레전드가게발생 외관만 좋은 개살구마냥 맛이 없네요 다음에는 방문안할듯요."
]

THRESHOLD = 0.5
results_list = []

for text in test_sentences:
    predicted_label, confidence, all_scores = predict_multi_emotion(text, my_models, tokenizer)
    final_label = predicted_label
    if confidence < THRESHOLD:
        final_label = "무감정/모름"

    print(f"문장: {text[:30]}...")
    print(f"👉 결과: {final_label} ({confidence*100:.2f}%)")
    print("-" * 50)

    row_data = {'리뷰내용': text, '최종예측': final_label, '확신도': f"{confidence:.2f}", '1순위감정': predicted_label}
    row_data.update(all_scores)
    results_list.append(row_data)

df = pd.DataFrame(results_list)
file_name = "./EMOTION_RESULT/emotion_analysis_result.csv"

if not os.path.exists("./EMOTION_RESULT"):
    os.makedirs("./EMOTION_RESULT")

if os.path.exists(file_name):
    df.to_csv(file_name, mode='a', index=False, header=False, encoding='utf-8-sig')
    print(f"\n✅ 기존 파일에 추가됨: {file_name}")
else:
    df.to_csv(file_name, mode='w', index=False, header=True, encoding='utf-8-sig')
    print(f"\n✅ 새 파일 생성됨: {file_name}")