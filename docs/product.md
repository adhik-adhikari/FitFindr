# FitFindr Product Requirements

## Document purpose

This document is the product source of truth for the FitFindr MVP. It defines what the product should do, whom it serves, its intended behavior, and its scope. It deliberately does not define architecture, technologies, models, services, or implementation details.

Product decisions may change as FitFindr is built and tested, but changes should be made intentionally by updating this document rather than allowing conflicting assumptions to accumulate elsewhere.

## Product definition

FitFindr is a personal wardrobe assistant that helps users decide what to wear. It turns photos of clothes a user already owns into a digital wardrobe and recommends complete outfits appropriate for the user's situation, preferences, and available clothing.

The product's center of gravity is the question:

> **What should I wear today?**

Garment recognition and wardrobe digitization enable that experience; they are not the end product by themselves.

The core product loop is:

> **Digitize wardrobe → understand garments → recommend useful outfits → let the user act on a recommendation**

## Problem

Many people own enough clothes but still struggle to choose a useful combination for a particular day. They may:

- forget what they own;
- be unsure which colors, patterns, styles, or garment types work together;
- struggle to match an outfit to an occasion or the weather;
- repeatedly wear the same combinations; or
- know roughly what they want to wear but need help choosing the best matching pieces.

FitFindr reduces the effort of making that decision by recommending outfits from the user's existing wardrobe. It should serve both users who want the app to decide for them and users who want to constrain the choice, without requiring separate modes or a burdensome setup.

## Target user

The initial target user is a college student or young professional with an ordinary wardrobe who wants quick, practical help deciding what to wear without buying new clothing.

The target user:

- may not know fashion terminology;
- should not have to enter a long list of garment attributes manually;
- may want either a low-effort answer or more control over a specific request;
- values practical, understandable recommendations over experimental styling; and
- expects to remain in control when FitFindr's interpretation is wrong.

## Product goals

The MVP should:

1. Make it practical to create and maintain a digital wardrobe from individual garment photos.
2. Turn imperfect garment analysis into trustworthy data through user review and correction.
3. Recommend complete, useful outfits made only from garments the user owns and currently has available.
4. Account for occasion/context, explicit requests, personal preferences, weather when available, outfit compatibility, and recent confirmed wear.
5. Explain recommendations and disclose compromises or failures instead of presenting false certainty.
6. Support a fast default flow while allowing users to add more control progressively.
7. Close the loop by letting users confirm what they actually wore.

## Product principles

### The recommendation is the product

Garment analysis should collect only information that helps identify a garment, evaluate compatibility, account for occasion or weather, or explain a recommendation.

### Use the user's existing wardrobe first

MVP recommendations use clothing the user already owns. Shopping and product discovery must not intrude into the core recommendation experience.

### Progressive control

The simplest experience should be effortless: choose an occasion/context and get outfits. Users who want more control can add a free-text request, select a garment to build around, or save preferences. Separate beginner and expert modes are not required.

Persistent preference setup is not part of required onboarding. Preferences remain optional and should be introduced after the user has experienced the core recommendation flow, so users understand their value before being asked to configure them.

### AI proposes; the user decides

Automatically detected garment information is a proposal, not unquestionable truth. Users can review and edit it before saving and change it later. When FitFindr is uncertain, it should use `Unknown` or ask for confirmation rather than fabricate a value.

Garment review should optimize for confirmation rather than data entry. Proposed values should be easy to accept as-is, while corrections remain easy to make. Optional attributes must not create onboarding friction or prevent a garment from being saved when the minimum required information is known.

### Personal preference is not objective fashion truth

FitFindr should recommend what is suitable for this user, not claim that one outfit is objectively correct. Weather and conventional compatibility matter, but strong personal preferences and explicit current requests may outweigh them.

### Transparency over forced success

FitFindr must not silently violate explicit constraints or misrepresent an unsuitable outfit as a good match. When a request cannot be fully satisfied, the product should explain the limitation, show the closest reasonable option when one exists, or return no suitable outfit.

