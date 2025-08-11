from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
from databases.my_sql.user_table import User
from routes.login_routes import get_db
from services.auth.auth import get_current_user_jwt
from tasks.chat_tasks import process_chat
from agents import InputGuardrailTripwireTriggered
from data_modals.pydantic_models.response_modals import ChatResponse, ErrorResponse, RequestBody

load_dotenv()

chat_router = APIRouter()

@chat_router.post(
    "/chat",
    responses={
        200: {"model": ChatResponse},
        400: {"model": ErrorResponse}
    }
)
async def chat(request_body: RequestBody,
               email: str = Depends(get_current_user_jwt),
               db: Session = Depends(get_db)
               ):
    try:
        task = process_chat.delay(request_body.query, email)
        print(f"✅ Task created with ID: {task.id}")
        user = db.query(User).filter(User.email == email).first()
        result = task.get(timeout=100)
        status = result.get("status")

        if status == "success" or  status == "blocked":
            print(f"✅ Task {task.id} completed successfully.")
            print("⏱️ Timings:", result.get("timings"))
            return ChatResponse(
                message=result["message"],
                links=result["links"],
                timestamp=datetime.utcnow(),
                status="success"
            )
        elif status == "over limit":
            print(f"❌ Task {task.id} failed: {result.get('error')}")
            return JSONResponse(
                status_code=429,
                content=jsonable_encoder(ErrorResponse(
                    detail=result.get("error", f"User limit is over until {user.expired_at + timedelta(hours=12)}.",),
                    status="error",
                    links=[],
                    timestamp=datetime.utcnow()
                ))
            )
        else:
            print(f"❌ Task {task.id} failed: {result.get('error')}")
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(ErrorResponse(
                    detail=result.get("error", "Unknown error"),
                    status="error",
                    links=[],
                    timestamp=datetime.utcnow()
                ))
            )

    except InputGuardrailTripwireTriggered:
        print("❌ Guardrail triggered")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(ErrorResponse(
                detail="Ask relevant questions.",
                status="blocked",
                links=[],
                timestamp=datetime.utcnow()
            ))
        )

    except Exception as e:
        print(f"❌ Exception in /chat: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(ErrorResponse(
                detail=str(e),
                status="error",
                links=[],
                timestamp=datetime.utcnow()
            ))
        )

