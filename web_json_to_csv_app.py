import csv
import io
import json
import os
import zipfile

from flask import Flask, render_template_string, request, send_file

from json_to_csv_converter import build_rows_from_top_level


app = Flask(__name__)


PAGE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>JSON to CSV Converter</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg-a: #f3f6ff;
      --bg-b: #ffe8d6;
      --ink: #1f2937;
      --muted: #4b5563;
      --card: rgba(255, 255, 255, 0.8);
      --stroke: rgba(17, 24, 39, 0.12);
      --accent: #0f766e;
      --accent-2: #f97316;
      --danger: #991b1b;
      --danger-bg: #fee2e2;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Space Grotesk", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 25%, rgba(15, 118, 110, 0.20), transparent 45%),
        radial-gradient(circle at 85% 75%, rgba(249, 115, 22, 0.20), transparent 45%),
        linear-gradient(135deg, var(--bg-a), var(--bg-b));
      display: grid;
      place-items: center;
      padding: 20px;
    }

    .panel {
      width: min(760px, 96vw);
      background: var(--card);
      backdrop-filter: blur(8px);
      border: 1px solid var(--stroke);
      border-radius: 24px;
      box-shadow: 0 22px 45px rgba(15, 23, 42, 0.16);
      padding: 26px;
      animation: float-in 500ms ease;
    }

    h1 {
      margin: 0 0 8px;
      font-size: clamp(1.6rem, 3vw, 2.2rem);
      line-height: 1.1;
      letter-spacing: -0.02em;
    }

    p {
      margin: 0 0 16px;
      color: var(--muted);
    }

    .dropzone {
      border: 2px dashed rgba(15, 118, 110, 0.45);
      border-radius: 18px;
      padding: 24px 18px;
      text-align: center;
      background: rgba(255, 255, 255, 0.75);
      transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      min-height: 190px;
      justify-content: center;
    }

    .dropzone:hover,
    .dropzone.dragover {
      transform: translateY(-2px);
      border-color: var(--accent-2);
      background: rgba(255, 255, 255, 0.95);
    }

    .dropzone strong {
      display: block;
      font-size: 1.1rem;
      margin: 0;
    }

    .dropzone .sub {
      margin: 0;
      color: var(--muted);
      font-size: 1rem;
    }

    .dropzone .hint {
      font-size: 0.92rem;
      margin-top: 8px;
      color: var(--muted);
    }

    .file-input {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      border: 0;
    }

    .pick-btn {
      border: 1px solid rgba(15, 118, 110, 0.22);
      border-radius: 10px;
      padding: 8px 12px;
      background: white;
      color: #0f3d39;
      font-family: "DM Mono", monospace;
      font-size: 0.88rem;
      cursor: pointer;
    }

    .pick-btn:hover {
      border-color: rgba(249, 115, 22, 0.45);
    }

    .file-picked {
      margin-top: 10px;
      font-family: "DM Mono", monospace;
      font-size: 0.9rem;
      color: #0b3f3c;
      word-break: break-all;
    }

    button {
      margin-top: 18px;
      border: 0;
      border-radius: 14px;
      padding: 12px 20px;
      font-weight: 700;
      font-size: 1rem;
      color: white;
      background: linear-gradient(120deg, var(--accent), #0284c7);
      cursor: pointer;
      transition: transform 140ms ease, box-shadow 140ms ease;
    }

    .submit-row {
      display: flex;
      justify-content: center;
    }

    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 16px rgba(2, 132, 199, 0.35);
    }

    .error {
      margin: 12px 0 0;
      padding: 10px 12px;
      border-radius: 10px;
      background: var(--danger-bg);
      color: var(--danger);
      font-weight: 500;
    }

    .note {
      margin-top: 14px;
      font-size: 0.9rem;
      color: var(--muted);
    }

    @keyframes float-in {
      from { opacity: 0; transform: translateY(10px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @media (max-width: 600px) {
      .panel { padding: 18px; border-radius: 18px; }
      .dropzone { padding: 18px 12px; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="panel">
    <h1>JSON to CSV Converter</h1>
    <p>Upload one JSON for result.csv, or upload a ZIP of JSON files to get a ZIP of same-named CSV files.</p>

    <form method="post" enctype="multipart/form-data" id="uploadForm">
      <div class="dropzone" id="dropzone">
        <strong>Drop your JSON or ZIP file here</strong>
        <p class="sub">or browse from your computer</p>
        <label class="pick-btn" for="jsonFile">Choose JSON or ZIP</label>
        <input class="file-input" type="file" id="jsonFile" name="json_file" accept=".json,.zip,application/json,application/zip" required />
        <div class="hint">JSON: top-level object. ZIP: contains one or more UTF-8 .json files.</div>
        <div class="file-picked" id="pickedName"></div>
      </div>

      <div class="submit-row">
        <button type="submit">Convert and Download</button>
      </div>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    <p class="note">Your browser typically saves the file to your Downloads folder automatically.</p>
  </main>

  <script>
    const input = document.getElementById("jsonFile");
    const dropzone = document.getElementById("dropzone");
    const pickedName = document.getElementById("pickedName");

    function updatePickedName(file) {
      pickedName.textContent = file ? `Selected: ${file.name}` : "";
    }

    input.addEventListener("change", () => {
      updatePickedName(input.files && input.files[0]);
    });

    dropzone.addEventListener("click", (event) => {
      if (!event.target.classList.contains("pick-btn")) {
        input.click();
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (event) => {
      const files = event.dataTransfer.files;
      if (files && files.length > 0) {
        input.files = files;
        updatePickedName(files[0]);
      }
    });
  </script>
</body>
</html>
"""


def rows_to_csv_bytes(rows):
    fieldnames = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    return io.BytesIO(output.getvalue().encode("utf-8"))


def build_csv_bytes_from_json_payload(payload, source_name):
  try:
    data = json.loads(payload)
  except json.JSONDecodeError as exc:
    raise ValueError(f"Invalid JSON in {source_name}: {exc.msg}") from exc

  if not isinstance(data, dict):
    raise ValueError(f"Top-level JSON in {source_name} must be an object/dictionary.")

  rows = build_rows_from_top_level(data)
  return rows_to_csv_bytes(rows)


def build_csv_zip_from_uploaded_zip(uploaded_name, raw_bytes):
  zip_input = io.BytesIO(raw_bytes)
  if not zipfile.is_zipfile(zip_input):
    raise ValueError("Uploaded file is not a valid ZIP archive.")

  zip_input.seek(0)
  output_zip = io.BytesIO()

  with zipfile.ZipFile(zip_input, "r") as in_zip, zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
    json_members = [
      member for member in in_zip.infolist()
      if not member.is_dir() and member.filename.lower().endswith(".json")
    ]

    if not json_members:
      raise ValueError("ZIP archive does not contain any .json files.")

    used_names = set()
    for member in json_members:
      with in_zip.open(member, "r") as source_file:
        try:
          payload = source_file.read().decode("utf-8")
        except UnicodeDecodeError as exc:
          raise ValueError(f"JSON file must be UTF-8 encoded: {member.filename}") from exc

      csv_bytes = build_csv_bytes_from_json_payload(payload, member.filename)
      csv_name = os.path.splitext(member.filename)[0] + ".csv"

      # Avoid duplicate output names when ZIP has colliding JSON paths/stems.
      if csv_name in used_names:
        base, ext = os.path.splitext(csv_name)
        suffix = 2
        while f"{base}_{suffix}{ext}" in used_names:
          suffix += 1
        csv_name = f"{base}_{suffix}{ext}"

      used_names.add(csv_name)
      out_zip.writestr(csv_name, csv_bytes.getvalue())

  output_zip.seek(0)
  base_name = os.path.splitext(os.path.basename(uploaded_name or "converted"))[0]
  return output_zip, f"{base_name}_csv.zip"


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template_string(PAGE_HTML, error=None)

    uploaded = request.files.get("json_file")
    if uploaded is None or uploaded.filename == "":
        return render_template_string(PAGE_HTML, error="Please select a JSON or ZIP file.")

    try:
        raw_bytes = uploaded.read()
    except Exception:
        return render_template_string(PAGE_HTML, error="Could not read uploaded file.")

    if not raw_bytes:
        return render_template_string(PAGE_HTML, error="Uploaded file is empty.")

    filename = uploaded.filename or ""
    lowered_name = filename.lower()

    if lowered_name.endswith(".zip"):
        try:
            zip_bytes, download_name = build_csv_zip_from_uploaded_zip(filename, raw_bytes)
        except ValueError as exc:
            return render_template_string(PAGE_HTML, error=str(exc))

        return send_file(
            zip_bytes,
            mimetype="application/zip",
            as_attachment=True,
            download_name=download_name,
        )

    try:
        payload = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return render_template_string(PAGE_HTML, error="File must be UTF-8 encoded JSON.")

    try:
        csv_bytes = build_csv_bytes_from_json_payload(payload, filename or "uploaded JSON")
    except ValueError as exc:
        return render_template_string(PAGE_HTML, error=str(exc))

    return send_file(
        csv_bytes,
        mimetype="text/csv",
        as_attachment=True,
        download_name="result.csv",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)