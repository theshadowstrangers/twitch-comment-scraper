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

    all_comments = []
    streamer_stats = {}

    for i, streamer in enumerate(streamers, 1):
        print(f"\n[{i}/{len(streamers)}] Checking #{streamer}...")
        comments = scrape_user(username, streamer, start_year, max_workers)
        if comments:
            streamer_stats[streamer] = len(comments)
            for c in comments:
                all_comments.append({
                    "Streamer": streamer,
                    "username": username,
                    "User-comment": c['commentUser'],
                    "timestamp": c['timestamp']
                })
            print(f"  -> Found {len(comments)} comments")
        else:
            streamer_stats[streamer] = 0
            print("  -> No comments found")

    if not all_comments:
        print("\n[-] No comments found in any channel")
        return

    # Sort stats
    sorted_stats = sorted(streamer_stats.items(), key=lambda x: x[1], reverse=True)
    found_streamers = [s for s, count in sorted_stats if count > 0]
    found_count = len(found_streamers)
    total_comments = len(all_comments)

    top_streamer = sorted_stats[0][0] if sorted_stats else "None"
    top_count = sorted_stats[0][1] if sorted_stats else 0

    # Find bottom (excluding zeros)
    non_zero_stats = [(s, c) for s, c in sorted_stats if c > 0]
    bottom_streamer = non_zero_stats[-1][0] if non_zero_stats else "None"
    bottom_count = non_zero_stats[-1][1] if non_zero_stats else 0

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"Username: {username}")
    print(f"Twitch URL: https://twitch.tv/{username}")
    print(f"Streamers comment found: {', '.join(found_streamers[:10])}{'...' if len(found_streamers) > 10 else ''}")
    print(f"StreamersNumTotal: {found_count}")
    print(f"Total comments: {total_comments}")
    print(f"Top-commented: {top_streamer} ({top_count} comments)")
    print(f"No-Top-comment: {bottom_streamer} ({bottom_count} comments)")
    print("=" * 60)

    print("\nOutput options:")
    print("1. Show all comments in terminal")
    print("2. Save to file only (default)")

    choice = input("\n> ").strip()

    if choice == '1':
        print("\n" + "-" * 40)
        for i, res in enumerate(all_comments, 1):
            print(f"[{i}] Streamer: #{res['Streamer']}")
            print(f"    username: {res['username']}")
            print(f"    User-comment: {res['User-comment']}")
            print(f"    timestamp: {res['timestamp']}")
            print()
            if i % 10 == 0:
                input("Press Enter to continue...")
        print("-" * 40)

    # Save results
    output_data = {
        "username": username,
        "twitchUrl": f"https://twitch.tv/{username}",
        "Streamers comment found": found_streamers,
        "streamersNumTotal": found_count,
        "total-comments": total_comments,
        "top-commented": f"{top_streamer} ({top_count} comments)",
        "no-Top-comment": f"{bottom_streamer} ({bottom_count} comments)",
        "comments": all_comments
    }

    filename = f"{username}_analytic.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

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
