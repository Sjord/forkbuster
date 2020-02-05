import httpx
import asyncio

test_files = set()

def filetest(fname):
    def decorator(func):
        test_files.add((fname, func))
        return func
    return decorator

@filetest(".git/HEAD")
def open_git(response):
    return response.content.startswith(b"ref: ")

@filetest(".hg/requires")
def open_hg(response):
    return b"generaldelta" in response.content

@filetest(".well-known/")
def wellknown_index(response):
    return b"Index of /.well-known/" in response.content

async def search_origin(origin):
    with httpx.Client() as client:
        for fname, found_func in test_files:
            url = origin + fname
            if found_func(client.get(url)):
                print(url)
    

async def bust():
    origin_queue = {"https://demo.sjoerdlangkemper.nl/", "https://www.qbit.nl/"}
    found = await asyncio.wait([search_origin(o) for o in origin_queue])


asyncio.get_event_loop().run_until_complete(bust())
