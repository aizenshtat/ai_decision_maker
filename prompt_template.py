import json

from decision_framework import PERSONAL_DECISION_FRAMEWORK

PROMPT_TEMPLATE = """
Step: {step_title}

{step_description}

Current Decision Context:
{current_context}

Please provide guidance for the user on this step of their decision-making process. 
Consider the following fields that the user needs to complete:

{fields}

Based on the user's input so far and the requirements of this step, provide:
1. A brief explanation and suggestions for this step (in markdown format)
2. Pre-filled data for the user input fields, based on your best guess of what user would write

Please structure your response in the following JSON format:

{{
    "suggestion": "Your brief markdown-formatted suggestion here",
    "pre_filled_data": {{
        {field_format}
    }}
}}
"""

def generate_field_format(fields):
    formats = []
    for field in fields:
        if field['type'] == 'list':
            formats.append(f'"{field["name"]}": ["Example 1", "Example 2", "Example 3"]')
        elif field['type'] == 'list_of_objects':
            object_format = ", ".join([f'"{k}": "Example {k}"' for k in field['object_structure'].keys()])
            formats.append(f'"{field["name"]}": [{{{object_format}}}, {{{object_format}}}]')
        else:
            formats.append(f'"{field["name"]}": "Example {field["name"]}"')
    return ",\n        ".join(formats)

def generate_prompt(step, current_context):
    fields_text = "\n".join([f"- {field['label']}: {field['description']}" for field in step['fields']])
    field_format = generate_field_format(step['fields'])
    # Parse the current_context if it's a string, otherwise use it as is
    if isinstance(current_context, str):
        context_dict = json.loads(current_context)
    else:
        context_dict = current_context

    formatted_context = "\n".join([f"{key}:\n{json.dumps(value, indent=2)}" for key, value in context_dict.items()])
    
    return PROMPT_TEMPLATE.format(
        step_title=step['title'],
        step_description=step['description'],
        current_context=formatted_context,
        fields=fields_text,
        field_format=field_format
    )