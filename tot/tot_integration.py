import asyncio
import time
import html
from typing import List

from tot.agent import TotAgent
from tot.dfs import ToTDFSAgent


class TotRagIntegration:
    """
    Integrates Tree of Thoughts (ToT) reasoning with RAG retrievals for a chatbot.
    Enhances retrieved chunks using the ToT agent and DFS logic.
    """

    def __init__(
        self,
        threshold: float = 0.8,
        max_loops: int = 5,
        prune_threshold: float = 0.5,
        number_of_agents: int = 1,
        use_openai_caller: bool = False,
    ):
        """
        Initialize the TotRagIntegration class.
        """
        print("[INIT] Initializing ToT-RAG Integration...")

        self.tot_agent = TotAgent(use_openai_caller=use_openai_caller)
        self.dfs_agent = ToTDFSAgent(
            agent=self.tot_agent,
            threshold=threshold,
            max_loops=max_loops,
            prune_threshold=prune_threshold,
            number_of_agents=number_of_agents,
        )

        print(f"[INIT] ToTDFSAgent configured with threshold={threshold}, max_loops={max_loops}, prune_threshold={prune_threshold}, number_of_agents={number_of_agents}")

    def format_context_for_tot(self, user_query: str, retrieved_chunks: List[str]) -> str:
        """
        Prepares the input prompt for ToT by embedding user query and retrieved context.
        """
        safe_user_query = html.escape(user_query)
        safe_context = html.escape("\n\n".join(retrieved_chunks))

        prompt = f"""
Your task: Generate a comprehensive and accurate response to the following user query based on the provided context information.

USER QUERY:
{safe_user_query}

CONTEXT INFORMATION:
{safe_context}

Instructions:
1. Use only information present in the CONTEXT INFORMATION to answer the query.
2. If the CONTEXT INFORMATION doesn't contain enough details to provide a complete answer, acknowledge this limitation.
3. Structure your answer in a clear, easy-to-understand format.
4. Be concise but thorough in your response.
"""
        return prompt.strip()

    async def enhance_response(self, user_query: str, retrieved_chunks: List[str]) -> str:
        """
        Enhances RAG-retrieved chunks using Tree of Thoughts (ToT) reasoning.
        """
        try:
            print("\n[ToT-RAG] Starting enhancement process...")
            t_start = time.time()

            # Step 1: Format context for ToT
            initial_prompt = self.format_context_for_tot(user_query, retrieved_chunks)
            print("\n[DEBUG] Initial ToT Prompt:")
            print("=" * 50)
            print(initial_prompt)
            print("=" * 50)
            print("$" * 50)
            print("Length of initial prompt: ", len(initial_prompt))
            print("$" * 50)

            # Step 2: Run ToT DFS Agent
            t_tot_start = time.time()
            print("\n[ToT-RAG] Running ToT DFS Agent...")
            final_thought = await self.dfs_agent.run(initial_prompt)
            t_tot_end = time.time()

            # Step 3: Process Output
            if isinstance(final_thought, dict) and "thought" in final_thought:
                full_text = final_thought["thought"]
            else:
                full_text = str(final_thought)

            print("\n[DEBUG] Raw ToT Output:")
            print("=" * 50)
            print(full_text)
            print("=" * 50)

            # Step 4: Extract final answer
            final_answer = self.extract_final_answer(full_text)

            t_end = time.time()
            # print(f"\n✅ ToT-RAG enhancement completed in {t_end - t_start:.2f} seconds")
            print(f"   - ToT DFS Agent execution time: {t_tot_end - t_tot_start:.2f} seconds")
            print(f"\n[FINAL ANSWER]\n{final_answer}\n")

            return final_answer

        except Exception as e:
            print(f"[ERROR] ToT-RAG enhancement failed: {e}")
            return f"An error occurred during response enhancement: {e}"

    def extract_final_answer(self, text: str) -> str:
        """
        Extracts the final answer by cutting off before the '### Final Evaluation' marker.
        """
        cutoff_marker = "### Final Evaluation"
        return text.split(cutoff_marker)[0].strip() if cutoff_marker in text else text.strip()

