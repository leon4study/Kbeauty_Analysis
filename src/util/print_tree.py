import os

def print_tree(directory, prefix=""):
    """디렉터리 구조를 트리 형태로 출력"""
    files = os.listdir(directory)
    files.sort()  # 알파벳 순 정렬
    for index, file in enumerate(files):
        path = os.path.join(directory, file)
        is_last = index == len(files) - 1  # 마지막 항목 여부
        print(f"{prefix}{'└ ' if is_last else '├ '}{file}")
        if os.path.isdir(path):
            new_prefix = prefix + ("   " if is_last else "│  ")
            print_tree(path, new_prefix)