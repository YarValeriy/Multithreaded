import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

c_symbols = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ!@$%^&*()-+=:;' "
l_symbols = (
    "a",
    "b",
    "v",
    "g",
    "d",
    "e",
    "e",
    "j",
    "z",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "h",
    "ts",
    "ch",
    "sh",
    "sch",
    "",
    "y",
    "",
    "e",
    "yu",
    "ya",
    "je",
    "i",
    "ji",
    "g",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
    "_",
)

trans = {}
for c, l in zip(c_symbols, l_symbols):
    trans[ord(c)] = l
    trans[ord(c.upper())] = l.upper()


def normalize(string):
    return string.translate(trans)


def process_directory(root, files, categories, folder_path):
    file_moved = {key: [] for key, value in categories.items()}

    for file in files:
        split_name = file.split(".")
        if len(split_name) == 1:
            file_ext = ""
            n_file = normalize(split_name[0])
        else:
            file_ext = split_name[-1].upper()
            n_file = normalize(split_name[0]) + "." + split_name[-1]
        file_path = os.path.join(root, file)

        # Find the category for the file
        file_category = "unknown"
        for category, extensions in categories.items():
            if file_ext in extensions:
                file_category = category
                break
        if file_category == "unknown" and (file_ext not in categories["unknown"]):
            categories["unknown"].append(file_ext)

        # Move the file to the appropriate folder
        destination_folder = os.path.join(folder_path, file_category)
        shutil.move(file_path, os.path.join(destination_folder, n_file))

        if n_file not in file_moved[file_category]:
            file_moved[file_category].append(n_file)

    return file_moved


def unpack_archive(file_path, archive_folder):
    try:
        shutil.unpack_archive(file_path, archive_folder)
        print(f"Archive {file_path} unpacked to {archive_folder}")
        os.remove(file_path)
    except Exception as e:
        print(f"Extraction failed for '{file_path}': {e}")

def sort_files():
    # Define folder names for each category
    categories = {
        "images": ["JPEG", "PNG", "JPG", "SVG", "BMP"],
        "video": ["AVI", "MP4", "MOV", "MKV"],
        "documents": ["DOC", "DOCX", "ODT", "TXT", "PDF", "XLS", "XLSX", "PPT", "PPTX"],
        "audio": ["MP3", "OGG", "WAV", "AMR", "M4A"],
        "archives": ["ZIP", "GZ", "TAR"],
        "code": ["PY", "CPP", "CXX", "CC"],
        "markup": ["XML", "HTML", "CSS"],
        "unknown": [],
    }

    file_moved = {key: [] for key, value in categories.items()}

    if len(sys.argv) < 2:
        folder_path = input("Enter the folder path: ")
    else:
        folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"{folder_path} is not a folder")
        return

    # Create folders if they don't exist
    for category in categories:
        category_folder = os.path.join(folder_path, category)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

    with ThreadPoolExecutor() as executor:
        futures = []

        # Loop through all files and move them to the appropriate folders
        for root, dirs, files in os.walk(folder_path):
            files = [f for f in files if not f[0] == "."]  # skip hidden files
            dirs[:] = [d for d in dirs if not d in list(categories.keys())]  # skip service folders

            futures.append(executor.submit(process_directory, root, files, categories, folder_path))

        for future in futures:
            file_moved_result = future.result()
            for key, value in file_moved_result.items():
                file_moved[key].extend(value)

    # Unpack archive files
    archives_folder = os.path.join(folder_path, "archives")
    with ThreadPoolExecutor() as executor:
        for root, dirs, files in os.walk(os.path.join(folder_path, "archives")):
            for file in files:
                file_path = os.path.join(root, file)
                archive_name = file.split(".")[0]
                # archive_folder = os.path.join(folder_path, "archives", archive_name)
                archive_folder = os.path.join(archives_folder, archive_name)

                # Submit the unpack_archive function to the executor
                executor.submit(unpack_archive, file_path, archive_folder)

    # Remove empty folders
    for root, dirs, _ in os.walk(folder_path, topdown=False):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            sub_dirs = os.listdir(folder_path)
            sub_dirs = [
                sub for sub in sub_dirs if not sub[0] == "."
            ]  # ignore hidden subfolders when deleting folder
            if not sub_dirs:
                shutil.rmtree(folder_path, ignore_errors=True)
                print(f"Empty {folder_path} deleted")

    print(f"Files at {folder_path} sorted successfully")
    print(f"Files moved to new folders based on extensions:")

    for key, value in categories.items():
        if file_moved[key]:
            print(f'{key} {value}:')
            print(f'{file_moved[key]}\n')

    return()


if __name__ == "__main__":
    sort_files()
