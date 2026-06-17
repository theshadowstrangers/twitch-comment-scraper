import json
import requests
import os

def get_user_data(streamer, username):
    url = f"https://logs.zonian.dev/api/{streamer}/{username}/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_links(streamer, username):
    return [
        f"https://logs.ivr.fi/?channel={streamer}&username={username}",
        f"https://logs.mejkiz.com/?channel={streamer}&username={username}",
        f"https://logs.potat.app/?channel={streamer}&username={username}",
        f"https://logs.spanix.team/?channel={streamer}&username={username}"
    ]

def user_analytics():
    print("\n" + "=" * 60)
    print("User Analytics Mode")
    print("=" * 60)
    
    if not os.path.exists("str.txt"):
        print("[-] File str.txt not found")
        return
    
    with open("str.txt", 'r') as f:
        streamers = [line.strip().lower() for line in f if line.strip()]
    
    if not streamers:
        print("[-] No streamers in str.txt")
        return
    
    print(f"[*] Loaded {len(streamers)} streamers")
    
    username = input("Username: ").strip().lower()
    if not username:
        print("[-] Username required")
        return
    
    print(f"\n[*] Checking {username} in {len(streamers)} channels...")
    print("=" * 60)
    
    found_channels = []
    
    for streamer in streamers:
        print(f"\n[+] Checking {streamer}...")
        data = get_user_data(streamer, username)
        
        if data and data.get('available', {}).get('user', False):
            print(f"  -> Found comments in {streamer}")
            
            links = generate_links(streamer, username)
            
            found_channels.append({
                "streamer": streamer,
                "fullLink": links
            })
        else:
            print(f"  -> No comments in {streamer}")
    
    if not found_channels:
        print("\n[-] No comments found")
        return
    
    # Список стримеров где найден
    streamer_list = [ch['streamer'] for ch in found_channels]
    total_num = len(streamer_list)
    
    # Показываем первые 3 стримера
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"Username: {username}")
    print(f"Twitch URL: https://twitch.tv/{username}")
    print(f"Streamers found: {', '.join(streamer_list[:3])}")
    if total_num > 3:
        print(f"... and {total_num - 3} more")
    print(f"Total streamers: {total_num}")
    
    # Показываем ссылки для первых 3 стримеров
    print("\nLinks (first 3):")
    for channel in found_channels[:3]:
        print(f"\n  Streamer: {channel['streamer']}")
        print("  fullLink:")
        for link in channel['fullLink']:
            print(f"    {link}")
    
    if total_num > 3:
        print(f"\n... and {total_num - 3} more streamers (see JSON)")
    
    # Сохраняем всё в JSON
    output_data = {
        "username": username,
        "twitchUrl": f"https://twitch.tv/{username}",
        "streamerFind": streamer_list,
        "streamerTotalNum": total_num,
        "foundIn": found_channels
    }
    
    filename = f"{username}_analytic.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[+] Saved to {filename}")

def main():
    while True:
        print("\n" + "=" * 60)
        print("Zonian Analytics v1.0")
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
