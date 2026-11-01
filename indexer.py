import os
import sqlite3
import json
from google.oauth2 import service_account
import googleapiclient.discovery

# --- KONFIGURASI ---
DB_PATH = "database_5menit/database.sqlite"  # Sesuaikan dengan folder database Anda di GitHub
BASE_URL = "https://thenewsday112.github.io/banyakrss7"

def run_google_indexer():
    print("=" * 60)
    print("MEMULAI PENGIRIMAN URL KE GOOGLE INDEXING API (VIA GITHUB)")
    print("=" * 60)

    # 1. Autentikasi menggunakan GitHub Secret
    try:
        google_creds_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if google_creds_env:
            creds_dict = json.loads(google_creds_env)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=["https://www.googleapis.com/auth/indexing"]
            )
        else:
            CREDENTIALS_FILE = "service_account.json"
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[-] ERROR: File '{CREDENTIALS_FILE}' tidak ditemukan!")
                return
            credentials = service_account.Credentials.from_service_file(
                CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/indexing"]
            )
            
        service = googleapiclient.discovery.build("indexing", "v3", credentials=credentials)
        print("[+] Berhasil terhubung ke Google Indexing API.")
    except Exception as e:
        print(f"[-] Gagal melakukan autentikasi Google API: {e}")
        return

    # 2. Validasi Database SQLite
    if not os.path.exists(DB_PATH):
        print(f"[-] ERROR: Database tidak ditemukan pada path: {DB_PATH}")
        return

    # 3. Ambil Daftar Artikel Terbaru dari Database SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM artikel ORDER BY id DESC LIMIT 50")
        articles = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[-] Gagal membaca database SQLite: {e}")
        return

    if not articles:
        print("[-] Tidak ada artikel ditemukan di dalam database.")
        return

    print(f"[*] Ditemukan {len(articles)} artikel untuk dikirim ke Google.\n")

    success_count = 0
    failed_count = 0

    # 4. Kirim URL Satu per Satu ke Google
    for row in articles:
        artikel_id = row[0]
        url_to_index = f"{BASE_URL}/output/artikel.html#artikel-{artikel_id}" # Sesuaikan path file HTML Anda

        body = {
            "url": url_to_index,
            "type": "URL_UPDATED"
        }

        try:
            request = service.urlNotifications().publish(body=body)
            response = request.execute()
            success_count += 1
            print(f"[OK] Berhasil di-index: {url_to_index}")
        except Exception as e:
            failed_count += 1
            print(f"[GAGAL] {url_to_index} -> Error: {e}")

    print("\n" + "=" * 60)
    print(f"[PROSES SELESAI]")
    print(f" - Berhasil dikirim ke Google : {success_count}")
    print(f" - Gagal / Terlewati         : {failed_count}")
    print("=" * 60)

if __name__ == "__main__":
    run_google_indexer()