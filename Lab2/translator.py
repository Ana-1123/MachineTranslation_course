"""
In approaching the task of building the word-by-word translation system, I first 
focused on loading and structuring the lexicon from the file lexicon.txt. I parse the 
file line by line, identifying parts of speech, gender information, and translation pairs.
I use regular expressions to detect sections defining nouns, proper nouns, and other word
categories, and I store each English word as a key with a list of dictionaries 
containing its French translation, part of speech, and gender if available. Once the 
lexicon is loaded, I begin the translation process by tokenizing the input sentence 
while preserving punctuation, and I normalize all words to lowercase to match the 
lexicon entries. I then generate part-of-speech tags for each word using the lexicon. I 
apply the translation rules in the following way: first, I implement the 
structural rewriting rule where an adjective followed by a noun is reordered as noun 
plus adjective to match French syntax. Next, I apply determiners and gender agreement 
rules by checking for combinations of determiners and nouns, selecting the appropriate 
French articles based on the noun's gender. I then handle special cases, such as the 
translation of words like "saw" and "cane," according to their part of speech in context. 
After applying these rules, I translate remaining words directly using the lexicon. 
Finally, I capitalize the beginning of the sentence and I join the 
tokens into a grammatically correct French sentence, cleaning up spacing around 
punctuation. The system successfully translates the example sentences from English to French.
"""

import re
# Load Lexicon
def load_lexicon(path):
    lexicon = {}
    current_pos = None
    gender = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("English-to-French"):
                continue
            # Extract POS and gender
            section_match = re.match(r'^(\w+)\s+N\s+\((\w+)\)', line)
            if section_match:
                current_pos = "N"
                gender = section_match.group(1)
                continue
            section_match = re.match(r'^(\w+)\s+\((\w+)\)', line)
            if section_match:
                current_pos = section_match.group(1)
                gender = None
                continue
            section_match = re.match(r'^PNOUN\b.*', line)
            if section_match:
                current_pos = 'PNOUN'
                gender = None
                continue
            # Parse translation pairs
            if "->" in line:
                eng, fr = [w.strip() for w in line.split("->")]
                eng_lower = eng.lower()
                fr_lower = fr.lower()
                entry = {"fr": fr_lower, "pos": current_pos, "gender": gender}
                lexicon.setdefault(eng_lower, []).append(entry)
            elif current_pos == "PNOUN" and line:
                eng_lower = line.lower()
                fr_lower = line.lower()
                entry = {"fr": fr_lower, "pos": current_pos, "gender": gender}
                lexicon.setdefault(eng_lower, []).append(entry)
    return lexicon

def translate(sentence, lexicon):
    # Tokenize sentence (keep punctuation)
    words = re.findall(r"[\w']+|[.,!?;]", sentence)
    words = [w.lower() for w in words]

    # Helper to get all POS tags for a word
    def get_pos(word):
        if word in lexicon:
            return [entry["pos"] for entry in lexicon[word]]
        return ["UNK"]

    # Helper to get gender for a word if known
    def get_gender(word):
        if word in lexicon:
            for e in lexicon[word]:
                if e.get("gender"):
                    return e["gender"]
        return None

    # Initialize
    pos_tags = [get_pos(w) for w in words]
    translated = [False] * len(words)
    output = words[:]

    # Apply rewriting rule: ADJ + N -> N + ADJ
    i = 0
    while i < len(words) - 1:
        if "ADJ" in pos_tags[i] and "N" in pos_tags[i + 1]:
            output[i], output[i + 1] = output[i + 1], output[i]
            pos_tags[i], pos_tags[i + 1] = pos_tags[i + 1], pos_tags[i]
            i += 2
        else:
            i += 1

    # Apply POS identification rules
    for i in range(len(output) - 1):
        w1, w2 = output[i], output[i + 1]
        pos1, pos2 = pos_tags[i], pos_tags[i + 1]

        # Determiners
        if w1 in ("the", "a") and "N" in pos2:
            gender = get_gender(w2)
            if w1 == "the":
                if gender == "Masc":
                    output[i] = "le"
                elif gender == "Fem":
                    output[i] = "la"
            elif w1 == "a":
                if gender == "Masc":
                    output[i] = "un"
                elif gender == "Fem":
                    output[i] = "une"
            translated[i] = True
            continue

        # DET + saw -> DET + Fem N
        if "DET" in pos1 and w2 == "saw":
            output[i + 1] = lexicon["saw"][0]["fr"]  # Fem N = "Scie"
            translated[i + 1] = True

        #  saw + DET -> V + DET
        if w1 == "saw" and "DET" in pos2:
            for e in lexicon["saw"]:
                if e["pos"] == "V":
                    output[i] = e["fr"]
                    translated[i] = True

        # DET + cane -> DET + Fem N
        if "DET" in pos1 and w2 == "cane":
            for e in lexicon["cane"]:
                if e["pos"] == "N":
                    output[i + 1] = e["fr"]
                    translated[i + 1] = True

        # N + cane -> N + ADJ
        if "N" in pos1 and w2 == "cane":
            for e in lexicon["cane"]:
                if e["pos"] == "ADJ":
                    output[i + 1] = e["fr"]
                    translated[i + 1] = True

    # Translate remaining words using lexicon directly
    for i, w in enumerate(output):
        if translated[i] or re.fullmatch(r"[.,!?;]", w):
            continue
        if w in lexicon:
            entry = lexicon[w][0]  # take first entry
            output[i] = entry["fr"]
        else:
            output[i] = w  # leave unknown words

    # Capitalize sentence
    output[0] = output[0].capitalize()

    # Join sentence and clean punctuation spacing
    result = " ".join(output)
    result = re.sub(r"\s+([.,!?;])", r"\1", result)
    return result



if __name__ == "__main__":
    lexicon = load_lexicon("lexicon.txt")

    examples = [
        "Mary reads a book.",
        "A book is under the table.",
        "Mary cut the sugar cane with a saw.",
        "Mary cut the sugar cane and is happy.",
        "The woman with a red cane saw a cat under the table and walks to the cat."
    ]
    for ex in examples:
        print(f"EN: {ex}")
        print(f"FR: {translate(ex, lexicon)}")
        print()
