import json
import re
import requests
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_comments_for_month(username, streamer, year, month):
    url = f"https://logs.ivr.fi/channel/{streamer}/user/{username}/{year}/{month}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def parse_comments(text, username):
    comments = []
    pattern = rf'\[(.*?)\] #\w+ {re.escape(username)}: (.*)'
    for line in text.strip().split('\n'):
        match = re.match(pattern, line)
        if match:
            comments.append({
                "timestamp": match.group(1),
                "commentUser": match.group(2).strip()
            })
    return comments

def scrape_user(username, streamer, start_year, max_workers=30):
    print(f"\n[*] Scraping {username} from #{streamer} ({start_year}-{datetime.now().year}) with {max_workers} threads")
    all_comments = []
    current_year = datetime.now().year

    tasks = []
    for year in range(current_year, start_year - 1, -1):
        for month in range(12, 0, -1):
            tasks.append((year, month))

    def fetch_month(year, month):
        text = get_comments_for_month(username, streamer, year, month)
        if text:
            comments = parse_comments(text, username)
            if comments:
                return (year, month, comments)
        return (year, month, [])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_month, year, month): (year, month) for year, month in tasks}

        for future in as_completed(futures):
            year, month, comments = future.result()
            if comments:
                print(f"  [+] {year}/{month}: {len(comments)} comments")
                all_comments.extend(comments)
            else:
                print(f"  [-] {year}/{month}: nothing")

    return all_comments

def user_analytics():
    print("\n" + "=" * 60)
    print("User Analytics Mode")
    print("=" * 60)

    default_file = "str.txt"
    if os.path.exists(default_file):
        print(f"[*] Found default file: {default_file}")
        use_default = input("Use this file? (y/n): ").strip().lower()
        if use_default == 'y':
            filepath = default_file
        else:
            filepath = input("Path to file with streamer names: ").strip()
            if not filepath or not os.path.exists(filepath):
                print("[-] File not found")
                return
    else:
        filepath = input("Path to file with streamer names (default: str.txt): ").strip()
        if not filepath:
            filepath = "str.txt"
        if not os.path.exists(filepath):
            print(f"[-] File {filepath} not found")
            return

    with open(filepath, 'r') as f:
        streamers = [line.strip().lower() for line in f if line.strip()]
        streamers = [re.sub(r'[^a-z0-9]', '', s) for s in streamers if s]

    if not streamers:
        print("[-] No valid streamer names found")
        return

    print(f"[*] Loaded {len(streamers)} streamers: {', '.join(streamers[:10])}{'...' if len(streamers) > 10 else ''}")

    username = input("Username: ").strip().lower()
    if not username:
        print("[-] Username required")
        return

    start_year = input("Start year (default 2016): ").strip()
    start_year = int(start_year) if start_year.isdigit() else 2016

    max_workers = input("Threads (default 30): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 30

    print(f"\n[*] Checking {username} in {len(streamers)} channels...")
    print("=" * 60)

    results = []
    total_comments = 0

    for i, streamer in enumerate(streamers, 1):
        print(f"\n[{i}/{len(streamers)}] Checking #{streamer}...")
        comments = scrape_user(username, streamer, start_year, max_workers)
        if comments:
            for c in comments:
                results.append({
                    "Streamer": streamer,
                    "username": username,
                    "User-comment": c['commentUser'],
                    "timestamp": c['timestamp']
                })
            total_comments += len(comments)
            print(f"  -> Found {len(comments)} comments")
        else:
            print("  -> No comments found")

    if not results:
        print("\n[-] No comments found in any channel")
        return

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"Username: {username}")
    print(f"Channels with comments: {len(set(r['Streamer'] for r in results))}")
    print(f"Total comments: {total_comments}")
    print("=" * 60)

    print("\nOutput options:")
    print("1. Show all comments in terminal")
    print("2. Save to file only (default)")

    choice = input("\n> ").strip()

    if choice == '1':
        print("\n" + "-" * 40)
        for i, res in enumerate(results, 1):
            print(f"[{i}] Streamer: #{res['Streamer']}")
            print(f"    username: {res['username']}")
            print(f"    User-comment: {res['User-comment']}")
            print(f"    timestamp: {res['timestamp']}")
            print()
            if i % 10 == 0:
                input("Press Enter to continue...")
        print("-" * 40)

    filename = f"{username}_analytic.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Saved to {filename}")

def main():
    while True:
        print("\n" + "=" * 60)
        print("User Analytics Tool")
        print("=" * 60)
        print("\n1. User Analytics")
        print("2. Exit")

        choice = input("\n> ").strip()

        if choice == '1':
            user_analytics()
        elif choice == '2':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

        print("\n" + "-" * 60)
        input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[-] Stopped by user")
    except Exception as e:
        print(f"\n[-] Error: {e}")
