import httpx
import random


async def get_word_data_from_api(word: str) -> tuple[str, str]:
    """Asynchronous fetch of word data from Free Dictionary API.

    Uses `httpx.AsyncClient` to avoid blocking the bot's event loop.
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()[0]
                meanings = data.get("meanings", [])

                definition = "No definition available."
                example = None

                if meanings:
                    definition = meanings[0]["definitions"][0].get(
                        "definition", definition
                    )
                    for meaning in meanings:
                        for d in meaning.get("definitions", []):
                            if d.get("example"):
                                example = d["example"]
                                break
                        if example:
                            break

                if not example:
                    part_of_speech = (
                        meanings[0].get("partOfSpeech", "word") if meanings else "word"
                    )
                    templates = [
                        f"The teacher asked us to write a sentence with the {part_of_speech} '{word}'.",
                        f"I need to look up how to use '{word}' in a real conversation.",
                        f"Learning the word '{word}' will help you improve your English skills.",
                        f"He tried to remember the definition of '{word}' during the test.",
                    ]
                    example = random.choice(templates)

                return definition, example

    except Exception as e:
        print(f"Ошибка во внешнем API словаря: {e}")

    return "Definition not found.", f"We should study the word '{word}'."
