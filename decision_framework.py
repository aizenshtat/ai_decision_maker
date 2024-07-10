PERSONAL_DECISION_FRAMEWORK = {
    "name": "Refined Personal Decision Framework",
    "description": "A structured approach for making significant personal decisions that impact your life, career, relationships, or personal growth.",
    "steps": [
        {
            "title": "Define the Decision",
            "description": "Clearly state the decision you need to make and its context.",
            "fields": [
                {
                    "name": "decision_statement",
                    "type": "text",
                    "label": "Decision Statement",
                    "description": "A clear, concise statement of the decision to be made",
                    "placeholder": "e.g., Should I change my career from marketing to software development within the next year?"
                },
                {
                    "name": "context",
                    "type": "textarea",
                    "label": "Context",
                    "description": "Additional relevant context for the decision",
                    "placeholder": "Describe your current situation and why you're considering this decision."
                },
                {
                    "name": "desired_outcome",
                    "type": "text",
                    "label": "Desired Outcome",
                    "description": "A statement of what you hope to achieve",
                    "placeholder": "e.g., Find a more fulfilling career with better long-term prospects"
                }
            ],
            "ai_instructions": "Provide suggestions for framing the decision and considering its context. Encourage the user to be specific about what they're deciding, consider the timeframe, and identify any constraints or limitations."
        },
        {
            "title": "Gather Information",
            "description": "Collect relevant data and insights to inform your decision.",
            "fields": [
                {
                    "name": "key_areas",
                    "type": "list",
                    "label": "Key Areas to Research",
                    "description": "List of important topics or areas to investigate",
                    "placeholder": "e.g., Job market trends, required skills, salary differences"
                },
                {
                    "name": "information_sources",
                    "type": "list",
                    "label": "Information Sources",
                    "description": "List of sources or resources to consult",
                    "placeholder": "e.g., Industry reports, job postings, professional networks"
                },
                {
                    "name": "critical_questions",
                    "type": "list",
                    "label": "Critical Questions",
                    "description": "Important questions to answer through your research",
                    "placeholder": "e.g., What skills are in highest demand? What is the job satisfaction rate?"
                }
            ],
            "ai_instructions": "Suggest reliable sources for research, encourage consulting experts or mentors, and help identify gaps in the user's knowledge. Provide guidance on how to approach the information-gathering process effectively."
        },
        {
            "title": "Identify Options",
            "description": "List all possible alternatives for your decision.",
            "fields": [
                {
                    "name": "options",
                    "type": "list_of_objects",
                    "label": "Options",
                    "description": "List of potential choices or alternatives",
                    "object_structure": {
                        "name": "text",
                        "description": "textarea"
                    },
                    "placeholder": "e.g., Option 1: Stay in current role, Option 2: Transition to software development full-time"
                }
            ],
            "ai_instructions": "Encourage brainstorming without judgment, suggest considering unconventional alternatives, and help break down complex options into simpler ones. Provide examples of creative options that the user might not have considered."
        },
        {
            "title": "Establish Criteria",
            "description": "Determine the factors that are important in making this decision.",
            "fields": [
                {
                    "name": "criteria",
                    "type": "list_of_objects",
                    "label": "Decision Criteria",
                    "description": "Factors to consider when evaluating options",
                    "object_structure": {
                        "name": "text",
                        "description": "textarea",
                        "weight": {
                            "type": "number",
                            "min": 0,
                            "max": 100,
                            "step": 1
                        }
                    },
                    "validation": {
                        "total_weight": {
                            "max": 100,
                            "message": "The sum of all weights must not exceed 100."
                        }
                    },
                    "placeholder": "e.g., Criterion: Potential income, Description: Expected salary and benefits, Weight: 8"
                }
            ],
            "ai_instructions": "Help the user consider both rational and emotional factors. Suggest prioritizing criteria based on personal values and goals. Encourage being specific about what each criterion means and why it's important."
        },
        {
            "title": "Evaluate Options",
            "description": "Assess each option against your established criteria.",
            "fields": [
                {
                    "name": "evaluations",
                    "type": "matrix",
                    "label": "Option Evaluations",
                    "description": "Rate each option against each criterion",
                    "matrix_structure": {
                        "rows": {
                            "source": "options",
                            "step": "Identify Options",
                            "field": "options"
                        },
                        "columns": {
                            "source": "criteria",
                            "step": "Establish Criteria",
                            "field": "criteria",
                            "use": "name"
                        }
                    },
                    "cell_format": {
                        "type": "number",
                        "min": 1,
                        "max": 5,
                        "step": 1
                    }
                },
                {
                    "name": "option_notes",
                    "type": "list_of_objects",
                    "label": "Option Notes",
                    "description": "Additional notes on strengths and weaknesses of each option",
                    "object_structure": {
                        "option": "text",
                        "strengths": "textarea",
                        "weaknesses": "textarea"
                    },
                    "dependencies": {
                        "option": {"step": "Identify Options", "field": "options"}
                    }
                }
            ],
            "ai_instructions": "Suggest using a consistent rating system for all options. Encourage considering both short-term and long-term impacts. Provide guidance on how to be as objective as possible in assessments while acknowledging emotional factors."
        },
        {
            "title": "Consider Consequences",
            "description": "Analyze the potential outcomes and risks of each option.",
            "fields": [
                {
                    "name": "consequences",
                    "type": "list_of_objects",
                    "label": "Potential Consequences",
                    "description": "List of possible outcomes for each option",
                    "object_structure": {
                        "option": "text",
                        "short_term": "textarea",
                        "long_term": "textarea",
                        "risks": "textarea"
                    },
                    "dependencies": {
                        "option": {"step": "Identify Options", "field": "options"}
                    }
                },
                {
                    "name": "risk_mitigation",
                    "type": "list_of_objects",
                    "label": "Risk Mitigation Strategies",
                    "description": "Strategies to address identified risks",
                    "object_structure": {
                        "risk": "text",
                        "strategy": "textarea"
                    }
                }
            ],
            "ai_instructions": "Prompt the user to imagine best-case and worst-case scenarios. Encourage consideration of how each option aligns with long-term goals. Help identify potential regrets and ways to mitigate risks."
        },
        {
            "title": "Make the Decision",
            "description": "Choose the best option based on your evaluation and analysis.",
            "fields": [
                {
                    "name": "chosen_option",
                    "type": "select",
                    "label": "Chosen Option",
                    "description": "The option you've decided to pursue",
                    "dependencies": {
                        "options": {"step": "Identify Options", "field": "options"}
                    }
                },
                {
                    "name": "decision_rationale",
                    "type": "textarea",
                    "label": "Decision Rationale",
                    "description": "Explanation of why you chose this option"
                }
            ],
            "ai_instructions": "Encourage trusting the analysis while also listening to intuition. Suggest discussing the choice with a trusted advisor if appropriate. Provide strategies for overcoming decision paralysis and feeling confident about the choice."
        },
        {
            "title": "Create an Action Plan",
            "description": "Develop a step-by-step plan to implement your decision.",
            "fields": [
                {
                    "name": "action_steps",
                    "type": "list_of_objects",
                    "label": "Action Steps",
                    "description": "Specific steps to implement your decision",
                    "object_structure": {
                        "description": "text",
                        "timeline": "text",
                        "resources_needed": "textarea"
                    }
                },
                {
                    "name": "potential_obstacles",
                    "type": "list",
                    "label": "Potential Obstacles",
                    "description": "Possible challenges in implementing your decision"
                },
                {
                    "name": "obstacle_strategies",
                    "type": "list_of_objects",
                    "label": "Strategies for Overcoming Obstacles",
                    "description": "Plans to address potential challenges",
                    "object_structure": {
                        "obstacle": "text",
                        "strategy": "textarea"
                    }
                }
            ],
            "ai_instructions": "Help break down the implementation into manageable tasks. Encourage setting specific, measurable goals. Assist in identifying potential obstacles and developing strategies to overcome them."
        },
        {
            "title": "Reflect and Learn",
            "description": "Review the outcomes of your decision and extract lessons for future decision-making.",
            "fields": [
                {
                    "name": "outcomes",
                    "type": "textarea",
                    "label": "Decision Outcomes",
                    "description": "Describe the results of implementing your decision"
                },
                {
                    "name": "lessons_learned",
                    "type": "list",
                    "label": "Lessons Learned",
                    "description": "Key insights gained from this decision-making process"
                },
                {
                    "name": "future_improvements",
                    "type": "textarea",
                    "label": "Future Improvements",
                    "description": "How you can improve your decision-making process in the future"
                }
            ],
            "ai_instructions": "Suggest scheduling regular check-ins to assess progress. Encourage being open to adjusting the plan if needed. Prompt the user to document what worked well and what could be improved in their decision-making process."
        }
    ]
}