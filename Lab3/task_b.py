import asyncio
import random
from googletrans import Translator, LANGUAGES


async def translation_loop(text: str, num_languages: int = 10, languages: list[str] = None):
    """
    Pass text through a sequence of translations using googletrans (async).
    """
    async with Translator() as translator:
        sequence = []

        # Select random languages if not provided
        available_langs = list(LANGUAGES.keys())
        # print(available_langs)
        available_langs.remove("en")

        if languages is None:
            chosen_langs = random.sample(available_langs, num_languages)
        else:
            chosen_langs = languages

        current_text = text
        current_lang = "en"

        # Sequentially translate through chosen languages
        for i, lang in enumerate(chosen_langs, start=1):
            try:
                print(f"Step {i}: {LANGUAGES[current_lang]} → {LANGUAGES[lang]}")
                translation = await translator.translate(current_text, src=current_lang, dest=lang)
                new_text = translation.text
                sequence.append((LANGUAGES[lang], new_text))
                current_text, current_lang = new_text, lang
                print(f"   Result: {new_text}\n")
            except Exception as e:
                print(f"Error translating {current_lang} → {lang}: {e}")
                break

        # Translate back to English
        print("Translating back to English...\n")
        try:
            final_translation = await translator.translate(current_text, src=current_lang, dest="en")
            final_text = final_translation.text
        except Exception as e:
            print(f"Error returning to English: {e}")
            final_text = current_text

        print(f"Original: {text}")
        print(f"Final:    {final_text}\n")

        return {
            "original": text,
            "final": final_text,
            "sequence": sequence,
            "languages": chosen_langs
        }


if __name__ == "__main__":
    text = "Catherine decides to make an overture of goodwill by offering up Margot in marriage to prominent Huguenot and King of Navarre, Henri de Bourbon, which is supposed to cement the hard-fought Peace of Saint-Germain. At the same time, Catherine schemes to bring about the notorious St. Bartholomew's Day Massacre of 1572 and assassinate many of the most wealthy and prominent Huguenots, who are in the largely-Catholic city of Paris to escort the Protestant prince to his wedding. The massacre begins four days after the wedding ceremony, and thousands of Protestants are slaughtered. The marriage goes ahead, but Margot, who does not love Henri, begins a passionate affair with the soldier La Môle, also a Protestant from a well-to-do family."
    asyncio.run(translation_loop(text, num_languages=10,languages=['bem', 'haw', 'hmn', 'kri', 'mfe', 'mni-mtei', 'nus', 'tiv', 'yua', 'lus']))
