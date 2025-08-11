from concurrent.futures import ThreadPoolExecutor
from celery import current_app as celery_app
from datetime import datetime, timedelta
import time
import asyncio
from sqlalchemy.orm import Session
from databases.my_sql.user_table import User
from services.gaurdrails_groq.groq_guardrails import GroqGuardrail, GroqInputGuardrailTriggeredException
from tot.tot_integration import TotRagIntegration
from utils.db.chat_count import update_chat_counter
from utils.db.connect_to_my_sql import SessionLocal
from utils.db.user_utils import reset_cross_limit_if_expired, check_and_update_premium_status
from utils.retrivers.retreiver import AutomergingRetriverInit
from utils.retrivers.retriver_init import get_data_sources
from utils.tools.tool_support_functions import clean_response_text
import utils.file_server.fileserver as fileserver


storage_contexts, embed_model = get_data_sources()
auto_merging_retriever = AutomergingRetriverInit(storage_contexts, embed_model)


@celery_app.task(bind=True)
def process_chat(self, query, email: str):
    db: Session = SessionLocal()  # ✅ Initialize DB inside task
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {
                "status": "error",
                "error": "User not found",
                "timestamp": datetime.utcnow().isoformat()
            }

        # ✅ Check premium expiry
        user = check_and_update_premium_status(user, db)

        if not user.is_premium:
            # ✅ Handle free user limit logic
            user = reset_cross_limit_if_expired(user, db)
            if user.is_cross_limit_per_day:
                print("❌ OverLimit triggered")
                return {
                    "status": "over limit",
                    "error": f"User limit is over until {user.expired_at}.",
                    "links": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "timings": {}
                }

        overall_start_time = time.time()
        timings = {}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        executor = ThreadPoolExecutor(max_workers=15)

        async def run_chat_pipeline():
            try:
                # Step 1: Guardrail classification
                guardrail = GroqGuardrail()
                agent_start = time.time()
                agent_task = loop.run_in_executor(executor, guardrail.run_guardrail, query)
                category_output = await agent_task
                agent_time = time.time() - agent_start

                category = category_output.get("category")
                if not category or category in ["not_legal", "other"]:
                    return {
                        "message": "Your query doesn't match any supported legal category.",
                        "links": [],
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "blocked",
                        "timings": {}
                    }

                # Step 2: Retrieve
                automerge_start = time.time()
                automerge_task = loop.run_in_executor(
                    executor,
                    auto_merging_retriever.automerging_retrival_pipeline,
                    query,
                    category
                )
                retrieved_nodes = await automerge_task
                automerge_time = time.time() - automerge_start

                # Step 3: ToT Enhancement
                tot_start = time.time()
                tot_rag = TotRagIntegration(
                    threshold=0.8,
                    max_loops=3,
                    prune_threshold=0.5,
                    number_of_agents=3,
                    use_openai_caller=False
                )
                node_texts = [
                    node.text for node in retrieved_nodes if hasattr(node, "text")
                ]
                enhanced_response = await tot_rag.enhance_response(query, node_texts)
                tot_time = time.time() - tot_start

                # Step 4: Build links
                links = []
                for node in retrieved_nodes:
                    metadata = getattr(node, "metadata", {}) or getattr(node, "metadata_dict", {})
                    if not isinstance(metadata, dict):
                        continue

                    file_name = metadata.get("source_file")
                    page_number = metadata.get("page_number")

                    if file_name and page_number:
                        link = fileserver.generate_download_link(category=category, file_name=file_name)
                        links.append({
                            "title": file_name,
                            "page": page_number,
                            "link": link
                        })

                timings.update({
                    "automerge_duration": round(automerge_time, 2),
                    "agent_duration": round(agent_time, 2),
                    "tot_duration": round(tot_time, 2),
                    "total_duration": round(time.time() - overall_start_time, 2)
                })

                return {
                    "message": clean_response_text(enhanced_response),
                    "links": links,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                    "timings": timings
                }

            except GroqInputGuardrailTriggeredException:
                return {
                    "message": "Please ask questions relevant to the legal categories supported.",
                    "links": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "blocked",
                    "timings": {}
                }

        result = loop.run_until_complete(run_chat_pipeline())

        print("===================================================")
        print(f"✅ Total response time: {result.get('timings', {}).get('total_duration', 'N/A')} seconds")
        print("⏱️ Timings:", result["timings"])
        print("===================================================")

        # if result["status"] == "success":
            # update_chat_counter(user, db)

        return result

    except Exception as e:
        print(f"❌ Error in process_chat: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()  # ✅ Always close DB session
