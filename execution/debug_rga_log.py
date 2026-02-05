
import sys

def search_rga_log():
    try:
        content = ""
        try:
            with open("rga_strict_output_v2.txt", "r", encoding="utf-16") as f:
                content = f.read()
        except UnicodeError:
            with open("rga_strict_output_v2.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "Processando cliente" in line:
                print(f"FOUND ACCOUNT LINE: {line}")
            if any(key in line for key in ["18/09/25", "FERNÃO DIAS", "COBERTURA", "Post do Instagram"]):
                 print(f"Match at line {i}: {line}")
                 # Print surrounding lines to see objective or error
                 start = max(0, i-1)
                 end = min(len(lines), i+3)
                 for j in range(start, end):
                     print(f"  {lines[j]}")
                 print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_rga_log()
