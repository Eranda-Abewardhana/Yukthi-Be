import os
import asyncio
import time
import tkinter as tk
from datetime import datetime

from PIL import ImageTk, Image
from tkinter import scrolledtext
import concurrent.futures  # ✅ Added for global executor

from agents import Runner
from data_modals.pydantic_models.dataclass_modals import UserContext
from agents import Runner, InputGuardrailTripwireTriggered

from tasks.chat_tasks import auto_merging_retriever
from tot.tot_integration import TotRagIntegration
from utils.file_server import fileserver
from utils.retrivers.retriver_init import get_data_sources
from utils.retrivers.retreiver import AutomergingRetriverInit
import utils.file_server.fileserver
from services.gaurdrails_groq.groq_guardrails import GroqGuardrail, GroqInputGuardrailTriggeredException

# from utils.tools.tool_support_functions import search_pinecone


key = os.getenv('OPENAI_API_KEY')
print(key)
timings = {}
# ✅ Global ThreadPoolExecutor (shared across all tasks)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

storage_contexts, embed_model = get_data_sources()
auto_merging_retriever = AutomergingRetriverInit(storage_contexts, embed_model)

groq_gaurdrail_obj = GroqGuardrail()

root = tk.Tk()
root.title("Commercial Bank - Virtual Assistant")

# Colors
background_color = "#f2f2f2"
user_color = "#007acc"
bot_color = "#228B22"
root.configure(bg=background_color)

# Load icons
user_icon = ImageTk.PhotoImage(Image.open("user.png").resize((40, 40)))
bot_icon = ImageTk.PhotoImage(Image.open("bot.png").resize((40, 40)))

# Chat area
chat_frame = tk.Frame(root, bg=background_color)
chat_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

chat_log = scrolledtext.ScrolledText(
    chat_frame, bg="white", fg="black", font=("Arial", 12), state=tk.DISABLED, wrap=tk.WORD, relief=tk.FLAT
)
chat_log.pack(fill=tk.BOTH, expand=True)

# User input area
input_frame = tk.Frame(root, bg=background_color)
input_frame.pack(padx=20, pady=(0, 20), fill=tk.X)

entry = tk.Entry(input_frame, font=("Arial", 12), relief=tk.GROOVE, bd=3)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=5)


# --- Async support ---
def run_async_task(coro):
    asyncio.create_task(coro)


send_button = tk.Button(
    input_frame, text="Send", font=("Arial", 12, "bold"),
    bg="#4CAF50", fg="white", activebackground="#45a049",
    relief=tk.RAISED, bd=3, command=lambda: run_async_task(send_message())
)
send_button.pack(side=tk.RIGHT)


# --- Functions ---

##############################################################################################

