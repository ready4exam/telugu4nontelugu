import os
import re

# --- CONFIGURATION ---
# Folder where you upload the raw page text files (e.g., 67.txt, 68.txt)
INPUT_DIR = "ocr_files"
BASE_OUTPUT_DIR = "class5"

# Map provided by you: Folder Name -> { Lesson Ranges, Exercise Ranges }
# Format: [Start_Page, End_Page] (Inclusive)
CHAPTER_MAPPING = {
    "06_Shataka_Padyalu": {
        "lesson": [67, 70],
        "exercise": [70, 74]
    },
    "07_Sankranthi_Sandesham": {
        "lesson": [75, 76],
        "exercise": [77, 80]
    },
    "08_Kanuvippu": {
        "lesson": [81, 84],
        "exercise": [84, 88]
    },
    "09_Ramappa": {
        "lesson": [89, 92],
        "exercise": [92, 96]
    },
    "10_Shibi_Chakravarti": {
        "lesson": [97, 99],
        "exercise": [100, 104]
    }
}

def get_file_content(page_num):
    """
    Tries to find a file named '67.txt' or 'page_67.txt' in the input folder.
    """
    # List all files to find a match
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: Input folder '{INPUT_DIR}' does not exist.")
        return ""

    files = os.listdir(INPUT_DIR)
    
    # Regex to match the page number in filename (e.g., "67.txt" or "page-67.txt")
    # It looks for the number 67 surrounded by non-digits or start/end of string.
    pattern = re.compile(f"(^|[^0-9]){page_num}([^0-9]|$)")

    matched_content = ""
    found = False
    
    for filename in files:
        if pattern.search(filename):
            path = os.path.join(INPUT_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    matched_content = f.read()
                    print(f"   found page {page_num} -> {filename}")
                    found = True
                    break
            except Exception as e:
                print(f"   ⚠️ Error reading {filename}: {e}")

    if not found:
        print(f"   ⚠️ Warning: No file found for page {page_num}")
        
    return matched_content

def main():
    print("🚀 Starting OCR Organization...")

    for folder, ranges in CHAPTER_MAPPING.items():
        print(f"\n📂 Processing: {folder}")
        
        output_folder_path = os.path.join(BASE_OUTPUT_DIR, folder)
        os.makedirs(output_folder_path, exist_ok=True)

        # --- PROCESS LESSON ---
        lesson_start, lesson_end = ranges["lesson"]
        print(f"   📖 Lesson Pages: {lesson_start}-{lesson_end}")
        
        full_lesson_text = f"# 📖 Lesson Content ({lesson_start}-{lesson_end})\n\n"
        for page in range(lesson_start, lesson_end + 1):
            text = get_file_content(page)
            full_lesson_text += f"\n\n--- Page {page} ---\n\n" + text
        
        with open(os.path.join(output_folder_path, "lesson.md"), "w", encoding="utf-8") as f:
            f.write(full_lesson_text)

        # --- PROCESS EXERCISE ---
        ex_start, ex_end = ranges["exercise"]
        print(f"   ✍️ Exercise Pages: {ex_start}-{ex_end}")
        
        full_exercise_text = f"# ✍️ Exercises ({ex_start}-{ex_end})\n\n"
        for page in range(ex_start, ex_end + 1):
            text = get_file_content(page)
            full_exercise_text += f"\n\n--- Page {page} ---\n\n" + text
            
        with open(os.path.join(output_folder_path, "exercise.md"), "w", encoding="utf-8") as f:
            f.write(full_exercise_text)

    print("\n✅ All operations completed.")

if __name__ == "__main__":
    main()
