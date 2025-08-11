import uuid
import json
from typing import Optional
from swarms import create_file_in_folder
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from loguru import logger
from dotenv import load_dotenv
import asyncio

from tot.agent import TotAgent

load_dotenv()


class ToTDFSAgent:
    """
    A class to perform Depth-First Search (DFS) using the TotAgent, with pruning based on evaluation scores.

    Methods:
        dfs(state: str, step: int = 0) -> Optional[Thought]: Performs DFS with pruning and returns the final thought.
        visualize_thoughts(thoughts: List[Thought]): Visualizes all thoughts including the highest-rated thought.
    """

    def __init__(
        self,
        agent: TotAgent,
        threshold: float,
        max_loops: int,
        prune_threshold: float = 0.8,
        number_of_agents: int = 1,
        autosave_on: bool = True,
        id: str = uuid.uuid4().hex,
        *args,
        **kwargs,
    ):
        """
        Initialize the ToTDFSAgent class.

        Args:
            agent (TotAgent): An instance of the TotAgent class to generate and evaluate thoughts.
            threshold (float): The evaluation threshold for selecting promising thoughts.
            max_loops (int): The maximum depth for the DFS algorithm.
            prune_threshold (float): The threshold below which branches are pruned. Default is 0.5.
        """
        self.id = id
        self.agent = agent
        self.threshold = threshold
        self.max_loops = max_loops
        self.prune_threshold = prune_threshold
        self.all_thoughts = []  # Store all thoughts generated during DFS
        self.pruned_branches = []  # Store metadata on pruned branches
        self.number_of_agents = number_of_agents
        self.autosave_on = autosave_on

        self.agent.max_loops = max_loops

    async def dfs(self, state: str, step: int = 0) -> Optional[Dict[str, Any]]:
        if step >= self.max_loops:
            return None

        print(f"🧠 DFS Step {step} — Requesting {self.number_of_agents} thoughts...")

        # 🔥 Make one batched call instead of N loops
        all_thoughts = await self.agent.run(state, n=self.number_of_agents)

        all_thoughts.sort(key=lambda x: x["evaluation"])

        for thought in all_thoughts:
            if thought["evaluation"] > self.prune_threshold:
                self.all_thoughts.append(thought)
                result = await self.dfs(thought["thought"], step + 1)
                if result and result["evaluation"] > self.threshold:
                    return result
            else:
                self._prune_thought(thought)

        return self.all_thoughts[-1] if self.all_thoughts else {"thought": "No valid thoughts found."}

    def _prune_thought(self, thought: Dict[str, Any]):
        self.pruned_branches.append(
            {
                "thought": thought["thought"],
                "evaluation": thought["evaluation"],
                "reason": "Evaluation score below threshold",
            }
        )

    async def run(self, task: str, *args, **kwargs) -> str:

        # Initialize the first agent run
        initial_thoughts = await self.dfs(task, *args, **kwargs)

        # Chain the agents' outputs through subsequent agents
        for i in range(1, self.max_loops):
            if initial_thoughts:
                next_task = initial_thoughts["thought"]
                initial_thoughts = await self.dfs(next_task, step=i)
            else:
                break

        # After chaining, sort all final thoughts
        self.all_thoughts.sort(key=lambda x: x["evaluation"], reverse=False)

        tree_dict = {
            "final_thoughts": self.all_thoughts,
            "pruned_branches": self.pruned_branches,
            "highest_rated_thought": (
                self.all_thoughts[-1] if self.all_thoughts else None
            ),
        }

        json_string = json.dumps(tree_dict, indent=4)

        if self.autosave_on:
            create_file_in_folder(
                "tree_of_thoughts_runs",
                f"tree_of_thoughts_run{self.id}.json",
                json_string,
            )

        # If no good thoughts, fall back to best pruned
        if not self.all_thoughts and self.pruned_branches:
            best_pruned = max(self.pruned_branches, key=lambda x: x["evaluation"])
            tree_dict["highest_rated_thought"] = best_pruned

        if self.autosave_on:
            create_file_in_folder(
                "tree_of_thoughts_runs",
                f"tree_of_thoughts_run{self.id}.json",
                json.dumps(tree_dict, indent=4),
            )

        return tree_dict["highest_rated_thought"]

