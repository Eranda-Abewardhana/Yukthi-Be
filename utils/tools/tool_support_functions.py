import openai
from dotenv import load_dotenv
import re

load_dotenv()

def embed_text(text: str) -> list:
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=[text]
    )
    return response.data[0].embedding

import re

def clean_response_text(text: str) -> str:
    # 1. Extract only the "Final Answer" section if present
    match = re.search(r"(Final Answer:|🔍 Final Answer:)(.*)", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(2)

    # 2. Remove rating lines like **Rating: 0.9**
    text = re.sub(r"\*\*Rating:.*?\*\*", "", text)

    # 3. Remove markdown headings (#, ##, ###)
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)

    # 4. Remove emphasis markers like *text* or **
    text = re.sub(r"\*+", "", text)

    # 5. Split into lines and build HTML
    lines = text.strip().split("\n")
    html_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # If the line looks like a bullet point, wrap in <li>
        if re.match(r"[-–•]\s+", line):
            html_lines.append(f"<li>{line[1:].strip()}</li>")
        else:
            html_lines.append(f"<p>{line}</p>")

    # 6. If there are <li> elements, wrap them in <ul>
    if any(line.startswith("<li>") for line in html_lines):
        ul_lines = [line for line in html_lines if line.startswith("<li>")]
        p_lines = [line for line in html_lines if not line.startswith("<li>")]
        return f"<div><h3>Final Answer</h3>{''.join(p_lines)}<ul>{''.join(ul_lines)}</ul></div>"
    else:
        return f"<div><h3>Final Answer</h3>{''.join(html_lines)}</div>"
