from collections import defaultdict

# source: https://stackoverflow.com/questions/8484943/construct-a-tree-from-list-os-file-paths-python-performance-dependent

FILE_MARKER = '<files>'
FOLDER_MARKER = '<folders>'


def attach(branch, trunk):
    '''
    Insert a branch of directories on its trunk.
    '''
    parts = branch.split('/', 1)
    if len(parts) == 1:  # branch is a file
        if len(parts[0]) != 0:
            trunk[FILE_MARKER].append(parts[0])
    else:
        node, others = parts
        if node not in trunk:
            trunk[node] = defaultdict(dict, ((FILE_MARKER, []),))
        attach(others, trunk[node])


def prettify(d, indent=0):
    '''
    Print the file tree structure with proper indentation.
    '''
    for key, value in d.items():
        if key == FILE_MARKER:
            if value:
                print('  ' * indent + str(value))
        else:
            print('  ' * indent + str(key))
            if isinstance(value, dict):
                prettify(value, indent+1)
            else:
                print('  ' * (indent+1) + str(value))


def generate_tree(paths):
    main_dict = defaultdict(dict, ((FILE_MARKER, []),))

    if isinstance(paths, str):
        for line in paths.split('\n'):
            if len(line) > 0:
                attach(line, main_dict)
    else:
        for line in paths:
            if len(line) > 0:
                attach(line, main_dict)

    return main_dict


def get_folder_content(main_dict, folder_path):
    target_dict = main_dict

    if len(folder_path) > 0:
        parts = folder_path.split('/')
        try:
            for pre_folder in parts:
                if len(pre_folder) > 0:
                    target_dict = target_dict[pre_folder]
        except:
            print("Unreachable folder")

    target_dict_content = {
        FILE_MARKER: [], FOLDER_MARKER: []}

    for key, value in target_dict.items():
        if key == FILE_MARKER:
            target_dict_content[FILE_MARKER] = value
        else:
            target_dict_content[FOLDER_MARKER].append(key)

    return target_dict_content


"""
# Example of utilisation:
paths = '''
dir/file
dir/dir2/file2
dir/file3
dir2/alpha/beta/gamma/delta
dir2/alpha/beta/gamma/delta/
dir3/file4
dir3/file5
'''

main_dict = generate_tree(paths)
print(main_dict)
prettify(main_dict)

content = get_folder_content(main_dict, "dir2/alpha/beta/gamma/delta")
print("\n\n", content)
"""

