#!/usr/bin/env python3
import os
import json
from collections import defaultdict, Counter
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.id3 import ID3
import sys

# Current thresholds from tagger.py
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

FALLBACK_OVERRIDES = {
    "love": 0.25, "romantic": 0.25,
    "energetic": 0.20, "fast": 0.15, "action": 0.15, "sport": 0.15, "powerful": 0.15,
    "inspiring": 0.08, "hopeful": 0.08, "motivational": 0.10,
}

MUSIC_FOLDER = sys.argv[1] if len(sys.argv) > 1 else "/Users/alessiolaiso/Downloads/Converted"

def get_tags_from_file(filepath):
    """Extract mood tags from audio file"""
    ext = filepath.lower()

    try:
        if ext.endswith(".m4a") or ext.endswith(".mp4"):
            audio = MP4(filepath)
            grouping = audio.tags.get("\xa9grp", [])
            if grouping:
                tags = [t.strip() for t in grouping[0].split(";")]
                return [t for t in tags if t.startswith("mood_")]
        elif ext.endswith(".flac"):
            audio = FLAC(filepath)
            grouping = audio.get("GROUPING", [])
            return [t for t in grouping if t.startswith("mood_")]
        elif ext.endswith(".mp3"):
            audio = ID3(filepath)
            tit1 = audio.getall("TIT1")
            if tit1:
                tags = [t.strip() for t in tit1[0].text[0].split(";")]
                return [t for t in tags if t.startswith("mood_")]
    except Exception as e:
        pass

    return []

def get_song_title(filepath):
    """Extract song title from audio file"""
    ext = filepath.lower()

    try:
        if ext.endswith(".m4a") or ext.endswith(".mp4"):
            audio = MP4(filepath)
            title = audio.tags.get("\xa9nam", [""])
            artist = audio.tags.get("\xa9ART", [""])
            if title[0] and artist[0]:
                return f"{artist[0]} - {title[0]}"
            elif title[0]:
                return title[0]
        elif ext.endswith(".flac"):
            audio = FLAC(filepath)
            title = audio.get("TITLE", [""])
            artist = audio.get("ARTIST", [""])
            if title[0] and artist[0]:
                return f"{artist[0]} - {title[0]}"
            elif title[0]:
                return title[0]
        elif ext.endswith(".mp3"):
            audio = ID3(filepath)
            title = audio.get("TIT2", None)
            artist = audio.get("TPE1", None)
            if title and artist:
                return f"{artist.text[0]} - {title.text[0]}"
            elif title:
                return title.text[0]
    except Exception:
        pass

    # Fallback to filename
    return os.path.splitext(os.path.basename(filepath))[0]

# Scan all files
print(f"Scanning {MUSIC_FOLDER}...")
tag_counts = Counter()
tag_to_songs = defaultdict(list)
total_files = 0
tagged_files = 0

# Define all expected output tags
all_tags = [
    "mood_happy", "mood_sad", "mood_love", "mood_dark", "mood_emotional",
    "mood_deep", "mood_energetic", "mood_relaxing", "mood_heavy",
    "mood_party", "mood_meditative", "mood_atmospheric", "mood_groovy",
    "mood_summer", "mood_cinematic", "mood_epic", "mood_inspiring", "mood_melodic",
    "mood_ballad"
]

for root, dirs, files in os.walk(MUSIC_FOLDER):
    for file in files:
        if file.lower().endswith(('.mp3', '.flac', '.m4a', '.mp4')):
            total_files += 1
            full_path = os.path.join(root, file)
            tags = get_tags_from_file(full_path)

            if tags:
                tagged_files += 1
                title = get_song_title(full_path)

                for tag in tags:
                    tag_counts[tag] += 1
                    tag_to_songs[tag].append(title)

# Generate report
print(f"\nTotal files processed: {total_files}")
print(f"Files with mood tags: {tagged_files} ({tagged_files/total_files*100:.1f}%)")
print(f"Files without mood tags: {total_files - tagged_files}\n")

print("="*80)
print("TAG DISTRIBUTION & SAMPLE SONGS")
print("="*80)

# Sort by count
sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

