import os
import shutil
import re
import pytesseract
from PIL import Image

# --- CONFIGURATION ---
SOURCE_DIR = "."                # Root of repo where you upload images
DEST_IMG_DIR = "scanned_images" # Where to move images for storage
OUTPUT_BASE = "class5"          # Base folder for chapters
OCR_LANG = "tel"                # Telugu Language Code

# Chapter Configuration: Folder Name -> { Lesson Ranges, Exercise Ranges, Chapter Number }
CHAPTER_MAPPING = {
    "06_Shataka_Padyalu": {
        "id": 6,
        "lesson": (67, 70), 
        "exercise": (70, 74)
    },
    "07_Sankranthi_Sandesham": {
        "id": 7,
        "lesson": (75, 76), 
        "exercise": (77, 80)
    },
    "08_Kanuvippu": {
        "id": 8,
        "lesson": (81, 84), 
        "exercise": (84, 88)
    },
    "09_Ramappa": {
        "id": 9,
        "lesson": (89, 92), 
        "exercise": (92, 96)
    },
    "10_Shibi_Chakravarti": {
        "id": 10,
        "lesson": (97, 99), 
        "exercise": (100, 104)
    }
}

def move_images():
    """Moves page-090.png etc. from root to scanned_images folder."""
    if not os.path.exists(DEST_IMG_DIR):
        os.makedirs(DEST_IMG_DIR)

    # Regex to match page-090.png, page-90.png, etc.
    file_pattern = re.compile(r"page-\d+\.png")

    for filename in os.listdir(SOURCE_DIR):
        if file_pattern.match(filename):
            src = os.path.join(SOURCE_DIR, filename)
            dst = os.path.join(DEST_IMG_DIR, filename)
            shutil.move(src, dst)
            print(f"   Moved {filename} -> {DEST_IMG_DIR}/")

def get_ocr_text(page_num):
    """Finds image for page_num and returns verbatim Telugu text."""
    # Look for page-090.png or page-90.png
    candidates = [f"page-{page_num:03d}.png", f"page-{page_num}.png"]
    
    img_path = None
    for c in candidates:
        p = os.path.join(DEST_IMG_DIR, c)
        if os.path.exists(p):
            img_path = p
            break
    
    if not img_path:
        return f"\n\n\n\n"

    try:
        # Extract text using Telugu model
        text = pytesseract.image_to_string(Image.open(img_path), lang=OCR_LANG)
        return text
    except Exception as e:
        print(f"   ❌ OCR Error on {img_path}: {e}")
        return ""

def main():
    print("🧹 Step 1: Moving images...")
    move_images()

    print("\n🔍 Step 2: Extracting Telugu Text...")
    for folder, data in CHAPTER_MAPPING.items():
        chapter_id = data['id']
        print(f"   👉 Processing Chapter {chapter_id} ({folder})...")
        
        output_dir = os.path.join(OUTPUT_BASE, folder)
        os.makedirs(output_dir, exist_ok=True)

        # --- PROCESS LESSON ---
        l_start, l_end = data['lesson']
        lesson_content = ""
        for p in range(l_start, l_end + 1):
            lesson_content += get_ocr_text(p) + "\n\n"
        
        # Save as lesson_6.md
        lesson_file = os.path.join(output_dir, f"lesson_{chapter_id}.md")
        with open(lesson_file, "w", encoding="utf-8") as f:
            f.write(lesson_content.strip())
        print(f"      ✅ Created {lesson_file}")

        # --- PROCESS EXERCISE ---
        e_start, e_end = data['exercise']
        exercise_content = ""
        for p in range(e_start, e_end + 1):
            exercise_content += get_ocr_text(p) + "\n\n"

        # Save as exercise_6.md
        exercise_file = os.path.join(output_dir, f"exercise_{chapter_id}.md")
        with open(exercise_file, "w", encoding="utf-8") as f:
            f.write(exercise_content.strip())
        print(f"      ✅ Created {exercise_file}")

if __name__ == "__main__":
    main()
