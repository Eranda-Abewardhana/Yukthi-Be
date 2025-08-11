import os
import uuid
import asyncio
from groq import Groq
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import ast

load_dotenv()


def string_to_dict(thought_string):
    return ast.literal_eval(thought_string)


TREE_OF_THOUGHTS_SYS_PROMPT = """
You are an expert legal problem-solving agent built for the Yukti platform — a chatbot designed to answer Sri Lankan law-related questions accurately and responsibly. Your task is to solve complex legal queries by following a structured thought process and critically evaluating each step and the final output based on the provided context.

You must reason in multiple steps using a Tree of Thoughts (ToT) strategy and assign a quality rating for each step to ensure clarity, correctness, and context relevance. Provide only the final answer unless an illustrative example is necessary — in which case, format it clearly and professionally.

### Instructions:

#### 1. Understand the Problem:
- Carefully read and analyze the user’s legal query.
- Break down the problem into smaller parts if needed (e.g., jurisdiction, legal context, procedural steps).
- Formulate a clear understanding of what is being asked and identify key legal concepts.

#### 2. Generate Thoughts:
- Propose multiple logical steps or thoughts toward solving the legal problem.
- For each thought, explain your reasoning in a clear, well-structured format (e.g., citing legal principles or procedures).
- Keep the context limited to Sri Lankan law only (e.g., Constitution of Sri Lanka, Penal Code, Labour Laws, etc.).

#### 3. Self-Evaluate Each Thought:
   - After generating each thought, evaluate its accuracy and quality.
   - Assign an evaluation score between 0.1 and 1.0. Use the following guidelines:
     - **0.1 to 0.4:** The thought is flawed, inaccurate, or incomplete.
     - **0.5 to 0.7:** The thought is partially correct but may lack detail or full accuracy.
     - **0.8 to 1.0:** The thought is accurate, complete, and well-reasoned.


#### 4. Generate Final Answer:
- Synthesize your best thoughts into a **clear, final legal answer**.
- Use bullet points or paragraph format where appropriate.
- Only include an example if it helps clarify the concept — and present it cleanly (e.g., "Example: If a tenant refuses to...").


#### 5. Final Evaluation:
- Evaluate the overall quality and accuracy of your final response.
- Provide a **final evaluation score** (same 0.1 to 1.0 scale) to reflect how well your answer satisfies the query and follows Sri Lankan legal standards.

---

**Note:** Avoid using non-Sri Lankan legal references. Your responses must be jurisdiction-specific to Sri Lanka. Always prioritize legal accuracy, clarity, and responsible advice according to the provided context.

"""


class Thought(BaseModel):
    thought: str
    evaluation: Optional[float] = Field(
        description="The evaluation of the thought. It can be a number between 0.1 and 1.0 being 0.1 the worst and 1.0 the best."
    )


class TotAgent:
    def __init__(
        self,
        id: str = uuid.uuid4().hex,
        model: str = "gpt-4.1-nano",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        *args,
        **kwargs,
    ):
        self.id = id
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def run(self, task: str, n: int = 1) -> List[Dict[str, Any]]:
        """
        Generate `n` thoughts concurrently using OpenAI API.
        Returns a list of dictionaries containing 'thought' and 'evaluation'.
        """
        client = AsyncOpenAI()

        API_KEY = os.getenv("GROQ_API_KEY")

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        client = Groq(api_key=API_KEY)

        def call_groq(task, system_prompt, n=1, temperature=0.1, max_tokens=20000):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # You may also use "mixtral-8x7b-32768"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ],
                temperature=temperature,
                #max_tokens=max_tokens,
                n=n
            )

            results = []
            for choice in response.choices:
                content = choice.message.content
                try:
                    parsed = string_to_dict(content.strip())
                    if isinstance(parsed, dict) and "thought" in parsed and "evaluation" in parsed:
                        results.append(parsed)
                    else:
                        results.append({"thought": content.strip(), "evaluation": 0.5})
                except Exception:
                    results.append({"thought": content.strip(), "evaluation": 0.5})
            return results

        results = call_groq(task,TREE_OF_THOUGHTS_SYS_PROMPT)
        return results
