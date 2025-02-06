import os
import requests
import json
from bs4 import BeautifulSoup

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
    search_items = search(
        search_item=search_term, SEARCH_API_KEY=SEARCH_API_KEY, cse_id=CSE_ID
    )
    results = get_search_results(search_items, search_term)

    response = strict_json(
        f"""You will be provided with a dictionary of search results in JSON format for search query {search_term}.
        Based on on the search results provided, provide a detailed response to this query: **'{search_query}'**.
        Make sure to cite all the sources at the end of your answer.""",
        json.dumps(results),
        output_format={"Summary": "Summary response"},
        llm=llm
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

        # Check if 'items' exists in the results
        if "items" in results:
            if site_filter is not None:
                # Filter results to include only those with site_filter in the link
                filtered_results = [
                    result
                    for result in results["items"]
                    if site_filter in result["link"]
                ]

                if filtered_results:
                    return filtered_results
                else:
                    print(f"No results with {site_filter} found.")
                    return []
            else:
                if "items" in results:
                    return results["items"]
                else:
                    print("No search results found.")
                    return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the search: {e}")
        return []



def retrieve_content(url, max_tokens=TRUNCATE_SCRAPED_TEXT):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text(separator=" ", strip=True)
        characters = max_tokens * 4  # Approximate conversion
        text = text[:characters]
        return text
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None


def summarize_content(content, search_term, character_limit=500):
    prompt = (
        f"You are an AI assistant tasked with summarizing content relevant to '{search_term}'. "
        f"Please provide a concise summary in {character_limit} characters or less."
    )
    try:
        response = strict_json(
            prompt, content, output_format={"Summary": "Concise summary"}, llm=llm
        )
        summary = response["Summary"]  # type: ignore
        return summary
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return None


def get_search_results(search_items, search_term, character_limit=500):
    # Generate a summary of search results for the given search term
    results_list = []
    for idx, item in enumerate(search_items, start=1):
        url = item.get("link")

        snippet = item.get("snippet", "")
        web_content = retrieve_content(url, TRUNCATE_SCRAPED_TEXT)

        if web_content is None:
            print(f"Error: skipped URL: {url}")
        else:
            summary = summarize_content(web_content, search_term, character_limit)
            result_dict = {
                "order": idx,
                "link": url,
                "title": snippet,
                "Summary": summary,
            }
            results_list.append(result_dict)
    return results_list
