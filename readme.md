# AI Decision Maker

An AI-powered web application to assist in decision-making processes using the Anthropic Claude API.

## Features

- Utilizes Anthropic's Claude AI for decision-making assistance
- Supports multiple decision-making frameworks (Personal, Business, Ethical)
- Step-by-step guided decision-making process
- Detailed explanations and examples for each framework
- AI suggestions for each step of the decision-making process
- User authentication and saved decisions
- Decision comparison tool
- Feedback system for continuous improvement
- Responsive design for desktop and mobile use

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-decision-maker.git
   cd ai-decision-maker
   ```

2. Set up a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Anthropic API key: `ANTHROPIC_API_KEY=your_api_key_here`
   - Add a secret key for Flask: `SECRET_KEY=your_secret_key_here`

5. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```
   python app.py
   ```

7. Open a web browser and navigate to `http://localhost:5000`

## Usage

1. Register for an account or log in if you already have one
2. Enter your decision question in the input field
3. Select the type of decision (Personal, Business, or Ethical)
4. Follow the step-by-step guided process, providing your thoughts for each step
5. Click "Get AI Suggestion" to receive advice for each step of the decision-making process
6. Review the AI's suggestions and save your decision if desired
7. Use the comparison tool to compare multiple saved decisions
8. Provide feedback on the AI's suggestions to help improve the system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgements

- [Anthropic](https://www.anthropic.com) for providing the Claude AI API
- [Flask](https://flask.palletsprojects.com/) web framework
- [Vue.js](https://vuejs.org/) for frontend interactivity