### Prefer useful variety, not novelty at any cost

Recent confirmed wear should encourage rotation when similarly suitable options exist. Repeating an item or outfit remains acceptable when it is still the best choice.

### Keep the MVP focused

A proposed MVP feature should answer this question:

> **Does the first public FitFindr need this to successfully answer “What should I wear today?”**

If not, it should normally remain outside the MVP.

## MVP user journey

1. The user creates an account and has a personal wardrobe.
2. The user uploads or takes a photo containing one garment.
3. FitFindr checks that a supported garment is visible clearly enough to analyze.
4. FitFindr proposes useful garment attributes.
5. The user confirms the proposed values as-is or quickly corrects them, completing only missing minimum required information. Optional attributes do not block progress.
6. The user saves the garment to the wardrobe. In this product flow, **save** means confirming the garment into the user's usable wardrobe after the minimum required information is known. The implementation may temporarily persist an incomplete draft earlier during upload or analysis, but a draft is not a saved wardrobe item and cannot be used in recommendations.
7. FitFindr clearly communicates starter-wardrobe progress, including which garment categories are still needed before recommendations unlock.
8. The user repeats the same flow until the starter wardrobe requirement is met.
9. The user opens **What should I wear?**
10. The user selects a required occasion/context.
11. Optionally, the user adds a natural-language request or chooses a garment to build around.
12. If local weather would improve the recommendation and permission has not already been granted, FitFindr may explain why location is useful and request it at this point. The user can decline or skip and continue without weather.
13. FitFindr considers the user's available wardrobe, any saved preferences, weather when available, and confirmed wear history.
14. FitFindr returns one primary outfit and up to two meaningful alternatives.
15. The user sees the actual garment images, a concise explanation, the context used, and any important compromise or warning.
16. The user can choose **Wear this**, try another outfit, change the request without rebuilding it from scratch, or inspect an item.
17. A confirmed outfit is added to wear history and can influence later recommendations.

Onboarding does not require the user to configure persistent preferences or grant location access. Optional persistent preferences should be introduced after the user has experienced the core recommendation flow.

Users can add more garments and manage their wardrobe at any time. The garment flow remains the same after onboarding: **Photo → analysis → confirm/correct → save**.

## Starter wardrobe requirement

Recommendations unlock when the user has at least:

- **3 available tops**
- **2 available bottoms**
- **2 available pairs of shoes**

Outerwear is optional and does not count toward the minimum.

The threshold creates enough starting variety to make the recommendation experience useful. It does not guarantee that the wardrobe can satisfy every occasion, preference, or request. FitFindr must still decline or qualify a recommendation when the available garments do not form a suitable outfit.

Before the threshold is met, FitFindr must clearly communicate the user's progress and identify the categories still needed. The interface does not have to use literal numeric counters such as `2/3`, but the user should never have to guess why recommendations remain locked or what to add next.

Recommendations use only garments currently marked available. If unavailable items reduce a category below what is needed for a suitable outfit, FitFindr should explain which category is limiting the result.

## Supported MVP outfit and garment scope

A complete MVP outfit contains:

- one top;
- one bottom;
- one pair of shoes; and
- optional outerwear when relevant.

Supported top-level garment categories are:

- tops;
- bottoms;
- shoes; and
- outerwear.

Bottoms include pants, jeans, chinos, shorts, and skirts. Dresses and other one-piece outfits are not supported in the MVP because they replace the top-plus-bottom structure. Accessories and more complex outfit structures are also outside the MVP.

## Garment ingestion and information

### Photo requirement

The MVP supports exactly one garment per uploaded or captured image. A normal phone photo is expected; studio-quality photography is not required. The garment must be visible clearly enough to analyze.

### Minimum information to save and use a garment

The following values must be known before a garment can be saved and used:

