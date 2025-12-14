import os
import json
import time
import google.generativeai as genai

# 1. Setup
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def translate_chapter(pdf_file, chapter):
    # Model Setup (Using Flash for speed and long context)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    prompt = f"""
    Analyze pages {chapter['start_page']} to {chapter['end_page']} of the provided PDF.
    This is chapter: {chapter['topic']}.

    **TASK 1: TRANSLATION (Story/Poem)**
    Extract the main story or poem. Ignore headers/footers.
    Output a Markdown table: | Telugu | Pronunciation | Meaning |

    **TASK 2: SEPARATOR**
    Output exactly this string on a new line: <<<SPLIT_HERE>>>

    **TASK 3: EXERCISES**
    Solve the exercises found in these pages.
    Format:
    #### Q: [Telugu Text]
    * **Pronunciation:** ...
    * **Meaning:** ...
    * **Answer:** [Telugu Answer]
    """

    # Generate content using the uploaded PDF file reference
    response = model.generate_content([pdf_file, prompt])
    return response.text

def main():
    # Load Config
    with open('class5/chapters.json', 'r') as f:
        config = json.load(f)

    # Upload PDF once (It caches for 48 hours)
    print(f"Uploading {config['pdf_path']}...")
    pdf_file = genai.upload_file(path=config['pdf_path'])
    
    # Wait for processing
    while pdf_file.state.name == "PROCESSING":
        print("Processing PDF...")
        time.sleep(2)
        pdf_file = genai.get_file(pdf_file.name)

    # Process Chapters
    for chapter in config['chapters']:
        print(f"Translating {chapter['folder']}...")
        
        try:
            full_response = translate_chapter(pdf_file, chapter)
            
            # Parsing the output
            if "<<<SPLIT_HERE>>>" in full_response:
                translation_part, exercise_part = full_response.split("<<<SPLIT_HERE>>>")
            else:
                translation_part = full_response
                exercise_part = "Exercises could not be parsed automatically."

            # Define paths
            base_path = f"class5/{chapter['folder']}"
            os.makedirs(base_path, exist_ok=True)

            # Write Translation MD
            with open(f"{base_path}/translation.md", "w", encoding="utf-8") as f:
                f.write(f"# 📖 {chapter['topic']}\n\n")
                f.write(translation_part.strip())

            # Write Exercise MD
            with open(f"{base_path}/exercise.md", "w", encoding="utf-8") as f:
                f.write(f"# ✍️ {chapter['topic']} - Exercises\n\n")
                f.write(exercise_part.strip())
                
            print(f"✅ Completed {chapter['folder']}")
            
            # Sleep to avoid rate limits
            time.sleep(5) 

        except Exception as e:
            print(f"❌ Error in {chapter['folder']}: {e}")

if __name__ == "__main__":
    main()
