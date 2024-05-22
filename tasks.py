import os
from celery_setting import celery  # Ensure celery_setting initializes Celery properly
from mert import get_embedding  # Assuming get_embedding is correctly imported
from dotenv import load_dotenv
import multiprocessing
import psycopg2
import psycopg2.extras
import sys
from pgvector.psycopg2 import register_vector
from openai import OpenAI

# Keep-Alive 설정을 위한 파라미터
keepalive_kwargs = {
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5
}


load_dotenv()

hostname: str = os.getenv("HOST")
dbname: str = os.getenv("DBNAME")
port: str = os.getenv("PORT")
user: str = os.getenv("USER")
pwd: str = os.getenv("PASSWORD")


DATABASE_URL = f"postgres://{user}:{pwd}@{hostname}:{port}/{dbname}"


@celery.task
def process_audio(file_path):
    try:
        conn = psycopg2.connect(DATABASE_URL, **keepalive_kwargs)
        register_vector(conn)
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
        import torch
        embedding = get_embedding(file_path)
        # query = "SELECT \"musicName\", \"Singer\", \"Vector\" <=> %s as similarity FROM public.\"MusicRecommend\" ORDER BY similarity DESC LIMIT 6"
        query = "SELECT \"musicName\", \"singer\", \"description\", \"embedding\" <-> %s as similarity FROM public.\"AJTKS_ORIGINAL\" ORDER BY similarity ASC LIMIT 6"
        cur.execute(query, (embedding[0],))
        response = cur.fetchall()
         # GPT-4 API 호출을 위한 입력 데이터 생성
        search_results = [{"musicName": r[0], "singer": r[1], "description": r[2], "similarity": r[3]} for r in response]

        client = OpenAI(api_key='your_api_key')
        desc = [r[2] for r in response]
        gpt4_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
            {"role": "system", "content": ("You are an expert in music recommendation. You have five songs selected to be recommended based on a specific song. Summarize the common features of the given descriptions concisely. Respond with bullet points. Don't mention the specific description. The descriptions are as follows:\n"
                                    f"Description 1: {desc[0]}\n"
                                    f"Description 2: {desc[1]}\n"
                                    f"Description 3: {desc[2]}\n"
                                    f"Description 4: {desc[3]}\n"
                                    f"Description 5: {desc[4]}\n"    
                                )
                }
            ],
            temperature=1.2
        )
        print(gpt4_response.choices[0].message.content)

        recommendation = gpt4_response.choices[0].message.content
        result = {
            "search_results": search_results,
            "recommendation": recommendation
        }

        return result

    except psycopg2.OperationalError as e:
        print(f"Unable to connect {e}")
        sys.exit(1)
    

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')