| Attribute | Purpose |
|---|---|
| Category | Places the garment in a valid outfit role |
| Type | Identifies the garment more specifically |
| Primary color | Supports identification and color compatibility |

“Required” does not mean the analysis must always infer the value successfully. The user may correct or complete it. A garment may exist temporarily as an implementation-level draft before these values are complete, but only a confirmed garment with the required information is part of the usable wardrobe and eligible for recommendations.

The review experience should make accepting accurate proposed values the fastest path. It should emphasize confirming the garment rather than completing a form. Optional metadata may be reviewed or edited, but it must not add required onboarding work.

### Recommendation metadata when known

The following attributes may be proposed and used when known:

| Attribute | Notes |
|---|---|
| Secondary/accent colors | Optional for multi-color garments |
| Pattern | Examples include solid, striped, plaid, or graphic |
| Formality | A broad, editable suitability description |
| Style tags | Multiple subjective tags may apply |
| Warmth | A broad value such as light, medium, or warm |
| Broad material/fabric | Optional; examples include denim, leather, knit, fleece, or cotton |
| Sleeve length | Applicable to tops and outerwear |
| Neckline/collar | Applicable where useful |
| Broad fit/silhouette | Optional and applicable only where useful |

These fields may remain `Unknown` when they cannot be determined confidently. Exact fabric composition is not required and must not be claimed from visual appearance alone.

### User-controlled information

Users can add:

- optional custom tags for organization;
- an optional free-form note;
- favorite status; and
- available/unavailable status.

Free-form notes do not automatically affect recommendations. A note may contain context unrelated to styling, so it must not be interpreted as a hidden recommendation rule. Favorite status is a soft preference signal, not a guarantee that the item will be selected.

Every relevant detected attribute remains editable both before and after saving. Corrected values should be used in future recommendations.

## Recommendation inputs

### Automatic and required inputs

- The user's currently available garments and their known attributes.
- A valid outfit structure.

### Required per request

The user selects one lightweight **occasion/context**. Initial examples may include Casual, Class, Work, Dinner, Going out, Formal, and Other. If the user selects Other, free text can describe the context.

The exact final list of labels is a later UX/content decision; the product requirement is a small, understandable set rather than a large taxonomy.

### Optional per request

- A free-text request, such as “something comfortable,” “no jeans,” “I want blue,” or “T-shirt and shorts, but help me match them.”
- One specific available wardrobe item to build around.

Temporary exclusions can be expressed through free text in the MVP. A dedicated exclusion selector is not required.

### Optional persistent preferences

Users may save preferences progressively after they have experienced the core recommendation flow. Preference setup is not required during account creation or onboarding. Supported preference types include:

- preferred styles;
- preferred colors;
- colors to avoid;
- a more-casual to more-dressed-up preference; and
- garment-type preferences or avoidances, such as preferring hoodies or avoiding shorts; and
- supported garment-attribute preferences or avoidances, such as preferring long sleeves or avoiding sleeveless tops.

The exact exhaustive set of preference-capable garment attributes remains intentionally undecided. Sleeve length is supported at minimum.

Saved preferences are strong defaults or ranking signals, not absolute prohibitions. An explicit current request can override them without changing the saved preference.

The product remains useful when a user has saved no preferences.

### Weather

When weather and permission to use relevant location context are available, FitFindr should consider current local conditions such as temperature, general conditions, and rain. Weather enhances recommendations but never gates the feature.

Location permission must not be requested as part of account creation or mandatory onboarding. It should be requested contextually when the user is asking for an outfit and weather could improve the result. The request should explain that location is used to consider local weather.

If weather is unavailable or the user declines or skips permission, FitFindr should continue without it and may state that weather was not considered. Season and time of day are not separate required MVP inputs.

## Recommendation priority and conflict rules

FitFindr should first form valid outfits and respect the user's direct intent, then rank the remaining suitable choices. The practical priority order is:

