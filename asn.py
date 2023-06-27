import aiohttp
import asyncio
from collections import defaultdict
import sys
from heapq import nlargest

async def get_geoip_data(session, ip_address, retries=3, backoff=5):
    url = f"https://apimon.de/ip/{ip_address}"
    for i in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 504:
                    print(f"\nError: API call failed with status code {response.status}. Retrying...")
                    await asyncio.sleep(backoff)
                else:
                    print(f"\nError: API call failed with status code {response.status}")
                    return None
        except Exception as e:
            print(f"\nError: {e}")
            await asyncio.sleep(backoff)
    return None

def display_top_asns(asn_occurrences, num_top=10):
    sys.stdout.write("\033[K")
    sorted_asns = nlargest(num_top, asn_occurrences, key=asn_occurrences.get)
    lines_printed = 0
    for asn in sorted_asns:
        sys.stdout.write(f"\rASN: {asn}, Occurrences: {asn_occurrences[asn]}\n")
        lines_printed += 1
    return lines_printed

async def main():
    ip_file = "input.txt"

    with open(ip_file, "r") as file:
        ip_addresses = file.readlines()

    asn_occurrences = defaultdict(int)
    total_ips = len(ip_addresses)
    checked_ips = 0
    failed_ips = 0

    async with aiohttp.ClientSession() as session:
        tasks = []
        for ip in ip_addresses:
            ip = ip.strip()
            tasks.append(asyncio.create_task(get_geoip_data(session, ip)))

        for task in asyncio.as_completed(tasks):
            geoip_data = await task
            checked_ips += 1

            if geoip_data:
                asn = geoip_data.get("as", {}).get("number")
                if asn:
                    asn_occurrences[asn] += 1
            else:
                failed_ips += 1

            sys.stdout.write(f"\r[{checked_ips - failed_ips}/{total_ips}] IPs checked\n")
            lines_printed = display_top_asns(asn_occurrences)
            sys.stdout.write("\033[F" * (lines_printed + 1)) 
            sys.stdout.flush()

    print("\n")
    display_top_asns(asn_occurrences)

if __name__ == "__main__":
    asyncio.run(main())