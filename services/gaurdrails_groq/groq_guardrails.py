import json
import os

from groq import Groq

from difflib import SequenceMatcher

from services.prompts.guardrail_prompts import legal_category_classification_prompt, security_guardrail_prompt, \
    relevancy_guardrail_prompt

client = Groq(os.environ["GROQ_API_KEY"] )


class GroqInputGuardrailTriggeredException(Exception):
    """
    Custom exception class for groq guardrails
    """
    def __init__(self, message, reasoning):
        super().__init__(message)
        self.reasoning = reasoning

    def __str__(self):
        return f"reasoning : {self.reasoning}"


class GroqGuardrail:
    """
    Custom class to implement guardrails from groq inferencing service
    """

    # query = None

    def __init__(self):
        pass

    def call_groq(self, system_prompt,query, n=1, temperature=0.1, max_tokens=200):
            """
             Function to call groq inferencing service
            Args:
                system_prompt: Prompt to model
                query: user message
                n:
                temperature:
                max_tokens:

            Returns:

            """
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=n
            )
            return response.choices[0].message.content

    def exception_verifier(self,llm_output,reasoning):
        """
        Function to check if an exception needs to be thrown
        Args:
            llm_output: llM output relevant or not relevant
            reasoning: reasoning why the exeption is thrown

        Returns:No value retuns throws exeption when unsafe input is given

        """
        match_words = ["relevant","not relevant"] # PHRASES TO CHECK
        i = 0 # VARIABLE TO TRACK WHAT KEYWORD IS MATCHED
        match_value = None
        for word in match_words:
            similarity = SequenceMatcher(None,word, llm_output).ratio() # similarity check using difflib
            if similarity > 0.9 and i == 0: # check if llm output is close to relevant
                match_value = 0
            elif similarity >0.9 and i == 1:# check if llm output is close to not relevant
                match_value =1
            else:
                i = i + 1 # increment iterator

        if match_value == 0:
            pass
        else:
            print(llm_output)
            print("guardrail_reasoning: "+reasoning)
            raise GroqInputGuardrailTriggeredException(message="Operation Not Relevant",reasoning=reasoning)


    def run_guardrail(self,query):
        """
        Function  run all guardrails at once
        Args:
            query: user message

        Returns: None triggers a Exception if input not safe

        """
        guardrails = [legal_category_classification_prompt, relevancy_guardrail_prompt, security_guardrail_prompt]# SELECT prompt
        for guardrail in guardrails:
            groq_response = self.call_groq(guardrail,query)# running groq instances
            response_json = json.loads(groq_response)# LOADING groq response to dict
            self.exception_verifier(response_json['relevancy'],response_json['reasoning'])#verifying execptions
            return response_json

    def classify_category(self, query):
        """
        Classify the user's query into a legal category.
        Returns a dictionary: { "category": "...", "reasoning": "..." }
        """
        response = self.call_groq(legal_category_classification_prompt, query)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "category": "other",
                "reasoning": "Failed to parse model output as JSON."
            }











