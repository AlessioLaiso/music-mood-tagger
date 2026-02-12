import os
import json
import numpy as np
import subprocess
import mutagen
from mutagen.id3 import ID3, TIT1, ID3NoHeaderError
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from essentia.standard import TensorflowPredictEffnetDiscogs, TensorflowPredict2D

# --- CONFIGURATION ---
MUSIC_FOLDER = "/music"
EMBEDDING_MODEL_FILE = "/app/discogs-effnet-bs64-1.pb"
CLASSIFIER_MODEL_FILE = "/app/mtg_jamendo_moodtheme-discogs-effnet-1.pb"
META_FILE = "/app/mtg_jamendo_moodtheme-discogs-effnet-1.json"

# Settings
FALLBACK_THRESHOLD = 0.06  # Minimum for fallback (base threshold)
MAX_TAGS = 5

# Tag-specific fallback overrides (when no tags pass first pass)
FALLBACK_OVERRIDES = {
    "love": 0.25, "romantic": 0.25,
    "energetic": 0.20, "fast": 0.15, "action": 0.15, "sport": 0.15, "powerful": 0.15,
    "inspiring": 0.08, "hopeful": 0.08, "motivational": 0.10,
}
CHUNK_DURATION = 30

# --- TAG CONFIGURATION ---
# Format: "raw_model_tag": ("final_display_tag", threshold)

TAG_CONFIG = {
    "happy":        ("mood_happy", 0.15),
    "positive":     ("mood_happy", 0.15),
    "upbeat":       ("mood_happy", 0.15),
    "uplifting":    ("mood_happy", 0.15),
    "fun":          ("mood_happy", 0.15),
    "sad":          ("mood_sad", 0.10),
    "melancholic":  ("mood_sad", 0.08),
    "love":         ("mood_love", 0.30),
    "romantic":     ("mood_love", 0.25),
    "dark":         ("mood_dark", 0.10),
    "emotional":    ("mood_emotional", 0.10),
    "hopeful":      ("mood_inspiring", 0.08),
    "motivational": ("mood_inspiring", 0.10),
    "deep":         ("mood_deep", 0.15),
    "energetic":    ("mood_energetic", 0.35),
    "fast":         ("mood_energetic", 0.30),
    "action":       ("mood_energetic", 0.25),
    "sport":        ("mood_energetic", 0.25),
    "powerful":     ("mood_energetic", 0.25),
    "relaxing":     ("mood_relaxing", 0.10),
    "calm":         ("mood_relaxing", 0.08),
    "soft":         ("mood_relaxing", 0.08),
    "slow":         ("mood_relaxing", 0.08),
    "heavy":        ("mood_heavy", 0.12),
    "party":        ("mood_party", 0.06),
    "meditative":   ("mood_meditative", 0.08),
    "background":   ("mood_atmospheric", 0.12),
    "soundscape":   ("mood_atmospheric", 0.10),
    "space":        ("mood_atmospheric", 0.08),
    "dream":        ("mood_atmospheric", 0.08),
    "groovy":       ("mood_groovy", 0.04),
    "cool":         ("mood_groovy", 0.04),
    "summer":       ("mood_summer", 0.10),
    "film":         ("mood_cinematic", 0.10),
    "movie":        ("mood_cinematic", 0.10),
    "trailer":      ("mood_cinematic", 0.10),
    "documentary":  ("mood_cinematic", 0.10),
    "drama":        ("mood_cinematic", 0.10),
    "dramatic":     ("mood_cinematic", 0.10),
    "adventure":    ("mood_cinematic", 0.10),
    "epic":         ("mood_epic", 0.10),
    "inspiring":    ("mood_inspiring", 0.10),
    "travel":       ("mood_inspiring", 0.08),
    "melodic":      ("mood_melodic", 0.15),
    "ballad":       ("mood_ballad", 0.15),
}

# --- IGNORED TAGS (never written) ---
IGNORED_TAGS = {"corporate", "advertising", "commercial", "children", "game", "christmas", "holiday", "nature", "funny", "retro", "sexy"}

def read_middle_chunk(file_path):
    try:
        probe = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try: duration = float(probe.stdout)
        except ValueError: duration = 60

        start_time = max(0, (duration / 2) - (CHUNK_DURATION / 2))

        command = [
            'ffmpeg', '-ss', str(start_time), '-t', str(CHUNK_DURATION),
            '-i', file_path, '-f', 'f32le', '-ac', '1', '-ar', '16000',
            '-loglevel', 'quiet', 'pipe:1'
        ]

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if process.returncode != 0: return None
        return np.frombuffer(process.stdout, dtype=np.float32)
    except Exception:
        return None