for tag, count in sorted_tags:
    percentage = (count / total_files * 100)
    print(f"\n{tag.upper()}")
    print(f"  Count: {count} songs ({percentage:.1f}% of library)")
    print(f"  Sample songs (showing 20):")

    for i, song in enumerate(tag_to_songs[tag][:20], 1):
        print(f"    {i}. {song}")

# Show tags with zero songs
print("\n" + "="*80)
print("TAGS WITH ZERO SONGS")
print("="*80)
for tag in all_tags:
    if tag not in tag_counts:
        print(f"  {tag}")

# Generate statistics for analysis
print("\n" + "="*80)
print("THRESHOLD ANALYSIS")
print("="*80)

# Get reverse mapping of thresholds
tag_thresholds = {}
for raw_tag, (mood_tag, threshold) in TAG_CONFIG.items():
    if mood_tag not in tag_thresholds:
        tag_thresholds[mood_tag] = []
    tag_thresholds[mood_tag].append((raw_tag, threshold))

print("\nCurrent thresholds for each mood tag:")
for mood_tag in sorted(all_tags):
    if mood_tag in tag_thresholds:
        print(f"\n{mood_tag}:")
        for raw_tag, threshold in sorted(tag_thresholds[mood_tag]):
            fallback = FALLBACK_OVERRIDES.get(raw_tag)
            if fallback:
                print(f"  {raw_tag}: {threshold*100:.0f}% (fallback: {fallback*100:.0f}%)")
            else:
                print(f"  {raw_tag}: {threshold*100:.0f}%")

print("\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)
print(f"\nTotal unique tags found: {len(tag_counts)}/{len(all_tags)}")
print(f"Most common tag: {sorted_tags[0][0]} ({sorted_tags[0][1]} songs)")
print(f"Least common tag: {sorted_tags[-1][0]} ({sorted_tags[-1][1]} songs)")

# Calculate distribution metrics
counts = [count for _, count in sorted_tags]
avg_count = sum(counts) / len(counts)
print(f"Average songs per tag: {avg_count:.1f}")
print(f"Median songs per tag: {sorted(counts)[len(counts)//2]}")

# Tag concentration
top_5_percentage = sum([count for _, count in sorted_tags[:5]]) / sum(counts) * 100
print(f"\nTop 5 tags represent {top_5_percentage:.1f}% of all tag assignments")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

# Analyze over/under represented tags
print("\nOVER-REPRESENTED TAGS (may need threshold increase):")
for tag, count in sorted_tags[:5]:
    if count > avg_count * 1.5:
        print(f"  {tag}: {count} songs ({count/avg_count:.1f}x average)")

print("\nUNDER-REPRESENTED TAGS (may need threshold decrease):")
for tag, count in sorted_tags[-5:]:
    if count < avg_count * 0.3:
        print(f"  {tag}: {count} songs ({count/avg_count:.2f}x average)")

# Save full song lists to file
output_file = "/app/mood_analysis_report.md"
with open(output_file, 'w') as f:
    f.write("# Mood Tag Analysis Report\n\n")
    f.write(f"**Total files:** {total_files}\n")
    f.write(f"**Files with mood tags:** {tagged_files} ({tagged_files/total_files*100:.1f}%)\n\n")

    f.write("## Tag Distribution\n\n")
    for tag, count in sorted_tags:
        percentage = (count / total_files * 100)
        f.write(f"### {tag.upper()} - {count} songs ({percentage:.1f}%)\n\n")
        for i, song in enumerate(tag_to_songs[tag][:20], 1):
            f.write(f"{i}. {song}\n")
        f.write("\n")

    f.write("\n## Current Threshold Configuration\n\n")
    for mood_tag in sorted(all_tags):
        if mood_tag in tag_thresholds:
            f.write(f"### {mood_tag}\n")
            for raw_tag, threshold in sorted(tag_thresholds[mood_tag]):
                fallback = FALLBACK_OVERRIDES.get(raw_tag)
                if fallback:
                    f.write(f"- {raw_tag}: {threshold*100:.0f}% (fallback: {fallback*100:.0f}%)\n")
                else:
                    f.write(f"- {raw_tag}: {threshold*100:.0f}%\n")
            f.write("\n")

print(f"\nFull report saved to: {output_file}")
