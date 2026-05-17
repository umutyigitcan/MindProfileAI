import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import psycopg2


load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


client = OpenAI(api_key=get_required_env("LLM_API_KEY"))

backend = FastAPI(
    title="MindProfileAI",
    description="Personality analysis API based on long-form user-written text.",
    version="1.0.0",
)


backend.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "mindprofile"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "mindprofile_db"),
    )


class User(BaseModel):
    name: str
    mail: str
    password: str


class LoginRequest(BaseModel):
    mail: str
    password: str


class AnalyzeText(BaseModel):
    text: str


def count_words(text: str) -> int:
    return len([word for word in text.strip().split() if word])


@backend.get("/")
def home():
    return {"message": "MindProfileAI API is running."}


@backend.post("/add_user")
def add_user(user: User):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (name, mail, password)
            VALUES (%s, %s, %s)
            RETURNING id, name, mail
            """,
            (user.name, user.mail, user.password),
        )

        user_data = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        return {
            "status": "User created successfully",
            "id": user_data[0],
            "name": user_data[1],
            "mail": user_data[2],
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@backend.get("/users")
def get_users():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, mail FROM users")
        users = cur.fetchall()

        cur.close()
        conn.close()

        return {"users": users}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@backend.post("/login")
def login_user(login: LoginRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, name, mail
            FROM users
            WHERE mail = %s AND password = %s
            """,
            (login.mail, login.password),
        )

        user_data = cur.fetchone()

        cur.close()
        conn.close()

        if user_data is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return {
            "status": "Login successful",
            "id": user_data[0],
            "name": user_data[1],
            "mail": user_data[2],
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@backend.post("/analyze")
def analyze_text(payload: AnalyzeText):
    word_count = count_words(payload.text)

    if word_count < 300 or word_count > 1000:
        raise HTTPException(
            status_code=400,
            detail=f"Text length must be between 300 and 1000 words. Current length: {word_count} words.",
        )

    try:
        completion = client.chat.completions.create(
            temperature=0.2,
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert personality analyst for a writing-based personality analysis API. "
                        "The user writes 300 to 1000 words of free text in any language. "
                        "Analyze the writing style, emotional tone, priorities, communication pattern, and self-expression. "
                        "Return only a valid JSON object with this exact structure: "
                        "{"
                        "\"summary\": string,"
                        "\"mbti\": {\"type\": string, \"confidence\": string, \"reasons\": [string]},"
                        "\"enneagram\": {\"type\": string, \"confidence\": string, \"reasons\": [string]},"
                        "\"personality_traits\": [string],"
                        "\"communication_insights\": {\"style\": string, \"tips_for_others\": [string]},"
                        "\"lifestyle_suggestions\": [string],"
                        "\"fashion_suggestions\": [string],"
                        "\"jewelry_suggestions\": [string]"
                        "}. "
                        "Do not include markdown. Do not include extra commentary. "
                        "Respond in the same language as the user's text when possible."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze this user-written text:\n\n{payload.text}",
                },
            ],
        )

        content = completion.choices[0].message.content

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
