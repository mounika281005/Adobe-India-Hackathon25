import json
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- Extract sections from PDF ----------------
def extract_sections(pdf_path):
    """
    Extracts text sections (lines/spans) from a PDF file.
    """
    doc = fitz.open(pdf_path)
    sections = []
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            sections.append({
                                "text": text,
                                "page": page_num,
                                "size": span["size"],
                                "flags": span["flags"]
                            })
    return sections

# ---------------- Rank sections by relevance ----------------
def rank_sections(sections, persona_desc, task_desc):
    """
    Rank PDF text sections based on relevance to persona and job-to-be-done
    using TF-IDF and cosine similarity.
    """
    combined_query = persona_desc + " " + task_desc
    texts = [s["text"] for s in sections]

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([combined_query] + texts)
    query_vec = vectors[0]
    doc_vecs = vectors[1:]
    sims = cosine_similarity(query_vec, doc_vecs).flatten()

    # Attach scores to sections
    for i, score in enumerate(sims):
        sections[i]["score"] = score

    # Sort sections by relevance
    ranked = sorted(sections, key=lambda x: x["score"], reverse=True)
    return ranked

# ---------------- Main processing ----------------
def process_collection(input_json_path, input_folder, output_path):
    """
    Process PDFs + persona + task and generate structured JSON output.
    """
    # Load input JSON
    with open(input_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    persona_desc = config["persona"]["role"]
    task_desc = config["job_to_be_done"]["task"]
    docs = config["documents"]

    all_sections = []

    # Extract text sections from each PDF
    for doc_meta in docs:
        pdf_path = Path(input_folder) / doc_meta["filename"]
        sections = extract_sections(pdf_path)
        for s in sections:
            s["document"] = doc_meta["filename"]
        all_sections.extend(sections)

    # Rank sections
    ranked = rank_sections(all_sections, persona_desc, task_desc)

    # Take top 10 most relevant sections
    top_sections = ranked[:10]

    # Prepare output JSON
    output_data = {
        "metadata": {
            "input_documents": [d["filename"] for d in docs],
            "persona": persona_desc,
            "job_to_be_done": task_desc,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": [
            {
                "document": s["document"],
                "section_title": s["text"][:100],  # Title = first 100 chars of text
                "importance_rank": i + 1,
                "page_number": s["page"]
            }
            for i, s in enumerate(top_sections)
        ],
        "subsection_analysis": [
            {
                "document": s["document"],
                "refined_text": s["text"],
                "page_number": s["page"]
            }
            for s in top_sections
        ]
    }

    # Save JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

# ---------------- Entrypoint for Docker ----------------
if __name__ == "__main__":
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    input_json_path = input_dir / "challenge1b_input.json"
    output_json_path = output_dir / "challenge1b_output.json"

    process_collection(input_json_path, input_dir, output_json_path)
