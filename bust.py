import httpx
import asyncio
import sys


class FileTest:
    def __init__(self, origin):
        self.origin = origin
        self.url = self.origin + self.path

    def get_result(self, response):
        if self.check_response(response):
            return (self.url, type(self).__name__)
        return None


class OpenGit(FileTest):
    path = ".git/HEAD"

    def check_response(self, response):
        return response.content.startswith(b"ref: ")


class OpenMercural(FileTest):
    path = ".hg/requires"

    def check_response(self, response):
        return b"generaldelta" in response.content


class WellKnownIndex(FileTest):
    path = ".well-known/"

    def check_response(self, response):
        return b"Index of /.well-known/" in response.content


class OriginScan:
    def __init__(self, origin):
        assert origin.endswith("/")
        assert origin.startswith("http")
        self.origin = origin
        self.tests = [t(origin) for t in FileTest.__subclasses__()]

    async def scan(self):
        # with httpx.Client(verify=False) as client:
        async with httpx.AsyncClient(http2=True, verify=False) as client:
            return [test.get_result(await client.get(test.url)) for test in self.tests]


def show_status(todo, total):
    percentage = 100 * (total - todo) / total
    print("%.1f" % percentage, "%", end="\r")


def print_results(task):
    exc = task.exception()
    if exc is not None:
        print("X", str(exc) or type(exc).__name__)
        return

    results = filter(None, task.result())
    for r in results:
        print("!", r)


async def bust(queue):
    tasks = [OriginScan(o.strip()).scan() for o in queue]
    total = len(tasks)
    done = []

    while tasks:
        show_status(len(tasks), total)
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            print_results(task)

    show_status(len(tasks), total)


with open(sys.argv[1]) as fd:
    asyncio.get_event_loop().run_until_complete(bust(fd))
