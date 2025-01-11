# Import necessary modules
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import redis
import os
from twilio.rest import Client
from groq import Groq
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set up environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Twilio, Redis, and Supabase
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Initialize Groq LLM
llm_client = Groq()

# FastAPI app
app = FastAPI()

# Pydantic model for user input
class ScamReportRequest(BaseModel):
    whatsapp_number: str
    message: str

# Helper function to query database for scam reports
def query_db_for_scam(phone_number: str):
    response = supabase_client.table("phone_numbers").select("*").eq("phone_number", phone_number).execute()
    return response.data

# Helper function to insert new scam report
def insert_new_scam_report(user_id: str, phone_number_id: str, scam_type_id: str, description: str, source: str):
    supabase_client.table("scam_reports").insert({
        "report_id": str(uuid4()),
        "user_id": user_id,
        "phone_number_id": phone_number_id,
        "description": description,
        "report_source": source,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

# Helper function to manage Redis sessions
def get_user_session(user_number: str):
    session_data = redis_client.get(user_number)
    return json.loads(session_data) if session_data else {}

def set_user_session(user_number: str, session_data: dict):
    redis_client.setex(user_number, 3600, json.dumps(session_data))  # Expire after 1 hour

# Helper function to send Twilio message
def send_whatsapp_message(user_number: str, message: str):
    client.messages.create(
        from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        body=message,
        to=f"whatsapp:{user_number}"
    )

@app.post("/report-scam")
async def report_scam(request: ScamReportRequest):
    try:
        user_input = request.message
        user_number = request.whatsapp_number

        # Maintain session context for multi-turn conversations using Redis
        user_session = get_user_session(user_number)
        previous_context = user_session.get("context", "")

        llm_prompt = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful agent named DAPA to classify user reports about potential digital financial scams or fraud."},
                {"role": "user", "content": f"Previous context: {previous_context}\nUser message: {user_input}" if previous_context else f"{user_input}"}
            ],
            "temperature": 0.41,
            "max_tokens": 1024,
            "top_p": 0.41,
            "stream": False
        }

        # Send input to Groq LLM for processing
        llm_output = llm_client.chat.completions.create(**llm_prompt)

        # Validate LLM response is JSON with retry logic
        try:
            response = json.loads(llm_output["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, KeyError):
            # Regenerate response with context to indicate the previous response failed
            retry_prompt = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful agent named DAPA to classify user reports about potential digital financial scams or fraud."},
                    {"role": "user", "content": f"Your previous response failed to parse as JSON. The context was: {previous_context}. Please regenerate the last response in valid JSON format without additional text."}
                ],
                "temperature": 0.41,
                "max_tokens": 1024,
                "top_p": 0.41,
                "stream": False
            }
            retry_output = llm_client.chat.completions.create(**retry_prompt)
            try:
                response = json.loads(retry_output["choices"][0]["message"]["content"])
            except (json.JSONDecodeError, KeyError):
                raise HTTPException(status_code=400, detail="LLM response is not in valid JSON format after retry")

        # Extract data from LLM response
        for_system = response.get("for_system", {})

        # Perform operations based on LLM instructions
        if for_system.get("query_db_scam_check"):
            phone_number = for_system.get("number")
            existing_reports = query_db_for_scam(phone_number)
            message_to_send = f"Yes, the number {phone_number} has been reported as a scam." if existing_reports else f"No, the number {phone_number} has not been reported as a scam."
            llm_followup_prompt = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "Inform the user about the scam check results in JSON format."},
                    {"role": "user", "content": f"{message_to_send}"}
                ]
            }
            followup_output = llm_client.chat.completions.create(**llm_followup_prompt)
            send_whatsapp_message(user_number, followup_output["choices"][0]["message"]["content"])
            return {"detail": "Response sent via WhatsApp."}

        if for_system.get("insert_report"):
            phone_number = for_system.get("number")
            scam_type = for_system.get("scam_type")
            report_summary = for_system.get("report")

            # Retrieve or create phone_number_id
            phone_number_response = supabase_client.table("phone_numbers").select("phone_number_id").eq("phone_number", phone_number).execute()
            if not phone_number_response.data:
                phone_number_id = str(uuid4())
                supabase_client.table("phone_numbers").insert({
                    "phone_number_id": phone_number_id,
                    "phone_number": phone_number,
                    "country_code": phone_number.split("-")[0],
                    "first_reported_at": datetime.utcnow().isoformat(),
                    "is_verified_scam": False
                }).execute()
            else:
                phone_number_id = phone_number_response.data[0]["phone_number_id"]

            # Retrieve scam type ID
            scam_type_response = supabase_client.table("scam_types").select("scam_type_id").eq("name", scam_type).execute()
            scam_type_id = scam_type_response.data[0]["scam_type_id"] if scam_type_response.data else None

            # Retrieve or create user_id
            user_response = supabase_client.table("users").select("user_id").eq("whatsapp_number", user_number).execute()
            user_id = user_response.data[0]["user_id"] if user_response.data else str(uuid4())
            if not user_response.data:
                supabase_client.table("users").insert({
                    "user_id": user_id,
                    "whatsapp_number": user_number,
                    "last_reported_at": datetime.utcnow().isoformat()
                }).execute()

            # Insert scam report if IDs are valid
            if scam_type_id:
                insert_new_scam_report(user_id, phone_number_id, scam_type_id, report_summary, "WhatsApp")
                user_session["context"] = f"Reported {scam_type} for {phone_number}"
                set_user_session(user_number, user_session)
                send_whatsapp_message(user_number, "Your report has been saved. Thank you!")
                return {"detail": "Report saved and response sent via WhatsApp."}

        # Update context for next message
        user_session["context"] = user_input
        set_user_session(user_number, user_session)

        return {"detail": "Context updated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Confirmation endpoint to handle user replies
@app.post("/confirm-report")
async def confirm_report(request: ScamReportRequest):
    try:
        user_response = request.message.lower().strip()
        user_number = request.whatsapp_number

        user_session = get_user_session(user_number)
        context = user_session.get("context")

        if context:
            llm_confirmation_prompt = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are confirming a report with the user."},
                    {"role": "user", "content": f"User response: {user_response}. Context: {context}. Generate an appropriate confirmation message in JSON format."}
                ]
            }
            confirmation_output = llm_client.chat.completions.create(**llm_confirmation_prompt)
            send_whatsapp_message(user_number, confirmation_output["choices"][0]["message"]["content"])
            return {"detail": "Confirmation response sent via WhatsApp."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
