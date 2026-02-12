# Music Mood Tagger

A tool to automatically tag your music library with mood metadata. It analyzes your audio files and adds mood tags like "mood_energetic", "mood_relaxing", "mood_happy", etc. to the files, in the grouping tag.

## How it works

The tagger uses the **MTG-Jamendo mood/theme dataset** trained on top of **Discogs-Effnet embeddings**. It analyzes a 30-second chunk from the middle of each track and applies mood tags based on the audio content. If the grouping tag of your files already has content other than "mood_value" tags, the content will be kept and the mood tags will be appended.

Music players like [Tunetuna](https://github.com/AlessioLaiso/tunetuna) can use this metadata to filter songs and create mood-based playlists.

### Threshold and rebalancing

The thresholds from the model were rebalanced to:
- Reduce over-represented tags (e.g., love, energetic) so they're more meaningful when they appear
- Lower thresholds for useful but rare tags (e.g., atmospheric, party, meditative)
- Merge similar tags to keep the total count manageable (consolidated to 19 final output tags)
- If no tag reached the respective threshold on first pass, lower thresholds are considered for a second pass. To reduce false positives, no tags will be applied to a file if the thresholds are still not reached after the second pass. Tags applied on the second pass will be shown with an asterisk in the console.

## Running Music Mood Tagger

### 1. Edit `docker-compose.yml`

Change the music folder path to point to your library:

```yaml
volumes:
  - /path/to/your/music:/music  # ← Change this line, keeping ':/music' at the end
  - .:/app
```

### 2. Run the tagger

```bash
docker compose run tagger
```

The script will go through your music folder and tag the audio files it finds (mp3, flac, m4a, mp4).

## Analysis script

An optional analysis scripts is included:

**`comprehensive_analysis.py`** - Run this on your *already tagged* library to see distribution stats. Shows which tags are over/under-represented and suggests threshold adjustments. Useful if you want to tune the thresholds for your specific collection.

```bash
docker compose run tagger python comprehensive_analysis.py /music
```

## Supported formats

- MP3 (uses `TIT1` / Content Group tag)
- FLAC (uses `GROUPING` tag)
- M4A / MP4 (uses `©grp` atom)

## Tags

19 mood tags total can be applied to the songs. The list below shows which raw tags get merged into which output tags, when applicable:

**atmospheric** ← background, soundscape, space, dream
**ballad**
**cinematic** ← film, movie, trailer, documentary, drama, dramatic, adventure
**dark**
**deep**
**emotional**
**energetic** ← fast, action, sport, powerful
**epic**
**groovy** ← cool
**happy** ← positive, upbeat, uplifting, fun
**heavy**
**inspiring** ← hopeful, motivational, travel
**love** ← romantic
**meditative**
**melodic**
**party**
**relaxing** ← calm, soft, slow
**sad** ← melancholic
**summer**

Some tags detected by the model are ignored, either because they are less useful to a general music library, or because the model showed poor tagging performance for them and applied them unreliably: advertising, children, christmas, commercial, corporate, funny, game, holiday, nature, retro, sexy.

## License

The source code in this repository is licensed under GPL-3.0 license.

The pre-trained model files are copyright Music Technology Group,
Universitat Pompeu Fabra, and are licensed under
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/):

- `discogs-effnet-bs64-1.pb`
- `mtg_jamendo_moodtheme-discogs-effnet-1.pb`
- `mtg_jamendo_moodtheme-discogs-effnet-1.json`

These models are also available under a proprietary license upon
request from [UPF](https://www.upf.edu/web/mtg/contact).

See: https://essentia.upf.edu/models.html