import datetime

def main():
    now = datetime.datetime.utcnow().isoformat()
    print(f"Daily job ran at (UTC): {now}")

if __name__ == "__main__":
    main()
