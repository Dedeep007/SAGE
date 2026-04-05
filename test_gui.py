import re

def main():
    result = ('C:\\path\\image.webp', '(0.4546, 0.48863)', 'C:\\path2\\image.webp')
    
    # Existing regex in tools.py
    coords = re.findall(r"[\(\[]([0-9.]+),\s*([0-9.]+)[\)\]]", str(result))
    print("Found coords:", coords)
    
    # If the user result is slightly different (e.g., dict or just string)
    if isinstance(result, tuple) and len(result) >= 2:
        coord_str = result[1]
        better_coords = re.findall(r"([0-9.]+)", str(coord_str))
        print("Better extraction:", better_coords)

if __name__ == "__main__":
    main()
