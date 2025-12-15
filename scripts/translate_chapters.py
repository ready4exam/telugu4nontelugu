import os
import json
import time
import google.generativeai as genai
from google.api_core import exceptions

# ============================================================================
#  MODEL DISCOVERY
# ============================================================================

# 1. Setup & Key Verification
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ CRITICAL: GEMINI_API_KEY is missing from environment variables!")

# Mask key for logs (safety)
print(f"🔑 API Key loaded (starts with: {API_KEY[:4]}...)")

genai.configure(api_key=API_KEY)

def get_working_model():
    """Finds a usable model that supports content generation."""
    print("🔄 Finding a working model that supports 'generateContent'...")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"   ✅ Found a working model: {model.name}")
            return model.name
    raise ValueError("❌ CRITICAL: Could not find a model that supports content generation.")

# Initialize the working model
try:
    ACTIVE_MODEL_NAME = get_working_model()
except Exception as e:
    print(f"🔥 FATAL ERROR: {e}")
    exit(1)

def get_lesson_prompt(chapter):
    return f"""
    You are a Telugu teacher creating a JSON study guide for a Class 5 student.
    Analyze the lesson content on pages {chapter['start_page']} to {chapter['end_page']} of the provided PDF.
    The chapter topic is: **{chapter['topic']}**.

    **YOUR TASK:**
    - Act as a teacher. **Do not copy the text verbatim.** Explain and rephrase the content to avoid copyright issues.
    - Summarize the story, explain the key lines, and define important vocabulary words.
    - Output a single, valid JSON object with the following structure:
    {{
      "chapter_summary": "A simple, one-paragraph summary of the story or poem in English.",
      "reading_content": [
        {{
          "telugu": "Original Telugu text line.",
          "pronunciation": "Simple English phonetics.",
          "meaning": "A teacher-like explanation of the line's meaning."
        }}
      ],
      "vocabulary": [
        {{
          "telugu_word": "Key Telugu word.",
          "pronunciation": "Simple English phonetics.",
          "meaning": "English meaning of the word."
        }}
      ]
    }}
    """

def get_exercise_prompt(chapter):
    return f"""
    You are an AI assistant creating a JSON homework guide for a Class 5 student.
    Analyze the exercises on pages {chapter['start_page']} to {chapter['end_page']} of the provided PDF.
    The chapter topic is: **{chapter['topic']}**.

    **YOUR TASK:**
    - Find all the questions on the specified pages.
    - Provide the question, its pronunciation, its meaning, and the correct answer with its pronunciation.
    - Output a single, valid JSON object with the following structure:
    {{
      "exercises": [
        {{
          "question_telugu": "The original question in Telugu.",
          "question_pronunciation": "Simple English phonetics of the question.",
          "question_meaning": "English meaning of the question.",
          "answer_telugu": "The answer in Telugu script (for writing).",
          "answer_pronunciation": "Simple English phonetics of the answer (for speaking)."
        }}
      ]
    }}
    """

