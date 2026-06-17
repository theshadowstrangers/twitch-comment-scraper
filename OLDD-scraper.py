
#!/usr/bin/env python3
import json
import re
import requests
import time
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
                "date": match.group(1),
                "text": match.group(2).strip()
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

def single_user_mode():
    print("\n" + "=" * 60)
    print("Single User Scrape Mode")
    print("=" * 60)

    streamer = input("Streamer name: ").strip()
    if not streamer:
        print("[-] Streamer name required")
        return

    username = input("Username: ").strip()
    if not username:
        print("[-] Username required")
        return

    start_year = input("Start year (default 2016): ").strip()
    start_year = int(start_year) if start_year.isdigit() else 2016

    max_workers = input("Threads (default 30): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 30

    comments = scrape_user(username, streamer, start_year, max_workers)

    if comments:
        print("\n" + "=" * 60)
        print(f"User: {username}")
        print(f"Total comments: {len(comments)}")
        print("=" * 60)

        print("\nOutput options:")
        print("1. Show all comments in terminal")
        print("2. Save to file only (default)")

        choice = input("\n> ").strip()

        if choice == '1':
            print("\n" + "-" * 40)
            for i, c in enumerate(comments, 1):
                print(f"{i}. {c['date']}: {c['text']}")
                if i % 50 == 0:
                    input("Press Enter to continue...")
            print("-" * 40)

        filename = f"{username}_{streamer}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "username": username,
                "twitchUrl": f"https://twitch.tv/{username}",
                "streamer": streamer,
                "totalComments": len(comments),
                "comments": comments
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[+] Saved to {filename}")
    else:
        print("[-] No comments found")

def file_mode():
    print("\n" + "=" * 60)
    print("File Mode (Batch Scrape)")
    print("=" * 60)

    filepath = input("Path to file with usernames: ").strip()
    if not filepath or not os.path.exists(filepath):
        print("[-] File not found")
        return

    streamer = input("Streamer name: ").strip()
    if not streamer:
        print("[-] Streamer name required")
        return

    start_year = input("Start year (default 2016): ").strip()
    start_year = int(start_year) if start_year.isdigit() else 2016

    max_workers = input("Threads per user (default 30): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 30

    with open(filepath, 'r') as f:
        usernames = [line.strip() for line in f if line.strip()]

    print(f"[*] Loaded {len(usernames)} usernames")
    results = []
    errors = []

    for i, name in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] Processing {name}...")
        comments = scrape_user(name, streamer, start_year, max_workers)
        if comments:
            results.append({
                "username": name,
                "twitchUrl": f"https://twitch.tv/{name}",
                "streamer": streamer,
                "totalComments": len(comments),
                "comments": comments
            })
            print(f"  -> {len(comments)} comments found")
        else:
            errors.append(name)
            print("  -> No comments")

    output_file = f"scraped_{streamer}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Total: {len(usernames)}")
    print(f"Success: {len(results)}")
    print(f"Failed: {len(errors)}")
    print(f"Saved to: {output_file}")

def search_from_file():
    print("\n" + "=" * 60)
    print("Search Mode")
    print("=" * 60)

    filepath = input("Path to JSON file (comments file): ").strip()
    if not filepath or not os.path.exists(filepath):
        print("[-] File not found")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[-] Invalid JSON file: {e}")
        return

    all_comments = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if 'comments' in item:
                    username = item.get('username', 'unknown')
                    for comment in item['comments']:
                        all_comments.append({
                            'username': username,
                            'date': comment.get('date', ''),
                            'text': comment.get('text', '')
                        })
                elif 'text' in item or 'date' in item:
                    all_comments.append({
                        'username': 'unknown',
                        'date': item.get('date', ''),
                        'text': item.get('text', '')
                    })
    elif isinstance(data, dict):
        if 'comments' in data:
            username = data.get('username', 'unknown')
            for comment in data['comments']:
                all_comments.append({
                    'username': username,
                    'date': comment.get('date', ''),
                    'text': comment.get('text', '')
                })

    if not all_comments:
        print("[-] No comments found in JSON")
        return

    print(f"[+] Loaded {len(all_comments)} comments from {filepath}")
    print("\nSearch commands:")
    print("  @search:<text> - search by text/date")
    print("  help - show this menu")
    print("  exit - exit search mode")

    while True:
        query = input("\n@search: ").strip()
        if not query:
            continue

        if query.lower() == 'exit':
            break

        if query.lower() == 'help':
            print("\nSearch commands:")
            print("  @search:<text> - search by text/date")
            print("  exit - exit search mode")
            continue

        results = []
        search_term = query.lower()

        for comment in all_comments:
            if search_term in comment['text'].lower() or search_term in comment['date']:
                results.append(comment)

        if results:
            print(f"\n[+] Found {len(results)} results:")
            print("-" * 40)
            for i, res in enumerate(results[:50], 1):
                print(f"[{i}] {res['username']} | {res['date']}")
                print(f"    {res['text'][:200]}")
                print()
            if len(results) > 50:
                print(f"... and {len(results) - 50} more results")
        else:
            print("[-] No results found")