def get_ai_tags(file_path, embedding_model, classifier_model, classes):
    audio = read_middle_chunk(file_path)
    if audio is None or len(audio) < 16000: return []

    try:
        embeddings = embedding_model(audio)
        avg_embeddings = np.mean(embeddings, axis=0, keepdims=True)
        predictions = classifier_model(avg_embeddings)
        avg_predictions = predictions[0]

        indices = np.argsort(avg_predictions)[::-1]

        final_tags = []
        debug_output = []
        fallback_candidate = None

        for i in indices:
            if len(final_tags) >= MAX_TAGS: break

            score = avg_predictions[i]
            raw_tag = classes[i]

            # Skip ignored tags
            if raw_tag in IGNORED_TAGS:
                continue

            # Skip tags not in the config
            if raw_tag not in TAG_CONFIG:
                continue

            display_tag, threshold = TAG_CONFIG[raw_tag]

            # Track best fallback candidate with tag-specific thresholds
            if fallback_candidate is None and score >= FALLBACK_THRESHOLD:
                min_fallback = FALLBACK_OVERRIDES.get(raw_tag, FALLBACK_THRESHOLD)
                if score >= min_fallback:
                    fallback_candidate = (raw_tag, display_tag, score)

            if score < threshold:
                continue

            if display_tag not in final_tags:
                final_tags.append(display_tag)
                debug_output.append(f"{raw_tag} ({score*100:.1f}%)")

        # Fallback: if no tags found, use best candidate
        if not final_tags and fallback_candidate:
            raw_tag, display_tag, score = fallback_candidate
            final_tags.append(display_tag)
            debug_output.append(f"{raw_tag} ({score*100:.1f}%)*")

        if final_tags:
            print(f"   {os.path.basename(file_path)}: {', '.join(debug_output)}")
        else:
            print(f"   {os.path.basename(file_path)}: (No mood tags above threshold)")

        return final_tags

    except Exception as e:
        print(f"   Error: {os.path.basename(file_path)} - {e}")
        return []

def append_tags_to_file(path, new_tags):
    if not new_tags: return

    try:
        updated = False
        filename = os.path.basename(path)
        ext = path.lower()

        # --- MP3 ---
        if ext.endswith(".mp3"):
            try: audio = ID3(path)
            except ID3NoHeaderError: audio = ID3()
            current_tags = []
            existing_frames = audio.getall("TIT1")
            if existing_frames:
                current_tags = [t.strip() for t in existing_frames[0].text[0].split(";")]
            # Remove old mood_* tags but keep other tags
            current_tags = [t for t in current_tags if not t.startswith("mood_")]
            # Add new mood tags
            for tag in new_tags:
                if tag not in current_tags:
                    current_tags.append(tag)
                    updated = True
            if updated or existing_frames:  # Update if changed or had mood tags before
                final_str = "; ".join(current_tags)
                audio["TIT1"] = TIT1(encoding=3, text=final_str)
                audio.save(path)
                print(f"   Saved MP3: {final_str}")

        # --- FLAC ---
        elif ext.endswith(".flac"):
            audio = FLAC(path)
            current_tags = audio.get("GROUPING", [])
            # Remove old mood_* tags but keep other tags
            current_tags = [t for t in current_tags if not t.startswith("mood_")]
            # Add new mood tags
            for tag in new_tags:
                if tag not in current_tags:
                    current_tags.append(tag)
                    updated = True
            if updated or audio.get("GROUPING"):  # Update if changed or had tags before
                audio["GROUPING"] = current_tags
                audio.save()
                print(f"   Saved FLAC: {new_tags}")

        # --- M4A / MP4 ---
        elif ext.endswith((".m4a", ".mp4")):
            try:
                audio = MP4(path)
                current_tags = []
                current_raw = audio.tags.get("\xa9grp", [])
                if current_raw:
                    current_tags = [t.strip() for t in current_raw[0].split(";")]
                # Remove old mood_* tags but keep other tags
                current_tags = [t for t in current_tags if not t.startswith("mood_")]
                # Add new mood tags
                for tag in new_tags:
                    if tag not in current_tags:
                        current_tags.append(tag)
                        updated = True
                if updated or current_raw:  # Update if changed or had tags before
                    final_str = "; ".join(current_tags)
                    audio.tags["\xa9grp"] = [final_str]
                    audio.save()
                    print(f"   Saved M4A: {final_str}")
            except Exception as e:
                print(f"   M4A Error: {e}")

    except Exception as e:
        print(f"   Write Error: {e}")

# --- MAIN ---
if __name__ == "__main__":
    print("--- Music Mood Tagger ---")

    if not os.path.exists(MUSIC_FOLDER):
        print(f"Error: Music folder not found: {MUSIC_FOLDER}")
        exit(1)
    if not os.path.exists(EMBEDDING_MODEL_FILE):
        print(f"Error: Embedding model not found: {EMBEDDING_MODEL_FILE}")
        exit(1)
    if not os.path.exists(CLASSIFIER_MODEL_FILE):
        print(f"Error: Classifier model not found: {CLASSIFIER_MODEL_FILE}")
        exit(1)

    with open(META_FILE, 'r') as f:
        classes = json.load(f)['classes']

    # Count unique output tags
    unique_outputs = set(v[0] for v in TAG_CONFIG.values())
    print(f"Model classes: {len(classes)} | Mapped to: {len(unique_outputs)} output tags")
    print(f"Fallback threshold: {FALLBACK_THRESHOLD*100:.0f}% (love: 15%) | Max tags: {MAX_TAGS}")
    print(f"Ignored tags: {', '.join(sorted(IGNORED_TAGS))}")

    print("Loading embedding model (discogs-effnet)...")
    embedding_model = TensorflowPredictEffnetDiscogs(
        graphFilename=EMBEDDING_MODEL_FILE,
        output="PartitionedCall:1"
    )

    print("Loading classifier model (mtg-jamendo-moodtheme)...")
    classifier_model = TensorflowPredict2D(graphFilename=CLASSIFIER_MODEL_FILE)

    print(f"Scanning {MUSIC_FOLDER}...")
    file_count = 0
    tagged_count = 0

    for root, dirs, files in os.walk(MUSIC_FOLDER):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.mp4')):
                file_count += 1
                full_path = os.path.join(root, file)
                tags = get_ai_tags(full_path, embedding_model, classifier_model, classes)
                if tags:
                    tagged_count += 1
                    append_tags_to_file(full_path, tags)

    print(f"Done! Processed {file_count} files, tagged {tagged_count}.")
