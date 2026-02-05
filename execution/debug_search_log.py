
import sys

def search_log():
    try:
        # Try different encodings
        content = ""
        try:
            with open("output.txt", "r", encoding="utf-16") as f:
                content = f.read()
        except UnicodeError:
            with open("output.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "27.11" in line:
                print(f"Match at line {i}: {line}")
                # Print context
                start = max(0, i-2)
                end = min(len(lines), i+2)
                for j in range(start, end):
                    print(f"  {lines[j]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_log()