1. **Valid outfit structure and garment availability** — a result must contain the required outfit roles and use only available items.
2. **Explicit current request and selected garment** — today's direct instruction is the strongest expression of user intent. A chosen build-around item or requested garment types act as strong constraints.
3. **Strong saved garment-type and garment-attribute preferences or avoidances** — these personalize normal behavior but can be overridden by an explicit current request.
4. **Occasion/context suitability** — the outfit should honestly match the requested situation.
5. **Weather suitability** — important but advisory and overridable by the user's expressed preferences.
6. **Saved style, color, and dressiness preferences** — used to rank otherwise suitable options.
7. **General outfit compatibility** — color, pattern, style, formality, warmth, and material when known.
8. **Recent confirmed wear history and favorite status** — soft signals that encourage variety while still allowing preferred items and repeats.

When two current instructions directly contradict each other, FitFindr should identify the conflict and ask the user to relax or change one rather than guessing.

When a current request conflicts with a saved preference, the current request wins. When it conflicts with weather, FitFindr may honor the request and show a clear weather note. When the wardrobe cannot satisfy the occasion or an explicit constraint, FitFindr should not silently substitute an unsuitable outfit.

## Recommendation result experience

### Result states

Every result should behave as one of three conceptual states:

1. **Good match** — the wardrobe can satisfy the request well.
2. **Compromise** — a usable outfit exists, but one or more preferences or suitability signals cannot be fully satisfied.
3. **No suitable outfit** — the wardrobe cannot reasonably satisfy the request.

These do not need to be literal labels in the interface, but the distinction must govern product behavior.

### Primary recommendation

The primary recommendation is visually dominant and shows the user's actual uploaded images grouped as an outfit. It identifies the top, bottom, shoes, and optional outerwear.

It includes:

- a short, plain-language reason for the recommendation;
- a lightweight summary of relevant context used, such as occasion, weather, preferences, or the current request;
- a clear indication when the outfit was built around a selected item;
- any meaningful compromise or weather warning; and
- an optional expandable **Why this outfit?** explanation tied to factors that actually influenced the selection.

The product must not present arbitrary compatibility or fashion scores with fake precision.

### Alternatives

FitFindr shows up to two alternatives beneath the primary recommendation. Alternatives should be meaningfully different when the wardrobe allows it, not minor variations added merely to fill space.

“Up to” is intentional: show one result if only one is suitable, two if only two are suitable, and no result when none is suitable. Recommendation quality must not be weakened to fill three cards.

### Result actions

The MVP provides these actions:

| Action | Behavior |
|---|---|
| **Wear this** | Confirms that the user chose the outfit and records it in wear history |
| **Try another** | Requests another suitable combination |
| **Change request** | Returns to the inputs without forcing the user to rebuild the request from scratch |
| **View item** | Opens a garment for inspection or management |

If the user marks an item unavailable from the recommendation flow, they should be able to get another recommendation using the same request.

### Compromises and failure

A compromise result must state what could not be satisfied and describe the result as the closest reasonable match. A no-result state must explain the limiting factor and offer relevant next actions, such as changing the request or managing the wardrobe.

Shopping suggestions do not appear in MVP failure states.

## Wardrobe management

The wardrobe should help users understand what FitFindr thinks they own, correct it, and control what is eligible for recommendations.

### Wardrobe browsing

The default wardrobe is visual and organized primarily by:

- All;
- Tops;
- Bottoms;
- Shoes; and
- Outerwear.

A garment card shows the image, type, primary color, and an unavailable indicator when applicable. Full metadata belongs in the garment detail view rather than the grid.

MVP filters include category, color, type, and availability. Text search is not required for the core MVP.

### Garment detail and management

Users can:

- view the original image and all known garment information;
- edit detected and user-provided attributes;
- add or change custom tags and a note;
- mark or unmark the garment as a favorite;
- mark it available or unavailable;
- delete it with confirmation; and
- add new garments at any time.

