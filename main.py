import json
import asyncio
import aiohttp
from os import listdir
from os.path import isfile, isdir, join, basename, dirname, splitext
from bs4 import BeautifulSoup
from contextlib import closing

BASE_DIR = '/Users/mikhailmustakimov/Downloads/Archive/messages'


def get_attachment_image_links_from_document(html_doc: str) -> list:
    soup = BeautifulSoup(html_doc, 'html.parser')
    link_tags = soup.find_all("a", class_="attachment__link")
    links = [tag['href'] for tag in link_tags if tag['href'].find('.jpg') != -1]
    return links


def get_all_files_from_directory(path: str, ext: list) -> list:
    return [join(path, f) for f in listdir(path) if isfile(join(path, f)) and splitext(join(path, f))[1] in ext]


def get_all_dirs_from_directory(path: str) -> list:
    return [join(path, f) for f in listdir(path) if isdir(join(path, f))]


def walk_dialog_directory(dir_path: str) -> list:
    files = get_all_files_from_directory(dir_path, ['.html'])
    result = []
    for file in files:
        f = open(file, encoding='windows-1251')
        try:
            content = '\n'.join(f.readlines())
            result.extend(get_attachment_image_links_from_document(content))
        except Exception as e:
            print('Error in file ' + file)
        finally:
            f.close()
    return result


def walk_messages_directory(base_dir: str) -> dict:
    result = {}
    dirs = get_all_dirs_from_directory(base_dir)
    for i, path in enumerate(dirs):
        print('Processing dialog ' + str(i) + ' out of ' + str(len(dirs)))
        id = basename(dirname(path + '/'))
        imgs = walk_dialog_directory(path)
        if len(imgs) > 0:
            result[id] = imgs
    return result


async def download_file(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        assert response.status == 200
        # For large files use response.content.read(chunk_size) instead.
        return await response.read()


@asyncio.coroutine
def download_multiple(session: aiohttp.ClientSession, urls: list):
    download_futures = [download_file(session, url) for url in urls]
    results = []
    for download_future in asyncio.as_completed(download_futures):
        response = yield from download_future
        results.append(response)
    return results


def download_images(obj: dict):
    with closing(asyncio.get_event_loop()) as loop:
        with aiohttp.ClientSession() as session:
            for id, urls in obj.items():
                result = loop.run_until_complete(download_multiple(session, ))
                print('finished:', result)


def main():
    result = walk_messages_directory(BASE_DIR)
    f = open('result.json', 'w')
    json.dump(result, f)
    f.close()


if __name__ == '__main__':
    main()
