# ProPlus — Daily Finance Tracker (Docker + MongoDB + Streamlit)

Ավտոմատ օրական գրանցումներ → PNG/PDF հաշվետվություն → email առաքում → շաբաթական Mongo backup։  
Պատրաստ գործարկման “1 command” տնօրինմամբ՝ Docker Compose-ով։

## ✔️ Հնարավորություններ
- `make add income=... debt=... savings=...` — օրվա թվերի գրանցում Mongo-ում  
- `make report` — գրաֆիկով PNG/PDF հաշվետվություն (`data_analytics/reports/`)  
- `make email` — հաշվետվության ավտոմատ email ուղարկում  
- Streamlit dashboard — http://localhost:8501  
- Շաբաթական `mongodump` պահուստավորում (cron օրինակներ ներքևում)

## 🧱 Տեխնոլոգիաներ
Docker, Docker Compose, MongoDB 6, Python 3.11, Streamlit, Matplotlib, SMTP (Gmail)

## 🚀 Արագ start
```bash
docker compose up -d
# բացիր http://localhost:8501
make add income=12000 debt=3000 savings=2000
make report
make email
![CI](https://github.com/sur75700/proplus/actions/workflows/ci.yml/badge.svg)

