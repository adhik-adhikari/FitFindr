"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from tools import search_listings, suggest_outfit, create_fit_card

load_dotenv()


def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


def _parse_query(query: str) -> dict:
    """
    Use the LLM to extract description, size, and max_price from a natural
    language query. Returns a dict with keys: description, size, max_price.
    Falls back to the full query as description if parsing fails.
    """
    prompt = (
        "Extract search parameters from this clothing query. "
        "Return ONLY a JSON object with exactly these keys:\n"
        '  "description": string (item keywords only, no size or price),\n'
        '  "size": string or null (e.g. "M", "S/M", "W30" — null if not mentioned),\n'
        '  "max_price": number or null (max price as a float — null if not mentioned).\n\n'
        f"Query: {query}\n\nJSON:"
    )
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        text = response.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return {
                "description": parsed.get("description", query),
                "size": parsed.get("size") or None,
                "max_price": float(parsed["max_price"]) if parsed.get("max_price") else None,
            }
    except Exception:
        pass
    return {"description": query, "size": None, "max_price": None}


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query → extract description, size, max_price
    session["parsed"] = _parse_query(query)
    description = session["parsed"]["description"]
    size = session["parsed"]["size"]
    max_price = session["parsed"]["max_price"]

    # Step 3: Search listings — stop early if nothing found
    session["search_results"] = search_listings(description, size=size, max_price=max_price)
    if not session["search_results"]:
        session["error"] = (
            "No listings found matching your search. Try describing the item "
            "differently, increasing your budget, or removing the size filter."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = session["search_results"][0]

    # Step 5: Suggest outfit — stop early if it fails
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)
    if not session["outfit_suggestion"] or session["outfit_suggestion"].startswith("Could not generate"):
        session["error"] = session["outfit_suggestion"] or "Could not generate outfit suggestions for this item."
        session["outfit_suggestion"] = None
        return session

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])

    # Step 7: Return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
