import os
import requests
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from trafilatura import extract

from agentjo import strict_json
from llm import llm

SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY")
CSE_ID = os.environ.get("CSE_ID")

TRUNCATE_SCRAPED_TEXT = 5000  # Adjust based on your model's context window


def search_web(search_query: str):
    """Searches the web for information related to search_query"""
    response = strict_json(
        "Provide a google search term based on the search query provided. Correct any spelling mistakes.",
        search_query,
        output_format={"Search_term": "The generated search term"},
        llm=llm,
    )
    search_term = response["Search_term"]  # type: ignore
    search_items = search(search_term, SEARCH_API_KEY, CSE_ID)
    results = asyncio.run(get_search_results(search_items, search_term))

    response = strict_json(
        f"""You will be provided with a dictionary of search results in JSON format for search query {search_term}.
        Based on the search results provided, provide a detailed response to this query: **'{search_query}'**.
        Make sure to cite all the sources at the end of your answer.""",
        json.dumps(results),
        output_format={"Summary": "Summary response"},
        llm=llm,
    )

    summary = response["Summary"]  # type: ignore
    return summary


def search(search_item, SEARCH_API_KEY, cse_id, search_depth=5, site_filter=None):
    service_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_item,
        "key": SEARCH_API_KEY,
        "cx": cse_id,
        "num": search_depth,
    }

    try:
        response = requests.get(service_url, params=params)
        response.raise_for_status()
        results = response.json()

        if "items" in results:
            if site_filter:
                return [r for r in results["items"] if site_filter in r["link"]]
            return results["items"]

    except requests.exceptions.RequestException as e:
        print(f"Error during search: {e}")
    return []


async def retrieve_content(session, url, max_tokens=TRUNCATE_SCRAPED_TEXT):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status != 200:
                return None
            text = await response.text()
            extracted_text = extract(text, include_comments=False, include_tables=False)
            return extracted_text[: max_tokens * 4] if extracted_text else None
    except Exception as e:
        print(f"Failed to retrieve {url}: {e}")
    return None


def summarize_content(content, search_term, character_limit=500):
    prompt = f"Summarize content relevant to '{search_term}' in {character_limit} characters or less."
    try:
        response = strict_json(
            prompt, content, output_format={"Summary": "Concise summary"}, llm=llm
        )
        return response["Summary"]  # type: ignore
    except Exception as e:
        print(f"Summarization error: {e}")
    return None


async def get_search_results(search_items, search_term, character_limit=500):
    results_list = []
    async with aiohttp.ClientSession() as session:
        tasks = [retrieve_content(session, item.get("link")) for item in search_items]
        web_contents = await asyncio.gather(*tasks)

        for idx, (item, web_content) in enumerate(
            zip(search_items, web_contents), start=1
        ):
            url = item.get("link")
            snippet = item.get("snippet", "")

            if web_content:
                summary = summarize_content(web_content, search_term, character_limit)
                results_list.append(
                    {
                        "order": idx,
                        "link": url,
                        "title": snippet,
                        "Summary": summary,
                    }
                )
            else:
                print(f"Skipped URL due to retrieval failure: {url}")
    return results_list
