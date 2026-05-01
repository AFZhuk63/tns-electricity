import os
from colorama import init, Fore, Style

# Инициализация colorama
init(autoreset=True)


def print_tree_structure(startpath, output_file="structure.txt"):
    IGNORE = {
        '__pycache__', '.git', '.idea', '.venv', '.vscode', 'js',
        'env', '.env.production', 'node_modules', 'setuptools', 'requests-2.32.3.dist-info',
        'python_dateutil-2.9.0.post0.dist-info', 'pytz', 'pkg_resources', 'pip-25.1.1.dist-info', 'pip', 'numpy',
        'series', 'Lib'
    }

    ALLOWED_EXT = {'.py', '.html', '.css', '.js', '.txt', '.json', '.yml', '.sh', '.conf'}
    ALLOWED_FILES = {'Dockerfile', 'docker-compose-dev.yml', 'manage.py'}

    lines = [f"{os.path.basename(startpath)}/"]
    _print_tree(startpath, "", IGNORE, ALLOWED_EXT, ALLOWED_FILES, lines)

    # Вывод в консоль с цветами
    print("СТРУКТУРА ПРОЕКТА:")
    for line in lines:
        if line.endswith("/"):
            print(Fore.YELLOW + line)
        else:
            print(Fore.GREEN + line)

    # Сохраняем в файл (без цветов)
    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def _print_tree(path, prefix, ignore, allowed_ext, allowed_files, lines):
    try:
        entries = sorted(os.listdir(path))
    except Exception:
        return

    entries = [e for e in entries if e not in ignore and not e.startswith('.')]

    for i, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last = i == len(entries) - 1

        if os.path.isdir(full_path):
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{entry}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            _print_tree(full_path, new_prefix, ignore, allowed_ext, allowed_files, lines)
        else:
            ext = os.path.splitext(entry)[1]
            if ext in allowed_ext or entry in allowed_files:
                lines.append(f"{prefix}{'└── ' if is_last else '├── '}{entry}")


if __name__ == "__main__":
    project_path = os.getcwd()
    print_tree_structure(project_path)
