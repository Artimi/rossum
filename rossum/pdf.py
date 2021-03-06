from typing import Any
import os

import dramatiq
import dramatiq.brokers.stub
import dramatiq.brokers.redis
import pdf2image

if os.getenv("UNIT_TESTS") == "1":
    broker = dramatiq.brokers.stub.StubBroker()
    broker.emit_after("process_boot")
else:
    broker = dramatiq.brokers.redis.RedisBroker(host="redis")
dramatiq.set_broker(broker)


def rename_images(paths: list[str]) -> None:
    """
    Rename image files, this removes prefix like
    dir/0001-1.png -> dir/1.png
    """
    for path in paths:
        dir, file_name = os.path.split(path)
        new_file_name = file_name.split("-")[1]
        os.rename(path, os.path.join(dir, new_file_name))


@dramatiq.actor(max_retries=3)
def pdf_to_png(path: str, document_id: str, data_dir: str, max_size: tuple[int, int]) -> None:
    '''
    Convert pdf at `path` to a series of png images stored in `data_dir`/`document_id`.
    Each image will be of a size `max_size`.
    '''
    output_folder = os.path.join(data_dir, document_id)
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
        # to which dimension to scale
        size=tuple(max_size),
        # for better performance
        use_pdftocairo=True,
    )
    rename_images(image_paths)


def pdf_info(path: str) -> dict[str, Any]:
    return pdf2image.pdfinfo_from_path(path)
