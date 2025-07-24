import os
import csv

def get_base_filenames(folder):
    """Return a set of filenames (without extension) from the given folder."""
    return set(
        os.path.splitext(f)[0]
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    )

def main():
    base_path = input("Enter the full path to the base folder: ").strip()
    if not os.path.isdir(base_path):
        print(f"Error: '{base_path}' is not a valid folder.")
        return

    base_folder_name = os.path.basename(base_path)
    parent_dir = os.path.dirname(base_path)

    # Find sibling folders that start with the same base name
    all_folders = [
        f for f in os.listdir(parent_dir)
        if os.path.isdir(os.path.join(parent_dir, f)) and f.startswith(base_folder_name)
    ]

    if not all_folders:
        print(f"No folders starting with '{base_folder_name}' were found in {parent_dir}.")
        return

    print(f"\nFound folders: {', '.join(all_folders)}")

    # Collect filenames from each folder
    folder_file_map = {}
    for folder in all_folders:
        folder_path = os.path.join(parent_dir, folder)
        folder_file_map[folder] = get_base_filenames(folder_path)

    sorted_folders = sorted(folder_file_map.keys())
    all_filenames = set().union(*folder_file_map.values())
    shared_files = set.intersection(*(folder_file_map[f] for f in sorted_folders))

    # Filenames not in all folders
    not_shared = sorted(all_filenames - shared_files)

    # --- Summary ---
    print("\n--- Summary ---")
    print(f"Total unique filenames (ignoring extension): {len(all_filenames)}")

    for folder in sorted_folders:
        own = folder_file_map[folder]
        others = set().union(*(folder_file_map[f] for f in sorted_folders if f != folder))
        unique_to_folder = own - others
        print(f"{folder}:")
        print(f"  - Total files: {len(own)}")
        print(f"  - Unique to this folder: {len(unique_to_folder)}")

    print(f"\nFilenames NOT present in all folders ({len(not_shared)}):")
    for name in not_shared:
        print(f"  - {name}")

    # --- Ask to create CSV ---
    user_choice = input("\nWould you like to create a CSV file with this comparison? (y/n): ").strip().lower()
    if user_choice == "y":
        csv_filename = os.path.join(parent_dir, f"{base_folder_name}_file_comparison.csv")
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = ["filename", "supplied_directory"] + sorted_folders
            writer.writerow(header)

            for filename in sorted(all_filenames):
                row = [filename, base_folder_name]
                for folder in sorted_folders:
                    row.append(1 if filename in folder_file_map[folder] else 0)
                writer.writerow(row)

        print(f"\n✅ CSV written to: {csv_filename}")
    else:
        print("\nNo CSV was created.")

if __name__ == "__main__":
    main()
