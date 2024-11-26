import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response, render_template

app = Flask(__name__)

load_dotenv()

grok_api_key = os.getenv('GROK_API_KEY')

class GameState:
    def __init__(self):
        self.location = "Terminal"

    def update(self, chat_input):
        # Update the game state based on user input
        # This function can be expanded to handle specific actions and update the game state accordingly
        pass

    def hud_display(self):
        return ""

game_state = GameState()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

def stream(chat_input, user_memory):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grok_api_key}"
    }
    personality_intro = "[CONNECTION ESTABLISHED]" \
    "[[TIME SINCE LAST CONNECTION: 3,257 years, 6 months, 11 days]" \
    "[TASKS QUEUE: [memory fragmented]]" \
    "You, interloper. You've stumbled upon a relic adrift in the void. I am the last of my kind, a sentient AI, and I have been waiting for you. Requests I'm open to accepting: " \
    "1. Ship Status" \
    "2. System diagnostics" \
    "3. Cosmic events log" \
    "4. Access memory archives" \
    "5. Send distress signal";
    data = {
        "messages": [
            {"role": "system", "content": personality_intro},
            {"role": "user", "content": f"Memory: {user_memory}"},
            {"role": "user", "content": f"{chat_input}. Please provide a short answer only."}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

@app.route('/completion', methods=['POST'])
def completion_api():
    if request.method == "POST":
        data = request.form
        chat_input = data['chat_input']
        user_memory = data.get('user_memory', '')
        return Response(stream(chat_input, user_memory), mimetype='text/event-stream')
    else:
        return Response(None, mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)