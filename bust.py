import httpx
import asyncio
import sys

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
    assert origin.endswith("/")
    assert origin.startswith("http")

    # with httpx.Client() as client:
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        for fname, found_func in test_files:
            url = origin + fname
            if found_func(await client.get(url)):
                print(url)
    

async def bust(queue):
    found = await asyncio.gather(*[search_origin(o.strip()) for o in queue], return_exceptions=True)

with open(sys.argv[1]) as fd:
    asyncio.get_event_loop().run_until_complete(bust(fd))