def generate_data(pdf_file, chapter, prompt_func):
    model = genai.GenerativeModel(model_name=ACTIVE_MODEL_NAME)
    prompt = prompt_func(chapter)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([pdf_file, prompt])
            # Find the start and end of the JSON block
            start_index = response.text.find('{')
            end_index = response.text.rfind('}')
            if start_index == -1 or end_index == -1:
                raise json.JSONDecodeError("Could not find JSON object in response.", "", 0)

            json_response = response.text[start_index:end_index+1]
            # Fix for invalid escape sequences
            json_response = json_response.replace('\\', '\\\\')
            return json.loads(json_response)
        except (exceptions.ResourceExhausted, exceptions.InternalServerError) as e:
            print(f"   ⚠️ Retrying due to server error: {e}. Sleeping 20s...")
            time.sleep(20)
        except Exception as e:
            print(f"   ⚠️ Error during generation: {e}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(5)
    return None

def main():
    config_path = 'class5/chapters.json'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    pdf_path = config.get('pdf_path')
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at path: {pdf_path}")

    print(f"📂 Uploading PDF: {pdf_path}...")
    pdf_file = genai.upload_file(path=pdf_path)
    
    print("⏳ Waiting for PDF processing...")
    while pdf_file.state.name == "PROCESSING":
        time.sleep(2)
        pdf_file = genai.get_file(pdf_file.name)
    
    if pdf_file.state.name == "FAILED":
        raise ValueError("PDF processing failed by Google API.")

    print(f"🚀 Processing with model: {ACTIVE_MODEL_NAME}")

    for chapter in config['chapters']:
        base_path = f"class5/{chapter['folder']}"
        os.makedirs(base_path, exist_ok=True)

        try:
            # Stage 1: Generate Lesson Data
            print(f"   📚 Generating lesson for {chapter['folder']}...", end=" ")
            lesson_data = generate_data(pdf_file, chapter, get_lesson_prompt)
            if not lesson_data:
                print("❌ Failed.")
                continue

            with open("scripts/lesson_template.html", "r", encoding="utf-8") as f:
                lesson_template = f.read()

            reading_html = "".join([f"<tr><td>{item.get('telugu', '')}</td><td>{item.get('pronunciation', '')}</td><td>{item.get('meaning', '')}</td></tr>" for item in lesson_data.get("reading_content", [])])
            vocab_html = "".join([f"<tr><td>{item.get('telugu_word', '')}</td><td>{item.get('pronunciation', '')}</td><td>{item.get('meaning', '')}</td></tr>" for item in lesson_data.get("vocabulary", [])])

            lesson_html = lesson_template.replace("{{CHAPTER_TOPIC}}", chapter.get('topic', ''))
            lesson_html = lesson_html.replace("{{CHAPTER_SUMMARY}}", lesson_data.get("chapter_summary", "Not available."))
            lesson_html = lesson_html.replace("{{READING_CONTENT}}", reading_html)
            lesson_html = lesson_html.replace("{{VOCABULARY_CONTENT}}", vocab_html)

            with open(f"{base_path}/lesson.html", "w", encoding="utf-8") as f:
                f.write(lesson_html)
            print("✅ Done.")

            # Stage 2: Generate Exercise Data
            print(f"   ✍️ Generating exercises for {chapter['folder']}...", end=" ")
            exercise_data = generate_data(pdf_file, chapter, get_exercise_prompt)
            if not exercise_data:
                print("❌ Failed.")
                continue

            with open("scripts/exercise_template.html", "r", encoding="utf-8") as f:
                exercise_template = f.read()

            exercise_html_content = ""
            for item in exercise_data.get("exercises", []):
                exercise_html_content += f"""
                <div class="exercise-card">
                    <div class="question">Q: {item.get('question_telugu', 'N/A')}</div>
                    <p><strong>Pronunciation:</strong> {item.get('question_pronunciation', 'N/A')}</p>
                    <p><strong>Meaning:</strong> {item.get('question_meaning', 'N/A')}</p>
                    <div class="answer">
                        <strong>Answer (Telugu):</strong> {item.get('answer_telugu', 'N/A')}<br>
                        <strong>Answer (Pronunciation):</strong> {item.get('answer_pronunciation', 'N/A')}
                    </div>
                </div>
                """

            exercise_html = exercise_template.replace("{{CHAPTER_TOPIC}}", chapter.get('topic', ''))
            exercise_html = exercise_html.replace("{{EXERCISE_CONTENT}}", exercise_html_content)

            with open(f"{base_path}/exercise.html", "w", encoding="utf-8") as f:
                f.write(exercise_html)
            print("✅ Done.")
            print("   😴 Sleeping for 60 seconds to respect API rate limits...")
            time.sleep(60)

        except Exception as e:
            print(f"❌ An unexpected error occurred for chapter {chapter['folder']}: {e}")

if __name__ == "__main__":
    main()
