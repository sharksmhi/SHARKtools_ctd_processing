import pathlib
import os
import traceback


def get_files_in_directory(directory, suffix=None):
    files = []
    directory = pathlib.Path(directory)
    if not directory.exists():
        return []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        if suffix and suffix != path.suffix:
            continue
        files.append(path.name)
    get_files_in_directory.counter.setdefault(directory, 0)
    get_files_in_directory.counter[directory] += 1
    print()
    print()
    print('='*50)
    stack = []
    for line in traceback.format_stack():
        text = line.strip().replace('\n', ' ')
        if 'page_start' not in text:
            continue
        split_text = text.split(',')
        line = split_text[1].split()[-1]
        fn = split_text[2].split()[1]
        stack.append(fn)
    stack.append(directory.name)
    get_files_in_directory.counter.setdefault('stack', [])
    get_files_in_directory.counter['stack'].append(' -> '.join(stack))
    print('='*50)
    print('get_files_in_directory')
    print('='*50)
    for key, value in get_files_in_directory.counter.items():
        if key == 'stack':
            print('STACK')
            for val in value:
                print(f'    {val}')
        else:
            print(f'{key=}, {value=}')
    print('-'*50)
    print()
    print()
    print()

    return files


get_files_in_directory.counter = {}


def open_path_in_default_program(path):
    os.startfile(str(path))


def open_paths_in_default_program(paths):
    for path in paths:
        open_path_in_default_program(path)


class ColorsList(list):

    def __init__(self):
        list.__init__(self)
        for color in sorted(self.get_base_colors() + self.get_tableau_colors() + self.get_css4_colors()):
            self.append(color)

    def _filter_color_list(self, color_list):
        new_color_list = []
        for color in color_list:
            if color.startswith('tab:'):
                continue
            if len(color) == 1:
                continue
            new_color_list.append(color)
        return sorted(new_color_list)

    def get_base_colors(self):
        return self._filter_color_list(mcolors.BASE_COLORS)

    def get_tableau_colors(self):
        return self._filter_color_list(mcolors.TABLEAU_COLORS)

    def get_css4_colors(self):
        return self._filter_color_list(mcolors.CSS4_COLORS)


class MarkerList(list):
    def __init__(self):
        list.__init__(self)
        temp_list = markers.MarkerStyle.markers.keys()
        self.marker_to_description = {}
        self.description_to_marker = {}
        for marker in temp_list:
            description = str(markers.MarkerStyle.markers[marker])
            marker = str(marker)
            self.marker_to_description[marker] = description
            self.description_to_marker[description] = marker

        for marker in sorted(self.marker_to_description.keys()):
            self.append(marker)

    def get_description(self, marker):
        return self.marker_to_description.get(marker, marker)

    def get_marker(self, description):
        return self.description_to_marker.get(description, description)