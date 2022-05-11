import os

import pdf2image


def rename_images(paths: list[str]) -> None:
    """
    Rename image files, this removes prefix like
    dir/0001-1.png -> dir/1.png
    """
    for path in paths:
        dir, file_name = os.path.split(path)
        new_file_name = file_name.split("-")[1]
        os.rename(path, os.path.join(dir, new_file_name))


def pdf_to_png(path: str, task_id: str, data_dir: str, max_size: tuple[int, int]):
    output_folder = os.path.join(data_dir, task_id)
    try:
        os.mkdir(output_folder)
    except FileExistsError:
        pass

    image_paths = pdf2image.convert_from_path(
        path,
        output_folder=output_folder,
        fmt="png",
        output_file="",
        paths_only=True,
        # this won't keep aspect ratio, but the assignment is to get it into rectangle 1200, 1600
        # if we should keep the aspect ratio we could check pdfinfo, read page size and decide
        # to which dimension to scal
        size=max_size,
        # for better performance
        use_pdftocairo=True,
    )
    rename_images(image_paths)
    return image_paths
