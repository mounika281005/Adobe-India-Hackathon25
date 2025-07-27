# Adobe Hackathon Round 1A - PDF Outline Extractor

## Overview
Extracts **Title**, **H1**, **H2**, and **H3** headings from PDF and outputs hierarchical JSON.

---

## Build Docker Image
```bash
docker build --platform linux/amd64 -t pdf-processor .
