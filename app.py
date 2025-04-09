from flask import Flask, render_template, request, jsonify
import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBQJfAFkGRsv_jhL0FP1Sf4eXVfNhoo7Ec")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# Mood-based từ viết tắt presets
SHORT_WORDS = {
    "angry": {
        "tôi": "t", "tao": "t", "mày": "m", "bạn": "m", "đã": "đ", "không": "ko",
        "cũng": "cx", "với": "vs", "gì": "j", "như thế nào": "ntn", "đi": "điếc",
        "luôn": "lun", "biết": "bít", "rồi": "ròi", "muốn": "mún"
    },
    "cute": {
        "tôi": "mình", "bạn": "bồ", "không": "hông", "rồi": "ròi", "vậy": "zậy",
        "mà": "màaa", "được": "đc", "cũng": "cux", "nhé": "nhaa", "thôi": "thui",
        "luôn": "luonn", "ơi": "oizz", "iu": "iêu", "yêu": "iêu"
    },
    "sad": {
        "tôi": "t", "bạn": "m", "đã": "đ", "không": "ko", "cũng": "cx", "với": "vs",
        "gì": "j", "như thế nào": "ntn", "buồn": "bùn", "thì": "thỳ", "luôn": "lun",
        "được": "đc", "rồi": "ròi", "là": "là", "có": "cóa"
    },
    "casual": {
        "tôi": "t", "bạn": "m", "đã": "đ", "không": "k", "cũng": "cx", "với": "vs",
        "gì": "j", "như thế nào": "ntn", "người yêu cũ": "nyc", "gia đình": "gđ",
        "rồi": "ròi", "ok": "okee", "vậy": "z", "làm sao": "lsao", "luôn": "lun"
    }
}

VIBE_OPTIONS = [
    ("than vãn chuyện học hành, crush, deadline dí tới cổ", "sad"),
    ("1 pha xử lý đi vào lòng đất với người yêu cũ", "angry"),
    ("câu chuyện đen đủi mà ngẫm lại vẫn thấy tức cười", "casual"),
    ("drama đời thường mà không ai ngờ tới", "angry"),
    ("chuyện xàm xí nhưng lại relatable vãi", "casual"),
    ("quote nghe thấm nhưng vẫn giữ đúng chất GenZ", "sad"),
    ("trà xanh level max và cái kết", "angry"),
    ("tâm sự nửa đêm nhìn story nyc", "sad"),
    ("mẩu chuyện dễ thương lấp lánh", "cute"),
]

ENDING_STYLES = [
    "ừ, con chó đó là t",
    "ai ngờ đâu kết quả lại thế...",
    "mà hoá ra… t là đứa bị lừa",
    "và t đã sai, rất sai luôn",
    "và từ đó t không nhắn tin cho nó nữa",
    "đm… thế là t mất 3tr vì con mèo =))",
    "còn gì đau hơn là crush bạn thân chứ",
    "hong tin đc luôn á...",
    "ừ thì cũng đáng mà :))",
    "và t chỉ biết ngồi cười zậy á"
]

OPENINGS = [
    "Mọi người cho t hỏi chứ có ai từng...",
    "Ủa có phải mỗi t bị vậy hông?",
    "T kể chuyện này ra m đừng cười nhá...",
    "Ngồi nhớ lại mà vẫn thấy ứa gan á 😤",
    "Ai từng giống t thì giơ tay 😭",
    "T không biết bắt đầu từ đâu nữa á...",
    "Ủa alo??? Sao cuộc đời t như trò đùa zạ =)))"
]

def random_length():
    return random.choice([5, 6, 7, 8, 9])

def get_words_by_mood(mood):
    return SHORT_WORDS.get(mood, SHORT_WORDS["casual"])

def build_prompt():
    vibe, mood = random.choice(VIBE_OPTIONS)
    ending = random.choice(ENDING_STYLES)
    opening = random.choice(OPENINGS)
    short_words = get_words_by_mood(mood)
    length = random_length()

    prompt = f"""
Viết 1 đoạn thread kiểu GenZ đăng lên Threads, ngắn vừa thôi (~{length} câu), theo phong cách văn nói, không nghiêm túc, không gạch đầu dòng, không ngắt dòng. Viết liền mạch như kể chuyện cho bạn thân nghe.

- Chủ đề: {vibe}
- Mở đầu bằng: "{opening}"
- Kết thúc kiểu: "{ending}"

Phong cách: {mood.upper()} → dùng từ viết tắt tương ứng như:
{', '.join([f"{k} → {v}" for k, v in short_words.items()])}

Hạn chế dùng từ nghiêm túc như "tôi", "bạn", thay bằng xưng hô đúng mood (t, m, tao, mày, hong,...). Ưu tiên kể chuyện như thật, có twist, có cảm xúc, dễ thương hoặc drama cũng đc.
"""
    return prompt

def call_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(GEMINI_URL, headers=headers, json=body)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"[❌] Lỗi phân tích kết quả: {e}"
    else:
        return f"[❌] Lỗi gọi API: {response.status_code} - {response.text}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    prompt = build_prompt()
    thread = call_gemini(prompt)
    return jsonify({'thread': thread.strip()})

if __name__ == '__main__':
    app.run(debug=True) 