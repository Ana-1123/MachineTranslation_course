import random
import re

lexicon = {
    "om": "biped",
    "oameni": "bipede",
    "student": "puiuț de om studios",
    "cercetător": "căutător de conserve",
    "lucrare": "miau-lucrare",
    "studiu": "miau-studiu",
    "analizează": "toarce asupra",
    "concluzie": "miorlăială finală",
    "energie": "vibrație de coadă",
    "tehnologie": "jucărie electronică",
    "comunicare": "miorlăială între bipede",
}

interj = ["Purr,", "Miau,", "Zzz,", "Prrr,"]
closings = [
    "purr-fect concluzie.",
    "miau-concluzionez cu grație.",
    "și-am toarce-semnat rezultatul.",
    "ah, ce satisfacție științifică în blăniță!",
]

def romanian_to_pisicesc(text):
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    output_sentences = []

    for s in sentences:
        if not s:
            continue
        s = s.strip()

        # Rule 1 - one of the interjections at the start
        intro = random.choice(interj)
        # Capitalize first letter if missing
        s = s[0].upper() + s[1:]
        s = f"{intro} {s}"

        # Rule 2 - Lexicon substitution
        for normal, pisic in lexicon.items():
            pattern = r"\b" + re.escape(normal) + r"\b"
            s = re.sub(pattern, pisic, s, flags=re.IGNORECASE)

        # Rule 3 - add "miau-" prefix to certain verbs
        s = re.sub(r"\b(fac|face|realizează|scrie|studi(e|a)ză)\b",
                   lambda m: "miau-" + m.group(0), s)
        # Rule 4 - forms of "analiza" to "toarce"
        s = re.sub(r"\banaliz(ează|at)\b", r"toarce", s)

        # Rule 5 - Adds -uță to words that end in -ic, -ică, or -ici
        s = re.sub(r"\b(\w+ic[ăi]?)\b", r"\1uță", s)
        # Also add "miau-" prefix to certain adjectives
        s = re.sub(r"\b(bun|rău|frumos)\b", r"miau-\1", s)

        # Rule 6 - Closing with a random phrase from the list
        s += " " + random.choice(closings)

        output_sentences.append(s)

    return " ".join(output_sentences)


print(romanian_to_pisicesc("Lucrarea analizează impactul tehnologiei moderne asupra comunicării dintre oameni. Cercetătorii observă o creștere a energiei creative."))