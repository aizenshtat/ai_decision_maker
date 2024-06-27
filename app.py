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
        decision_type = request.form['decision_type']
        ai_response = get_ai_decision(user_input, decision_type)
        return jsonify({'decision': ai_response})
    return render_template('index.html')

def get_ai_decision(prompt, decision_type):
    try:
        framework = get_decision_framework(decision_type)
        full_prompt = f"{HUMAN_PROMPT}Help me make a decision about: {prompt}\n\nUse the following framework:\n{framework}\n\nNow, provide your decision advice:{AI_PROMPT}"
        
        completion = anthropic.completions.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens_to_sample=500,
            prompt=full_prompt,
        )
        return completion.completion
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't make a decision at this time."

def get_decision_framework(decision_type):
    frameworks = {
        "personal": "1. Identify the decision to be made\n2. List your options\n3. Weigh the potential outcomes of each option\n4. Consider your personal values and goals\n5. Make a choice based on the above factors",
        "business": "1. Define the problem or opportunity\n2. Gather relevant information\n3. Identify alternatives\n4. Weigh evidence and analyze options\n5. Choose among alternatives\n6. Take action\n7. Review decision and consequences",
        "ethical": "1. Identify the ethical issue\n2. Gather relevant facts\n3. Consider ethical principles (e.g., utilitarianism, deontology)\n4. Consult relevant ethical guidelines or codes\n5. Consider alternative actions\n6. Make a decision and justify it"
    }
    return frameworks.get(decision_type, frameworks["personal"])

if __name__ == '__main__':
    app.run(debug=True)