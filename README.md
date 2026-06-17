# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Given a natural language query, FitFindr searches mock thrift listings, generates outfit suggestions using the user's wardrobe, and produces a shareable fit card caption.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Run the app:
```bash
python app.py
```

Then open `http://127.0.0.1:7860` in your browser.

---

## Tool Inventory

### `search_listings(description, size, max_price)`

**Purpose:** Searches the mock listings dataset for items matching the user's description, filtered by size and price.

**Inputs:**
- `description` (str) — keywords describing the item (e.g. `"vintage graphic tee"`)
- `size` (str | None) — size string to filter by, case-insensitive substring match (e.g. `"M"` matches `"S/M"`); `None` skips size filtering
- `max_price` (float | None) — price ceiling, inclusive; `None` skips price filtering

**Output:** A list of matching listing dicts sorted by relevance (best match first). Each dict has: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Returns `[]` if nothing matches — never raises an exception.

---

### `suggest_outfit(new_item, wardrobe)`

**Purpose:** Given a thrifted item and the user's wardrobe, suggests 1–2 complete outfit combinations using the LLM.

**Inputs:**
- `new_item` (dict) — a listing dict from `search_listings`
- `wardrobe` (dict) — a wardrobe dict with an `items` key containing a list of wardrobe item dicts; may be empty

**Output:** A non-empty string with outfit suggestions (2–3 sentences). If `wardrobe['items']` is empty, returns general styling advice for the item instead of wardrobe-specific pairings. If the LLM call fails, returns an error string starting with `"Could not generate outfit suggestions"`.

---

### `create_fit_card(outfit, new_item)`

**Purpose:** Generates a short, casual Instagram/TikTok-style caption describing the full outfit and thrifted find.

**Inputs:**
- `outfit` (str) — the outfit suggestion string returned by `suggest_outfit`
- `new_item` (dict) — the listing dict for the thrifted item

**Output:** A 1–2 sentence string written in casual first-person tone (Instagram-style caption), mentioning the item name, price, and platform once each. Output varies across calls (temperature=1.0). If `outfit` is empty or whitespace, returns `"Outfit data incomplete — try suggesting the outfit first."` immediately without calling the LLM.

---

## Planning Loop

The agent runs a sequential decision loop — each step only runs if the previous one succeeded.

**Step 1 — Parse query:** The LLM extracts `description`, `size`, and `max_price` from the user's natural language input and stores them in `session["parsed"]`.

**Step 2 — Search:** Calls `search_listings(description, size, max_price)` and stores the result in `session["search_results"]`. If the result is an empty list, the agent sets `session["error"]` to `"No listings found matching your search. Try describing the item differently, increasing your budget, or removing the size filter."` and returns immediately — `suggest_outfit` and `create_fit_card` are never called.

**Step 3 — Select item:** Takes `session["search_results"][0]` (top result by relevance score) and stores it in `session["selected_item"]`.

**Step 4 — Suggest outfit:** Calls `suggest_outfit(session["selected_item"], wardrobe)` and stores the result in `session["outfit_suggestion"]`. If the result starts with `"Could not generate"` or is empty, the agent sets `session["error"]` and returns — `create_fit_card` is never called.

**Step 5 — Fit card:** Calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])` and stores the result in `session["fit_card"]`.

**Step 6 — Return:** Returns the complete session dict. Callers check `session["error"]` first — if it is not `None`, the other output fields are `None`.

---

## State Management

All state for a single interaction lives in a session dict initialized by `_new_session()` in `agent.py`. The dict has these keys:

| Key | Set when | Used by |
|-----|----------|---------|
| `query` | Start | Reference only |
| `parsed` | After LLM query parse | `search_listings` call |
| `search_results` | After `search_listings` | Selecting top item |
| `selected_item` | After top result picked | `suggest_outfit`, `create_fit_card` |
| `wardrobe` | Start | `suggest_outfit` |
| `outfit_suggestion` | After `suggest_outfit` | `create_fit_card` |
| `fit_card` | After `create_fit_card` | Final output |
| `error` | On any failure | Early return check |

The item returned by `search_listings` is stored in `session["selected_item"]` and passed directly into `suggest_outfit` — the user never re-enters it. The string returned by `suggest_outfit` is stored in `session["outfit_suggestion"]` and passed directly into `create_fit_card`.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Returns `[]`; agent sets `session["error"]` to a specific message and stops — `suggest_outfit` is never called with empty input |
| `suggest_outfit` | `wardrobe['items']` is empty | Returns general styling advice (e.g. "This graphic tee pairs well with high-waisted jeans and chunky sneakers") instead of crashing — the interaction continues to `create_fit_card` normally |
| `suggest_outfit` | LLM call raises an exception | Returns `"Could not generate outfit suggestions for this item. (Error: ...)"` — agent sets `session["error"]` and stops |
| `create_fit_card` | `outfit` is empty or whitespace | Returns `"Outfit data incomplete — try suggesting the outfit first."` immediately, no LLM call made |

**Concrete example from testing:**

Running `search_listings("designer ballgown", size="XXS", max_price=5)` returns `[]` — no listings in the dataset match all three constraints. The agent sets:
```
session["error"] = "No listings found matching your search. Try describing the item differently, increasing your budget, or removing the size filter."
session["fit_card"] = None
```
And returns without calling `suggest_outfit` or `create_fit_card`.

Running `create_fit_card("", item)` returns immediately:
```
"Outfit data incomplete — try suggesting the outfit first."
```

---

## Spec Reflection

**One way the spec helped:** Having exact input types and return value shapes defined in `planning.md` before writing any code made it straightforward to test each tool in isolation with hardcoded inputs. For example, knowing `search_listings` must return `[]` (not `None`, not raise) on no results let the agent's error-check be a single `if not session["search_results"]` without defensive wrapping.

**One way implementation diverged:** The planning loop spec didn't specify how to parse the user's natural language query into `description`, `size`, and `max_price`. During implementation, regex was the obvious first approach, but natural language queries vary too much ("under thirty dollars", "$30 max", "budget of 30") to handle reliably with patterns. The implementation uses a Groq LLM call with a structured JSON prompt instead. This adds one extra API call per interaction but handles arbitrary phrasing correctly.

**A second divergence:** The original spec for `create_fit_card` described a "2–4 sentence" caption, but testing showed that output was too long to feel like a real Instagram post — it read more like a product write-up. The prompt and `max_tokens` were tightened to target 1–2 sentences, which better matches the "short, shareable" intent from the project description.

---

## AI Usage

**Instance 1 — Implementing `search_listings`:**
I gave Claude the Tool 1 block from `planning.md` (inputs, return value description, failure mode) and asked it to implement the function using `load_listings()` from the data loader. The generated code filtered by `max_price` and `size` and scored by keyword overlap. I reviewed it and kept the scoring logic as-is, but verified it handled the empty-results case by running three test queries before trusting it. All six pytest tests passed on the first run.

**Instance 2 — Implementing the planning loop:**
I gave Claude the Planning Loop and State Management sections from `planning.md` along with the Architecture diagram and asked it to implement `run_agent()` in `agent.py` following the numbered TODO steps in the file. I reviewed the generated code to confirm it branched on `session["search_results"]` (not calling `suggest_outfit` unconditionally), stored `selected_item` in the session dict before passing it to `suggest_outfit`, and checked for the error prefix from `suggest_outfit` before proceeding to `create_fit_card`. I then ran the built-in CLI test (`python agent.py`) and verified both the happy path and the no-results path behaved as described in `planning.md`.