Unavailable means the garment stays in the wardrobe but is excluded from recommendations. This represents recommendation availability only; FitFindr does not manage laundry cycles.

The wardrobe may show basic counts by category and a useful warning when low availability is likely to limit outfit variety. It should not invent a wardrobe-quality score or pressure the user to buy clothing.

## Wear history and variety

An outfit enters wear history only when the user explicitly chooses **Wear this**. Displaying or generating an outfit does not count as wearing it.

The MVP includes a basic view of confirmed recently worn outfits. Recent outfits and items act as soft diversity signals:

- prefer a different similarly suitable option when one exists;
- allow repetition when the wardrobe is small or the repeated option is clearly better; and
- never create a poor or strange outfit solely to avoid repetition.

History represents what the user confirmed, not guaranteed real-world behavior. If the user forgets to confirm or later wears something else, FitFindr does not infer or silently alter the record.

Deleting a garment should not necessarily erase past wear records. A historical entry may retain the garment as an item no longer in the wardrobe. Exact history correction behavior can be decided later.

## Edge cases and required behavior

### Photo and upload problems

| Situation | Required behavior |
|---|---|
| No garment is clearly visible | Ask for another photo |
| Multiple garments are visible | Explain that the MVP supports one garment per photo |
| Image is too dark or blurry | Explain that analysis is unreliable and ask for another photo |
| Garment is partly cut off | Continue only if it can be analyzed confidently; otherwise ask for another image |
| Background is busy | Attempt analysis, but request a clearer photo if extraction is unreliable |
| Uploaded object is not a supported garment | Explain that a supported garment was not detected |
| An attribute is uncertain | Use `Unknown` or ask the user to confirm; do not invent a value |

### Incorrect classification

All detected values remain editable before and after saving. Subjective fields such as style and formality should be presented as FitFindr's interpretation, not objective fact.

### Duplicate-looking garments

FitFindr must not automatically delete apparent duplicates because a user may own two identical items. Automatic duplicate detection or warnings are not required for the MVP; users can remove accidental duplicates themselves.

### Unsupported garments

FitFindr should clearly state when a garment category is not supported or is not used in recommendations. It must not pretend to support dresses, accessories, or other excluded structures.

### Insufficient or unsuitable wardrobe

Meeting the starter threshold does not guarantee a valid recommendation for every request. If the wardrobe lacks suitable options, FitFindr should explain the limiting category or suitability problem rather than forcing a combination.

### Unavailable build-around item

If the selected build-around garment is unavailable, FitFindr should flag the conflict and ask the user to mark it available or choose another item. It must not silently ignore either state.

### Conflicting constraints

FitFindr should identify direct contradictions such as “no jeans” and “use my black jeans” and ask the user to change one of them. It should not guess or return a random result.

### Weather unavailable or contrary to preference

Recommendations continue when weather is unavailable. When an explicit request or strong preference is unusual for current conditions, FitFindr may honor it and provide a lightweight comfort warning rather than block the user.

### Fewer than three suitable outfits

FitFindr returns only the number of suitable outfits available, including zero. It does not lower its standards to produce a primary recommendation and two alternatives.

## MVP scope

The MVP includes:

- user accounts and a personal wardrobe;
- uploading or capturing one garment per photo;
- proposed garment attributes with a confirmation-first review and correction flow;
- the starter wardrobe requirement with clear progress and missing-category guidance;
- supported categories of tops, bottoms, shoes, and outerwear;
- a visual wardrobe with category browsing and basic filters;
- garment detail, editing, deletion, favorites, tags, notes, and availability;
- basic wardrobe counts and useful availability warnings;
- optional persistent style, color, dressiness, garment-type, and garment-attribute preferences or avoidances introduced after the core recommendation flow;
- a required occasion/context for each recommendation;
- an optional free-text request;
- an optional build-around garment;
- contextual, skippable location permission and weather consideration when available;
- a primary complete outfit plus up to two alternatives;
- concise explanations, actual context used, and honest compromise or failure messaging;
- **Wear this** confirmation;
- basic confirmed wear history; and
- variety influenced by recent confirmed wear.

