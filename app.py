import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import re
from typing import Dict, Tuple, Optional

st.set_page_config(page_title="Chord Annotator (No Nashville)", page_icon="🎼")

st.title("🎼 Chord Annotator — No Nashville Conversion")
st.write("Paste lyrics, enter chords per word (as-is, no conversion), then export a PNG.")

# ---------------------- Helpers ----------------------
def tokenize_line(line: str):
    # tokens preserve spaces so we can measure text properly
    return re.findall(r"\S+|\s+", line)

def render_chorded_lyrics(
    lyrics: str,
    chord_map: Dict[Tuple[int,int], str],
    title: Optional[str] = None,
    page_width: int = 1500,
    margin: int = 60,
    line_spacing: int = 18,
    chord_gap: int = 8,
) -> Image.Image:
    lines = lyrics.splitlines()
    try:
        base_font = ImageFont.truetype("DejaVuSansMono.ttf", 28)
        chord_font = ImageFont.truetype("DejaVuSansMono.ttf", 24)
        title_font = ImageFont.truetype("DejaVuSans.ttf", 36)
    except Exception:
        base_font = ImageFont.load_default()
        chord_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    def textheight(font):
        bbox = font.getbbox("Ag")
        return bbox[3] - bbox[1]

    line_h = textheight(base_font)
    chord_h = textheight(chord_font)
    title_h = (textheight(title_font) + 20) if title else 0
    total_h = margin + title_h + (line_h + chord_h + chord_gap + line_spacing) * len(lines) + margin

    img = Image.new("RGB", (page_width, total_h), "white")
    draw = ImageDraw.Draw(img)

    y = margin
    if title:
        tw = draw.textlength(title, font=title_font)
        draw.text(((page_width - tw)//2, y), title, fill="black", font=title_font)
        y += title_h

    for li, line in enumerate(lines):
        tokens = tokenize_line(line)
        x = margin
        # Draw chords above words
        for ti, tok in enumerate(tokens):
            if tok.isspace():
                x += draw.textlength(tok, font=base_font)
                continue
            tok_w = draw.textlength(tok, font=base_font)
            if (li, ti) in chord_map:
                chord_txt = chord_map[(li, ti)]
                cw = draw.textlength(chord_txt, font=chord_font)
                draw.text((x + (tok_w - cw)/2, y), chord_txt, fill="black", font=chord_font)
            x += tok_w + draw.textlength(" ", font=base_font)
        # Draw lyric line
        draw.text((margin, y + chord_h + chord_gap), line, fill="black", font=base_font)
        y += chord_h + chord_gap + line_h + line_spacing

    return img

# ---------------------- UI ----------------------
default_lyrics = "Guide me, O Thou great Jehovah\nPilgrim through this barren land"
lyrics = st.text_area("Lyrics", value=default_lyrics, height=180)

if "chords" not in st.session_state or st.button("Reset chord inputs"):
    st.session_state.chords = {}

lines = lyrics.splitlines()
st.subheader("Enter chords above words (leave blank to skip)")
for li, line in enumerate(lines):
    tokens = tokenize_line(line)
    cols = st.columns(min(8, max(1, len(tokens))))
    col_idx = 0
    for ti, tok in enumerate(tokens):
        if tok.isspace():
            continue
        key_name = f"li{li}_ti{ti}"
        with cols[col_idx % len(cols)]:
            st.text_input(f"'{tok}'", key=key_name, value=st.session_state.chords.get((li,ti), ""))
        col_idx += 1

title = st.text_input("Optional title", "Chord Chart")
page_width = st.slider("Image width (px)", 800, 2200, 1500, 50)

if st.button("Render PNG"):
    chord_map = {}
    for li, line in enumerate(lines):
        tokens = tokenize_line(line)
        for ti, tok in enumerate(tokens):
            if tok.isspace():
                continue
            key_name = f"li{li}_ti{ti}"
            val = st.session_state.get(key_name, "").strip()
            if val:
                chord_map[(li, ti)] = val  # <-- use exactly what the user typed, no conversion
                st.session_state.chords[(li,ti)] = val
    image = render_chorded_lyrics(lyrics, chord_map, title=title, page_width=page_width)
    st.image(image, caption="Preview", use_container_width=True)
    import io
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    st.download_button("Download PNG", data=buf.getvalue(), file_name="lyrics_chords.png", mime="image/png")
