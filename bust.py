import httpx
import asyncio
import sys

test_files = set()

def filetest(fname):
    def decorator(func):
        test_files.add((fname, func))
        return func
    return decorator


class OriginScan:
    def __init__(self, origin):
        assert origin.endswith("/")
        assert origin.startswith("http")
        self.origin = origin
        self.started = False
        self.counter = 0

    @filetest(".git/HEAD")
    def open_git(self, response):
        return response.content.startswith(b"ref: ")

    @filetest(".hg/requires")
    def open_hg(self, response):
        return b"generaldelta" in response.content

    @filetest(".well-known/")
    def wellknown_index(self, response):
        return b"Index of /.well-known/" in response.content

    async def scan(self):
        # with httpx.Client() as client:
        self.started = True
        async with httpx.AsyncClient(http2=True, verify=False) as client:
            for fname, found_func in test_files:
                url = self.origin + fname
                if found_func(self, await client.get(url)):
                    print(url)
                self.counter += 1

    def scan_task(self):
        task = asyncio.create_task(self.scan())
        task.scan_object = self
        return task
        
def show_status(tasks):
    print(chr(27) + "[2J")
    for t in tasks:
        scan = t.scan_object
        if scan.started:
            print(scan.origin, "." * scan.counter)



async def bust(queue):
    tasks = [OriginScan(o.strip()).scan_task() for o in queue]

    while tasks:
        show_status(tasks)
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    show_status(tasks)

with open(sys.argv[1]) as fd:
    asyncio.get_event_loop().run_until_complete(bust(fd))
