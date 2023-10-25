def increment_version(version_str, part='patch'):
    parts = version_str.split(".")
    if part == 'patch':
        parts[2] = str(int(parts[2]) + 1)
    elif part == 'minor':
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = "0"
    elif part == 'major':
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = "0"
        parts[2] = "0"
    else:
        raise ValueError("Invalid 'part' argument. Use 'patch', 'minor', or 'major'.")

    return ".".join(parts)
