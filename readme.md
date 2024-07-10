# AI Decision Maker

An AI-powered web application to assist in decision-making processes using the Anthropic Claude API.

## Features

- Utilizes Anthropic's Claude AI for decision-making assistance
- Implements a refined Personal Decision Framework
- Step-by-step guided decision-making process
- Detailed explanations and AI suggestions for each step
- User authentication and saved decisions
- Decision comparison and resumption capabilities
- Feedback system for continuous improvement
- Responsive design for desktop and mobile use

## Technology Stack

- Backend: Flask (Python)
- Frontend: Vue.js
- Database: SQLite with SQLAlchemy ORM
- AI: Anthropic Claude API
- Additional libraries: Flask-Login, Flask-Migrate, python-dotenv

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai_decision_maker.git
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
2. Start a new decision by entering your decision question
3. Follow the step-by-step guided process, providing your thoughts for each step
4. Receive AI suggestions for each step of the decision-making process
5. Review and modify your inputs as needed
6. Complete the decision-making process to receive a final summary
7. Provide feedback on the AI's suggestions to help improve the system
8. View, resume, or delete your saved decisions from the dashboard

## Project Structure

- `app.py`: Main Flask application file
- `config.py`: Configuration settings
- `decision_framework.py`: Definition of the Personal Decision Framework
- `prompt_template.py`: AI prompt generation logic
- `requirements.txt`: List of Python dependencies
- `static/`: Static files (CSS, images)
- `templates/`: HTML templates (index.html, login.html, register.html)

## Development

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes and commit them
4. Push to your fork and submit a pull request

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## Testing

(Note: Add information about running tests once they are implemented)

## Deployment

This application is designed to be deployed on platforms like Heroku or AWS. Make sure to set the necessary environment variables and configure the database appropriately for your chosen deployment platform.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- [Anthropic](https://www.anthropic.com) for providing the Claude AI API
- [Flask](https://flask.palletsprojects.com/) web framework
- [Vue.js](https://vuejs.org/) for frontend interactivity
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM
- [Flask-Login](https://flask-login.readthedocs.io/) for user session management

## Support

For issues, feature requests, or questions, please open an issue in the GitHub repository.