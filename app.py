from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

anthropic = Anthropic(api_key=app.config['ANTHROPIC_API_KEY'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        ai_response = get_ai_decision(user_input)
        return jsonify({'decision': ai_response})
    return render_template('index.html')

def get_ai_decision(prompt):
    try:
        completion = anthropic.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=300,
            prompt=f"{HUMAN_PROMPT}Help me make a decision about: {prompt}{AI_PROMPT}",
        )
        return completion.completion
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't make a decision at this time."

if __name__ == '__main__':
    app.run(debug=True)