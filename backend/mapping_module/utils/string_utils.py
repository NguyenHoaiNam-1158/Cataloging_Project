def reverse_vietnamese_name(full_name: str) -> str:
    if not full_name:
        return ""
    parts = full_name.strip().title().split()
    if len(parts) <= 1:
        return parts[0]
    return f"{parts[-1]}, {' '.join(parts[:-1])}"