## Explicitly out of scope for the MVP

### Additional garment and outfit structures

- dresses and other one-piece outfits;
- accessories, hats, bags, jewelry, and scarves;
- complex formalwear structures; and
- multi-garment extraction from one photo.

### Advanced wardrobe organization and management

- complex collections or folders;
- seasonal organization and clothing archives;
- advanced duplicate detection;
- automatic laundry or clean/dirty tracking;
- closet shelf or drawer location;
- purchase receipts, prices, or wardrobe monetary value;
- cost-per-wear and advanced analytics;
- resale, lending, or sustainability scoring; and
- packing lists.

### Advanced recommendation and personalization features

- dedicated like/dislike learning;
- “never recommend this combination again” feedback;
- favorite outfit collections;
- sophisticated preference learning;
- tomorrow, weekly, calendar-based, or travel outfit planning;
- dedicated temporary item-exclusion controls; and
- explicit season or time-of-day inputs.

### Shopping and discovery

- retailer or product discovery;
- pricing, stock, sizing, or shopping links;
- sponsored recommendations; and
- suggestions to buy products inside the core MVP recommendation flow.

### Visualization and social features

- generic mannequin previews;
- personalized virtual try-on;
- body representations or body analysis;
- public wardrobes or profiles;
- follows, feeds, comments, likes, or influencer features; and
- social outfit sharing.

## Post-MVP roadmap

The roadmap describes directions, not committed releases or dates.

### Better personalization

- richer recommendation feedback;
- stronger learning from confirmed wear and expressed preferences;
- favorite combinations;
- more garment categories; and
- improved outfit-history controls.

### Better wardrobe organization

- search;
- advanced filters;
- collections;
- seasonal organization;
- archiving; and
- user-controlled duplicate warnings.

### Recommendation planning

- tomorrow's outfit;
- weekly or calendar-based planning; and
- travel and packing recommendations.

### Visualization

- generic mannequin or outfit previews; and
- potentially, much later, personalized virtual try-on with explicit attention to privacy, garment fidelity, body representation, and user expectations.

### Wardrobe intelligence

- identify wardrobe gaps;
- assess versatility without fake precision;
- show which additions would unlock useful combinations; and
- provide richer planning insights.

### Wardrobe-aware clothing discovery

Recommend new pieces that complement what the user already owns. This is a separate future product phase because it introduces product discovery, retailer information, price, availability, sizing, and shopping concerns.

## Explicit product limitations

The FitFindr MVP:

- supports one garment per uploaded image;
- uses only supported garment categories and the top + bottom + shoes + optional outerwear structure;
- cannot determine whether clothing physically fits the user;
- does not determine body type or judge the user's body or appearance;
- does not require body measurements, face analysis, or full-body photos;
- cannot guarantee exact fabric or material composition from a normal garment photo;
- cannot guarantee that an outfit will feel comfortable in the weather;
- cannot guarantee that an outfit is fashionable;
- does not make objective judgments about personal style;
- does not replace the user's own preferences;
- may work without weather or location context;
- depends on wardrobe variety and the accuracy of garment information; and
- may return fewer than three recommendations or no recommendation when suitable outfits are unavailable.

Recommendations are informed suggestions, not objective fashion judgments.

## Intentionally undecided details

The following do not need to be fixed before implementation and should not be mistaken for missing product requirements:

- the complete list of garment subtypes;
- the exact list of style and formality labels;
- the exact number of days considered “recently worn”;
- the exact weighting among favorites, preferences, weather, compatibility, and recent wear;
- final interface copy and error-message wording;
- whether and how a user corrects past wear-history entries; and
- whether search or image replacement is included as a small MVP enhancement.

These decisions may be refined through design and product testing as long as they preserve the requirements and principles above.
