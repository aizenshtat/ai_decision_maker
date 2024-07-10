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
1. A brief explanation and suggestions for this step (in markdown format) Important: always use \\n for new lines.
2. Pre-filled data for the user input fields, based on your best guess of what user would write

Please ensure that your pre-filled data adheres to the field types, structures, and validations described above.

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
        if field['type'] == 'matrix':
            formats.append(f'"{field["name"]}": {{"Option1": {{"Criterion1": 5, "Criterion2": 4}}, "Option2": {{"Criterion1": 3, "Criterion2": 5}}}}')
        elif field['type'] == 'list_of_objects':
            object_format = ", ".join([f'"{k}": "Example {k}"' for k in field['object_structure'].keys()])
            formats.append(f'"{field["name"]}": [{{{object_format}}}, {{{object_format}}}]')
        elif field['type'] == 'list':
            formats.append(f'"{field["name"]}": ["Example 1", "Example 2", "Example 3"]')
        else:
            formats.append(f'"{field["name"]}": "Example {field["name"]}"')
    return ",\n        ".join(formats)

def generate_field_description(field):
    description = f"- {field['label']}: {field['description']}\n"
    description += f"  Type: {field['type']}\n"
    
    if field['type'] == 'matrix':
        description += f"  Matrix Structure:\n"
        description += f"    Rows: {field['matrix_structure']['rows']}\n"
        description += f"    Columns: {field['matrix_structure']['columns']}\n"
        if 'cell_format' in field:
            description += f"  Cell Format: {field['cell_format']}\n"
    elif field['type'] == 'list_of_objects':
        description += f"  Object Structure: {field['object_structure']}\n"
    
    if 'validation' in field:
        description += f"  Validation: {field['validation']}\n"
    
    if 'dependencies' in field:
        description += f"  Dependencies: {field['dependencies']}\n"
    
    return description

def generate_prompt(step, current_context):
    fields_text = "\n".join([generate_field_description(field) for field in step['fields']])
    field_format = generate_field_format(step['fields'])
    
    # Parse the current_context if it's a string, otherwise use it as is
    if isinstance(current_context, str):
        context_dict = json.loads(current_context)
    else:
        context_dict = current_context

    formatted_context = "\n".join([f"{key}:\n{json.dumps(value, indent=2)}" for key, value in context_dict.items()])
    
    return PROMPT_TEMPLATE.format(
        step_title=step['title'],
        step_description=step.get('description', 'No description provided'),
        current_context=formatted_context,
        fields=fields_text,
        field_format=field_format
    )