def personalinfo_checker():
    print("\n" + "=" * 60)
    print("Personal Info Checker")
    print("=" * 60)

    filepath = input("Path to JSON file (comments file): ").strip()
    if not filepath or not os.path.exists(filepath):
        print("[-] File not found")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[-] Invalid JSON file: {e}")
        return

    all_comments = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if 'comments' in item:
                    username = item.get('username', 'unknown')
                    for comment in item['comments']:
                        all_comments.append({
                            'username': username,
                            'date': comment.get('date', ''),
                            'text': comment.get('text', '')
                        })
                elif 'text' in item or 'date' in item:
                    all_comments.append({
                        'username': 'unknown',
                        'date': item.get('date', ''),
                        'text': item.get('text', '')
                    })
    elif isinstance(data, dict):
        if 'comments' in data:
            username = data.get('username', 'unknown')
            for comment in data['comments']:
                all_comments.append({
                    'username': username,
                    'date': comment.get('date', ''),
                    'text': comment.get('text', '')
                })

    if not all_comments:
        print("[-] No comments found in JSON")
        return

    print(f"[+] Loaded {len(all_comments)} comments from {filepath}")

    age_count = 0
    phone_count = 0
    tag_count = 0

    age_pattern = re.compile(r'\b\d{2}\b|\b\d-\d\b')
    phone_pattern = re.compile(r'(?:\+7|7|1|380|79)?\d{9,11}\b')
    tag_pattern = re.compile(r'@\w+')

    for comment in all_comments:
        text = comment['text']
        age_count += len(age_pattern.findall(text))
        phone_count += len(phone_pattern.findall(text))
        tag_count += len(tag_pattern.findall(text))

    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(f"1. Age found total: {age_count}")
    print(f"2. Phones found total: {phone_count}")
    print(f"3. Tags people total: {tag_count}")
    print("4. Exit")
    print("=" * 60)

    while True:
        choice = input("\n> ").strip()

        if choice == '1':
            if age_count == 0:
                print("[-] No ages found")
                continue

            ages = []
            for comment in all_comments:
                matches = age_pattern.findall(comment['text'])
                for match in matches:
                    ages.append({
                        'username': comment['username'],
                        'date': comment['date'],
                        'match': match,
                        'full_text': comment['text']
                    })

            print(f"\n[+] Found {len(ages)} age mentions:")
            print("-" * 40)
            for i, age in enumerate(ages[:30], 1):
                print(f"[{i}] {age['username']} | {age['date']}")
                print(f"    Age: {age['match']}")
                print(f"    Context: {age['full_text'][:100]}...")
                print()
            if len(ages) > 30:
                print(f"... and {len(ages) - 30} more")

        elif choice == '2':
            if phone_count == 0:
                print("[-] No phone numbers found")
                continue

            phones = []
            for comment in all_comments:
                matches = phone_pattern.findall(comment['text'])
                for match in matches:
                    phones.append({
                        'username': comment['username'],
                        'date': comment['date'],
                        'phone': match,
                        'full_text': comment['text']
                    })

            print(f"\n[+] Found {len(phones)} phone numbers:")
            print("-" * 40)
            for i, phone in enumerate(phones[:30], 1):
                print(f"[{i}] {phone['username']} | {phone['date']}")
                print(f"    Phone: {phone['phone']}")
                print(f"    Context: {phone['full_text'][:100]}...")
                print()
            if len(phones) > 30:
                print(f"... and {len(phones) - 30} more")

        elif choice == '3':
            if tag_count == 0:
                print("[-] No tags found")
                continue

            tags = []
            for comment in all_comments:
                matches = tag_pattern.findall(comment['text'])
                for match in matches:
                    tags.append({
                        'username': comment['username'],
                        'date': comment['date'],
                        'tag': match,
                        'full_text': comment['text']
                    })

            print(f"\n[+] Found {len(tags)} tags:")
            print("-" * 40)
            for i, tag in enumerate(tags[:30], 1):
                print(f"[{i}] {tag['username']} | {tag['date']}")
                print(f"    Tag: {tag['tag']}")
                print(f"    Context: {tag['full_text'][:100]}...")
                print()
            if len(tags) > 30:
                print(f"... and {len(tags) - 30} more")

        elif choice == '4':
            break

        else:
            print("[-] Invalid choice")

def help_menu():
    print("\n" + "=" * 60)
    print("HELP MENU")
    print("=" * 60)
    print("1. Bro just search - search by text/date in comments file")
    print("2. Personal info checker - check for ages, phones, tags in comments")
    print("3. Help - show this menu")
    print("4. Exit - exit to main menu")
    print("=" * 60)

def main():
    while True:
        print("=" * 60)
        print("Twitch Chat Scraper v10.0 (Full Control)")
        print("=" * 60)
        print("\n1. Scrape single user")
        print("2. Scrape users from file")
        print("3. Search from file")
        print("4. Personal info checker")
        print("5. Help")
        print("6. Exit")

        choice = input("\n> ").strip()

        if choice == '1':
            single_user_mode()
        elif choice == '2':
            file_mode()
        elif choice == '3':
            search_from_file()
        elif choice == '4':
            personalinfo_checker()
        elif choice == '5':
            help_menu()
        elif choice == '6':
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
