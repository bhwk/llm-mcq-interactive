import os
import json
import aiohttp
import asyncio
from trafilatura import extract

from agentjo import strict_json, strict_json_async
from llm import llm, llm_async

SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY")
CSE_ID = os.environ.get("CSE_ID")

TRUNCATE_SCRAPED_TEXT = 5000  # Adjust based on your model's context window


async def search_web(search_query: str):
    """Searches the web for information related to search_query"""
    response = await strict_json_async(
        "Provide a google search term based on the search query provided. Correct any spelling mistakes.",
        search_query,
        output_format={"Search_term": "The generated search term"},
        llm=llm_async,
    )
    search_term = response["Search_term"]  # type: ignore
    search_items = await search(search_term, SEARCH_API_KEY, CSE_ID)
    results = await get_search_results(search_items, search_term)

    response = await strict_json_async(
        f"""You will be provided with a dictionary of search results in JSON format for search query {search_term}.
        Based on the search results provided, provide a detailed response to this query: **'{search_query}'**.
        Make sure to cite all the sources at the end of your answer.""",
        json.dumps(results),
        output_format={"Summary": "Summary response"},
        llm=llm_async,
    )

    return response["Summary"]  # type: ignore


async def search(search_item, SEARCH_API_KEY, cse_id, search_depth=5, site_filter=None):
    service_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_item,
        "key": SEARCH_API_KEY,
        "cx": cse_id,
        "num": search_depth,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(service_url, params=params) as response:
                results = await response.json()
                if "items" in results:
                    return (
                        [r for r in results["items"] if site_filter in r["link"]]
                        if site_filter
                        else results["items"]
                    )
        except Exception as e:
            print(f"Error during search: {e}")
    return []


async def retrieve_content(session, url, max_tokens=TRUNCATE_SCRAPED_TEXT):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status != 200:
                return None
            text = await response.text()
            extracted_text = extract(
                text, include_comments=False, include_tables=False, favor_precision=True
            )
            return extracted_text[: max_tokens * 4] if extracted_text else None
    except Exception as e:
        print(f"Failed to retrieve {url}: {e}")
    return None


async def summarize_content(content, search_term, character_limit=500):
    prompt = f"Summarize content relevant to '{search_term}' in {character_limit} characters or less."
    try:
        response = await strict_json_async(
            prompt,
            content,
            output_format={"Summary": "Concise summary"},
            llm=llm,
        )
        return response["Summary"]  # type: ignore
    except Exception as e:
        print(f"Summarization error: {e}")
    return None


async def get_search_results(search_items, search_term, character_limit=500):
    results_list = []
    async with aiohttp.ClientSession() as session:
        web_contents = await asyncio.gather(
            *[retrieve_content(session, item.get("link")) for item in search_items],
            return_exceptions=True,
        )
        summaries = await asyncio.gather(
            *[
                summarize_content(content, search_term, character_limit)
                for content in web_contents
                if content
            ],
            return_exceptions=True,
        )

        for idx, (item, summary) in enumerate(zip(search_items, summaries), start=1):
            if isinstance(summary, Exception) or summary is None:
                continue
            results_list.append(
                {
                    "order": idx,
                    "link": item.get("link"),
                    "title": item.get("snippet", ""),
                    "Summary": summary,
                }
            )
    return results_list
