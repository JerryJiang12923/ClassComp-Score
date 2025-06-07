# ClassComp Score
***Computer Usage Score Uploading System***

This is a lightweight web-based scoring system designed for student representatives to evaluate computer usage in other classrooms. It supports:

- 📝 Score submission per week
- 📊 Excel report export (2-week cycle per sheet, grouped by grade)
- 💾 Data stored in Supabase PostgreSQL

---

## ✨ Features

- Web-based form for information committee members to score each class
- Server-side export to Excel in structured format (per grade, biweekly)
- Automatic summary and submission log sheets
- Timezone-aware (Shanghai, UTC+8)
- Clean separation of front-end (HTML templates) and back-end (Flask)

---


## 🚀 Getting Started (Local)

### 1. Clone the repo

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup environment variables

Create a `.env` file:

```
DATABASE_URL=postgres://user:password@host:port/dbname
EXPORT_FOLDER=exports
```

### 4. Run the app

```bash
python app.py
```

The app will be available at: [http://localhost:5000](http://localhost:5000)

---

## 📦 Export Function

You can export a monthly report via:

```
GET /export_excel?month=YYYY-MM
```

This returns an `.xlsx` file containing:

* Sheet 1, 2...: each 2-week segment by grade
* Sheet “汇总”: average scores per evaluated class
* Sheet “提交明细”: raw submission records

---

## 🌐 Deployment Options

* ✅ **Replit** (recommended for quick hosting, free but may sleep)
* ✅ **Render / Fly.io / Railway** (supports 24/7 uptime with free tier)
* ⚠️ **Supabase Edge Functions** (requires JS rewrite)

If deploying on Replit:

* Set `PORT=3000`
* Set environment variables in the Secrets tab
* Use `/tmp/exports` as export path

---

## 🧪 Tech Stack

* **Backend**: Python + Flask
* **Database**: Supabase PostgreSQL
* **Excel Export**: pandas + xlsxwriter
* **Frontend**: HTML + JS (AJAX fetch)

