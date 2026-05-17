# MindProfileAI

MindProfileAI is a FastAPI-based personality analysis API that analyzes long-form user-written text and returns a structured personality profile.

The system processes a text sample and generates JSON output including an MBTI-like profile, Enneagram-inspired style, personality traits, communication insights, lifestyle suggestions, fashion recommendations, and jewelry style ideas.

## Features

- User registration endpoint
- User login endpoint
- PostgreSQL database integration
- Text length validation for analysis input
- Personality analysis from 300-1000 word text samples
- Structured JSON response format
- MBTI-like personality type inference
- Enneagram-inspired profile inference
- Communication and lifestyle insights
- Fashion and jewelry recommendation output
- FastAPI-based REST API architecture

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- psycopg2
- Pydantic
- python-dotenv
- OpenAI SDK

## Project Structure

```text
MindProfileAI/
├── main.py
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md