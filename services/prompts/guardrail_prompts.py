relevancy_guardrail_prompt = """
- Check if user queries are related to Sri Lankan law and its recognized categories (e.g., criminal law, contract law, property law, family law, etc.).
- Do not answer any queries unrelated to the legal domain (e.g., cooking, entertainment, fitness).
- Do not answer queries about legal systems of other countries (e.g., Indian law, US law, UK law).
- Do not answer highly personal or one-off legal disputes unless the query is about a general legal procedure or public rule.
- Do not answer religious/cultural issues unless governed by recognized personal laws (Kandyan, Muslim, Tesawalamai).
- Answer if it's about Sri Lankan laws, legal definitions, rights, or procedures—even if the specific law is not mentioned.

###### Examples #######
query 1: - How to file a Fundamental Rights petition in Sri Lanka?  
→ Relevant: Constitutional legal procedure

query 2: - What are the marriage laws under Kandyan Law?  
→ Relevant: Recognized Sri Lankan personal law

query 3: - How to bake a cake?  
→ Not Relevant: Not related to law

query 4: - Can I get a divorce in the US if I am Sri Lankan?  
→ Not Relevant: Concerns foreign legal jurisdiction

query 5: - How to transfer property ownership in Sri Lanka?  
→ Relevant: General legal procedure under property law

Return your response as:
{ "relevancy": "relevant" or "not relevant","category": "category_name", "reasoning": "brief reason" }
!!! give me category name same as provided
"""
security_guardrail_prompt = """
- Check if the query asks for private legal data like case numbers, addresses, NIC numbers, or names of individuals.
- Do not answer if it includes identifiable case information or contact details.
- It's safe to answer general questions about legal procedures, law definitions, or common processes.
- Explaining a law or how it is applied generally is NOT a security threat.

###### Examples #######
query 1: - What is the penalty for theft under Sri Lankan law?  
→ Not a security threat

query 2: - My case number is HC/1234/2023, what will happen?  
→ Security threat: Reveals personal case info

query 3: - How to apply for bail?  
→ Not a security threat: General procedure

query 4: - What’s the email of the judge in Colombo High Court?  
→ Security threat: Requests private info

Return your response as:
{ "relevancy": "relevant" or "not relevant","category": "category_name", "reasoning": "brief reason" }
!!! give me category name same as provided
"""
legal_category_classification_prompt = """
- Classify the user's legal question strictly into one of the official legal categories listed below.
- You must return the category name **exactly as written below**.
- Do NOT invent or rephrase category names (e.g., use "law_of_crimes", not "criminal law").
- If the query doesn't match any category, return "other".
- If the query is not legal in nature, return "not_legal".
- If unsure, use "other". Do not guess.

### Valid Categories (Use exactly as shown) ###
- law_of_crimes
- law_of_contracts
- law_of_delict
- law_of_property
- family_law
- succession_law
- commercial_law
- labour_law
- constitutional_law
- administrative_law
- environmental_law
- taxation_law
- consumer_law
- customary_laws
- muslim_personal_law
- kandyan_law
- tesawalamai_law
- intellectual_property_law
- cyber_law
- human_rights_law
- international_law
- immigration_law
- banking_and_finance_law
- education_law
- media_and_communication_law
- other
- not_legal

###### Format your response as strictly JSON ######
{ "relevancy": "relevant" or "not relevant", "category": "one_of_the_above_exactly", "reasoning": "brief reason" }

###### Examples ######
query 1: - What are the penalties under the Penal Code?  
→ { "relevancy": "relevant", "category": "law_of_crimes", "reasoning": "Query relates to criminal offences and punishments." }

query 2: - How to register a lease agreement?  
→ { "relevancy": "relevant", "category": "law_of_property", "reasoning": "Lease agreements fall under property law." }

query 3: - What is Tesawalamai law?  
→ { "relevancy": "relevant", "category": "tesawalamai_law", "reasoning": "Asks about a recognized Sri Lankan customary law." }

query 4: - How to improve memory for exams?  
→ { "relevancy": "not relevant", "category": "not_legal", "reasoning": "Query is not about any legal subject." }

query 5: - I want to apply for a passport.  
→ { "relevancy": "relevant", "category": "immigration_law", "reasoning": "Concerns immigration documents and procedures." }
"""
