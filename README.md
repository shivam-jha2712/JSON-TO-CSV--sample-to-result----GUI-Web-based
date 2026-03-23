# JSON to CSV Converter

This project converts a JSON file from `source/` into `result/result.csv`.

No CLI input is required.

## Instant Share Version (No CMD Needed)

This repo now includes a pure browser app that needs no Python runtime for end users:

- `index.html` - static JSON to CSV converter (runs fully in browser)
- `Open JSON to CSV Website.url` - one-click shortcut that opens your deployed website
- `open_json_to_csv_website.bat` - double-click launcher for the deployed website

For users, the flow is:

1. Open your deployed site URL.
2. Upload one JSON, or upload one ZIP that contains multiple JSON files.
3. Click convert.
4. Browser downloads `result.csv` (single JSON) or `<your-zip-name>_csv.zip` (ZIP input).

No command line is needed for end users.

## Runtime Behavior

- The app looks for `.json` files inside `source/`.
- If multiple JSON files exist, it picks the most recently modified one.
- It writes output to `result/result.csv` (overwrites if already present).

## Folder Layout

- `json_to_csv_converter.py` - converter script
- `source/` - place input JSON files here
- `result/` - generated CSV output

## Build `.exe` (one-time)

From the project folder, run:

```powershell
py -m pip install pyinstaller
py -m PyInstaller --onefile --name json_to_csv_converter .\json_to_csv_converter.py
```

After build, the executable will be at:

`dist\json_to_csv_converter.exe`

## How User Runs It

1. Keep the generated `dist\\json_to_csv_converter.exe` as-is.
2. Put a JSON file in `source/`.
3. Double-click `json_to_csv_converter.exe`.
4. Check `result\result.csv`.

Tip: You can run the `.exe` directly from `dist/`; it will automatically detect `source/` and `result/` in the project root.

## Notes

- Input JSON must have a top-level object/dictionary.
- Nested objects are flattened using `__` (double underscore).

## Web App Version (Upload and Download)

This repo now includes a web-based app that does the same conversion logic:

- Upload one `.json` file from your computer for a single CSV.
- Or upload one `.zip` file that contains `.json` files for bulk conversion.
- Click convert.
- The browser downloads `result.csv` (single JSON) or `<your-zip-name>_csv.zip` (ZIP input).

### File

- `web_json_to_csv_app.py` - Flask app with upload UI and CSV download

### Run the Web App

From the project folder, run:

```powershell
py -m pip install -r .\requirements.txt
py .\web_json_to_csv_app.py
```

Then open:

`http://127.0.0.1:5000`

## Deploy to Netlify (Simple)

This project can be deployed as a static site using `index.html`.

1. Push this folder to GitHub.
2. In Netlify, create a new site from that repository.
3. Build command: leave empty.
4. Publish directory: `.`

`netlify.toml` is already included with publish set to root.

After deploy, update `Open JSON to CSV Website.url` with your real Netlify URL.

## Deploy to Vercel (Simple)

1. Import this repository into Vercel.
2. Framework preset: `Other`.
3. Build command: leave empty.
4. Output directory: `.` (or leave default for static root files).

`vercel.json` is included for clean static hosting behavior.

After deploy, update `Open JSON to CSV Website.url` with your real Vercel URL.

### Notes for Downloads Folder Behavior

- The app sends the file as an attachment named `result.csv`.
- Your browser controls the final save location.
- In most setups this means the file goes directly to your Downloads folder.