async def send_message(event=None):
    user_text = entry.get()
    if not user_text.strip():
        return

    display_message(user_text, sender="user")
    entry.delete(0, tk.END)

    context = UserContext(index='DEFAULT_INDEX_OPERATIONS', user_input_query=user_text)

    try:
        try:
            overall_start_time = time.time()
            loop = asyncio.get_running_loop()

            agent_start = time.time()
            guardrail = GroqGuardrail()
            agent_task = loop.run_in_executor(executor, guardrail.run_guardrail, user_text)

            # Step 1: Classify category
            category_output = await agent_task
            print(category_output)
            category = category_output.get("category")

            if not category or category in ["not_legal", "other"]:
                return {
                    "message": "Your query doesn't match any supported legal category.",
                    "links": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "blocked",
                    "timings": {}
                }

            # Step 2: Retrieve relevant chunks
            automerge_start = time.time()
            automerge_task = loop.run_in_executor(
                executor,
                auto_merging_retriever.automerging_retrival_pipeline,
                user_text,
                category
            )

            retrieved_nodes = await automerge_task
            automerge_time = time.time() - automerge_start

            # Start ToT as soon as AutoMerge is done
            tot_start = time.time()
            tot_rag = TotRagIntegration(
                threshold=0.8,
                max_loops=1,
                prune_threshold=0.5,
                number_of_agents=1,
                use_openai_caller=False
            )
            print("Example node:", retrieved_nodes[0])
            print("Type:", type(retrieved_nodes[0]))
            # Step 3: Extract text from nodes for ToT enhancement
            node_texts = []
            for node in retrieved_nodes:
                # Safely handle nodes that are not objects with a 'text' attribute
                if hasattr(node, "text"):
                    node_texts.append(node.text)
                elif isinstance(node, str):
                    node_texts.append(node)
                else:
                    print("⚠️ Skipping node without valid text:", node)

            # Step 4: Enhance response using ToT
            enhanced_response = await tot_rag.enhance_response(user_text, node_texts)
            tot_time = time.time() - tot_start

            # Step 5: Guardrail check completion
            agent_response = await agent_task
            agent_time = time.time() - agent_start

            # Assume all `retrieved_nodes` are Node objects
            node_texts = [node.text for node in retrieved_nodes if hasattr(node, "text")]

            links = []

            for idx, node in enumerate(retrieved_nodes):
                print(f"\n[DEBUG] Node #{idx} — Type: {type(node)}")
                print(f"[DEBUG] Full node content:\n{repr(node)}")

                node_id = getattr(node, "node_id", None)
                if not node_id:
                    print("[DEBUG] ⚠️ Node has no node_id, skipping.")
                    continue

                metadata = getattr(node, "metadata", {}) or getattr(node, "metadata_dict", {})

                if not isinstance(metadata, dict):
                    print(f"[DEBUG] ❌ metadata for node_id {node_id} is not a dict.")
                    continue

                print(f"[DEBUG] ✅ Metadata keys found: {list(metadata.keys())}")

                file_name = metadata.get("source_file")
                page_number = metadata.get("page_number")

                if not file_name:
                    print("[DEBUG] ⚠️ Missing `source_file` in metadata")
                if not page_number:
                    print("[DEBUG] ⚠️ Missing `page_number` in metadata")

                if file_name and page_number:
                    link = fileserver.generate_download_link(category=category, file_name=file_name)
                    print(f"[DEBUG] ✅ Link generated for file: {file_name}, page: {page_number}")
                    links.append({
                        "title": file_name,
                        "page": page_number,
                        "link": link
                    })

            print(f"\n[DEBUG] ✅ Total links generated: {len(links)}")
            print("Links:", links)

            # Step 6: Build timing stats
            timings.update({
                "automerge_duration": round(automerge_time, 2),
                "agent_duration": round(agent_time, 2),
                "tot_duration": round(tot_time, 2),
                "total_duration": round(time.time() - overall_start_time, 2)
            })

        except GroqInputGuardrailTriggeredException:
            display_message("Please Ask Questions Relevant To Sri Lankan Law", sender="bot")

    except Exception as e:
        display_message(f"An error occurred: {e}", sender="bot")


##############################################################################################

def display_message(message, sender="bot"):
    chat_log.config(state=tk.NORMAL)
    if sender == "user":
        chat_log.insert(tk.END, "\n", "spacer")
        chat_log.image_create(tk.END, image=user_icon)
        chat_log.insert(tk.END, f"  You:\n{message}\n", "user")
    else:
        chat_log.insert(tk.END, "\n", "spacer")
        chat_log.image_create(tk.END, image=bot_icon)
        chat_log.insert(tk.END, f"  Assistant:\n{message}\n", "bot")

    chat_log.config(state=tk.DISABLED)
    chat_log.see(tk.END)


# Tag styles
chat_log.tag_configure("user", foreground=user_color, font=("Arial", 12, "bold"))
chat_log.tag_configure("bot", foreground=bot_color, font=("Arial", 12))
chat_log.tag_configure("spacer", spacing1=10, spacing3=10)

# Key binding
root.bind('<Return>', lambda event: run_async_task(send_message()))

# Window size
root.geometry("700x650")
root.minsize(600, 550)


# Async-compatible Tkinter mainloop
async def main():
    while True:
        try:
            root.update()
            await asyncio.sleep(0.01)
        except tk.TclError:
            break  # Window closed


asyncio.run(main())
