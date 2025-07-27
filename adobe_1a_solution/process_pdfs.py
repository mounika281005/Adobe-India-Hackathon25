import json
from pathlib import Path
import fitz  # PyMuPDF

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)
    text_elements = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    # Collect spans with positions
                    spans_data = []
                    for span in line["spans"]:
                        if span["text"].strip():
                            spans_data.append({
                                "text": span["text"],
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                                "size": span["size"]
                            })
                    # Sort spans left-to-right
                    spans_data.sort(key=lambda s: s["x"])

                    # Merge spans into one string (small gap threshold)
                    merged_text = ""
                    last_x = None
                    sizes = []
                    for span in spans_data:
                        if last_x is not None and span["x"] - last_x > 5:
                            merged_text += " "  # add space for big gap
                        merged_text += span["text"]
                        last_x = span["x"] + len(span["text"])  # approx end
                        sizes.append(span["size"])

                    if merged_text.strip():
                        avg_size = round(sum(sizes) / len(sizes), 1) if sizes else 0
                        text_elements.append({
                            "text": merged_text.strip(),
                            "size": avg_size,
                            "page": page_num
                        })

    # Determine font size levels dynamically
    font_sizes = sorted(set(el["size"] for el in text_elements if el["size"] > 0), reverse=True)
    level_map = {}
    if len(font_sizes) > 0: level_map[font_sizes[0]] = "H1"
    if len(font_sizes) > 1: level_map[font_sizes[1]] = "H2"
    if len(font_sizes) > 2: level_map[font_sizes[2]] = "H3"
    if len(font_sizes) > 3: level_map[font_sizes[3]] = "H4"

    # Title = first H1
    title = ""
    for el in text_elements:
        if round(el["size"], 1) == font_sizes[0]:
            title = el["text"]
            break

    outline = []
    for el in text_elements:
        level = level_map.get(round(el["size"], 1))
        if level:
            outline.append({
                "level": level,
                "text": el["text"],
                "page": el["page"]
            })

    return {"title": title, "outline": outline}

def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in input_dir.glob("*.pdf"):
        print(f"Processing: {pdf_file.name}")
        result = extract_headings(pdf_file)
        output_path = output_dir / f"{pdf_file.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    process_pdfs()
