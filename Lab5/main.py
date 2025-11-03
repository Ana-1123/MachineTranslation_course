class PhraseExtractor:
    def __init__(self):
        self.alignments = []
        
    def read_pure_matrix_alignment(self, filename):
        """
        Read alignment file in pure matrix format
        Returns: eng_words, ro_words, alignment_matrix
        """
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        eng_words, ro_words = [], []
        alignment_matrix = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                # Extract word lists from comments
                if 'English:' in line:
                    eng_part = line.split('English:')[1].strip()
                    eng_words = eng_part.split()
                elif 'Romanian:' in line:
                    ro_part = line.split('Romanian:')[1].strip()
                    ro_words = ro_part.split()
                continue
            
            # Process matrix row (just numbers)
            alignment_vector = [int(x) for x in line.split()]
            alignment_matrix.append(alignment_vector)
        
        return eng_words, ro_words, alignment_matrix
    
    def matrix_to_alignment_set(self, alignment_matrix):
        """Convert matrix format to set of (eng_idx, ro_idx) pairs"""
        alignments = set()
        for ro_idx, row in enumerate(alignment_matrix):
            for eng_idx, aligned in enumerate(row):
                if aligned == 1:
                    alignments.add((eng_idx, ro_idx))
        return alignments
    
    def alignment_set_to_matrix(self, alignments, eng_len, ro_len):
        """Convert alignment set back to matrix format"""
        matrix = [[0] * eng_len for _ in range(ro_len)]
        for eng_idx, ro_idx in alignments:
            if eng_idx < eng_len and ro_idx < ro_len:
                matrix[ro_idx][eng_idx] = 1
        return matrix
    
    def extract_consistent_phrases(self, eng_words, ro_words, alignment_matrix, max_phrase_length=7):
        """
        Extract all consistent phrases from word alignments
        Based on the definition from Koehn et al. 2003
        """
        eng_len = len(eng_words)
        ro_len = len(ro_words)
        
        # Build alignment set for easier lookup
        alignment_set = self.matrix_to_alignment_set(alignment_matrix)
        
        consistent_phrases = []
        
        # Try all possible English phrases
        for eng_start in range(eng_len):
            for eng_end in range(eng_start, min(eng_start + max_phrase_length, eng_len)):
                eng_phrase = eng_words[eng_start:eng_end + 1]
                
                # Find Romanian words aligned to this English phrase
                aligned_ro_indices = set()
                for eng_idx in range(eng_start, eng_end + 1):
                    for ro_idx in range(ro_len):
                        if (eng_idx, ro_idx) in alignment_set:
                            aligned_ro_indices.add(ro_idx)
                
                if not aligned_ro_indices:
                    continue
                
                ro_start = min(aligned_ro_indices)
                ro_end = max(aligned_ro_indices)
                
                # Check if Romanian phrase is within bounds
                if ro_end >= ro_len:
                    continue
                    
                ro_phrase = [ro_words[i] for i in range(ro_start, ro_end + 1)]
                
                # Check consistency
                if self.is_consistent_phrase(eng_start, eng_end, ro_start, ro_end, alignment_set, eng_len, ro_len):
                    consistent_phrases.append({
                        'eng_phrase': ' '.join(eng_phrase),
                        'ro_phrase': ' '.join(ro_phrase),
                        'eng_span': (eng_start, eng_end),
                        'ro_span': (ro_start, ro_end)
                    })
        
        return consistent_phrases
    
    def is_consistent_phrase(self, eng_start, eng_end, ro_start, ro_end, alignment_set, eng_len, ro_len):

        # No English word inside the phrase should align to Romanian word outside the phrase
        for eng_idx in range(eng_start, eng_end + 1):
            for ro_idx in range(ro_len):
                if (eng_idx, ro_idx) in alignment_set:
                    if not (ro_start <= ro_idx <= ro_end):
                        return False

        # No Romanian word inside the phrase should align to English word outside the phrase
        for ro_idx in range(ro_start, ro_end + 1):
            for eng_idx in range(eng_len):
                if (eng_idx, ro_idx) in alignment_set:
                    if not (eng_start <= eng_idx <= eng_end):
                        return False
        
        return True
    
    def symmetrize_alignments(self, eng_to_ro_matrix, ro_to_eng_matrix):
        """
        Combines intersection, union, and heuristic rules
        """
        eng_len = len(eng_to_ro_matrix[0]) if eng_to_ro_matrix else 0
        ro_len = len(eng_to_ro_matrix) if eng_to_ro_matrix else 0
        
        # Convert to sets
        eng_ro_set = self.matrix_to_alignment_set(eng_to_ro_matrix)
        ro_eng_set = self.matrix_to_alignment_set(ro_to_eng_matrix)
        
        print(f"  ENG->RO alignments: {len(eng_ro_set)}")
        print(f"  RO->ENG alignments: {len(ro_eng_set)}")
        
        symmetrized = set()
        
        # Intersection: alignments present in both directions
        intersection = eng_ro_set & ro_eng_set
        symmetrized.update(intersection)
        print(f"  Intersection points: {len(intersection)}")
        
        # Finds alignment points that are adjacent to intersection points
        union = eng_ro_set | ro_eng_set
        neighbor_points = self.get_neighbor_points(union, intersection, eng_len, ro_len)
        symmetrized.update(neighbor_points)
        print(f"  Neighbor points: {len(neighbor_points)}")
        
        # Finds words that align to exactly one word in the other language
        # Only adds if both directions suggest this unique mapping
        one_to_one_points = self.get_one_to_one_points(union, intersection, eng_len, ro_len)
        symmetrized.update(one_to_one_points)
        print(f"  One-to-one points: {len(one_to_one_points)}")
        
        # Fills gaps between strong alignments
        gap_points = self.get_gap_filling_points(union, intersection, eng_len, ro_len)
        symmetrized.update(gap_points)
        print(f"  Gap filling points: {len(gap_points)}")
        
        # Convert back to matrix
        return self.alignment_set_to_matrix(symmetrized, eng_len, ro_len), symmetrized
    
    def get_neighbor_points(self, union, intersection, eng_len, ro_len):
        """Find points adjacent to intersection points"""
        neighbors = set()
        for eng_idx, ro_idx in union:
            if (eng_idx, ro_idx) in intersection:
                continue
            # Check if adjacent to any intersection point
            for ie, ir in intersection:
                if abs(eng_idx - ie) <= 1 and abs(ro_idx - ir) <= 1:
                    neighbors.add((eng_idx, ro_idx))
                    break
        return neighbors
    
    def get_one_to_one_points(self, union, intersection, eng_len, ro_len):
        """Find points that complete 1:1 mappings"""
        one_to_one = set()
        
        # Check for English words with single alignment
        for eng_idx in range(eng_len):
            eng_alignments = [ro_idx for e, ro_idx in union if e == eng_idx]
            if len(eng_alignments) == 1:
                ro_idx = eng_alignments[0]
                if (eng_idx, ro_idx) not in intersection:
                    # Check if Romanian word also has single alignment
                    ro_alignments = [e for e, r in union if r == ro_idx]
                    if len(ro_alignments) == 1:
                        one_to_one.add((eng_idx, ro_idx))
        
        return one_to_one
    
    def get_gap_filling_points(self, union, intersection, eng_len, ro_len):
        """Fill gaps in alignment patterns to create better phrases"""
        gap_points = set()
        
        # Look for patterns where words are mostly aligned but missing some connections
        for eng_idx in range(eng_len):
            for ro_idx in range(ro_len):
                if (eng_idx, ro_idx) in intersection:
                    continue
                    
                # Check if this fills a gap between existing alignments
                if self.fills_alignment_gap(eng_idx, ro_idx, union, intersection, eng_len, ro_len):
                    gap_points.add((eng_idx, ro_idx))
        
        return gap_points
    
    def fills_alignment_gap(self, eng_idx, ro_idx, union, intersection, eng_len, ro_len):
        #Check if a point fills an alignment gap
        nearby_intersection = 0
        for de in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if de == 0 and dr == 0: # Skips the center position (0,0) - that's the point we're testing
                    continue
                ne, nr = eng_idx + de, ro_idx + dr
                if 0 <= ne < eng_len and 0 <= nr < ro_len: # Ensures we don't go outside the matrix boundaries
                    if (ne, nr) in intersection:
                        nearby_intersection += 1
        
        # If surrounded by intersection points, likely a missing alignment
        return nearby_intersection >= 2
    
    def print_alignment_comparison(self, original_matrix, symmetrized_matrix, eng_words, ro_words, title):
        """Print comparison between original and symmetrized alignments"""
        print(f"\n{'='*60}")
        print(f"{title} \n")
        
        original_set = self.matrix_to_alignment_set(original_matrix)
        symmetrized_set = self.matrix_to_alignment_set(symmetrized_matrix)
        
        print(f"Original alignments: {len(original_set)}")
        print(f"Symmetrized alignments: {len(symmetrized_set)}")
        print(f"New alignments added: {len(symmetrized_set - original_set)}")
        
        # Show specific changes
        added = symmetrized_set - original_set
        if added:
            print("\nAdded alignments:")
            for eng_idx, ro_idx in added:
                print(f"  + {ro_words[ro_idx]:12} -> {eng_words[eng_idx]}")
        
        removed = original_set - symmetrized_set
        if removed:
            print("\nRemoved alignments:")
            for eng_idx, ro_idx in removed:
                print(f"  - {ro_words[ro_idx]:12} -> {eng_words[eng_idx]}")
                

def analyze_sentence_pair(extractor, eng_file, ro_file, title):
    """Analyze a sentence pair with both alignment directions"""
    print(f"\n{'#'*80}")
    print(f"PROCESSING: {title} \n")
    
    # Read both alignment directions
    eng_words1, ro_words1, matrix1 = extractor.read_pure_matrix_alignment(eng_file)
    eng_words2, ro_words2, matrix2 = extractor.read_pure_matrix_alignment(ro_file)
    
    eng_words, ro_words = eng_words1, ro_words1
    
    print(f"English: {' '.join(eng_words)}")
    print(f"Romanian: {' '.join(ro_words)}")
    
    # 1. Extract phrases from BOTH original alignment directions
    print(f"\n--- Phrases from {eng_file} (Direction 1) ---")
    phrases1 = extractor.extract_consistent_phrases(eng_words, ro_words, matrix1)
    print(f"Found {len(phrases1)} consistent phrases:")
    for i, phrase in enumerate(phrases1[:8]):  # Show first 8
        print(f"{i+1:2}. '{phrase['eng_phrase']}' <-> '{phrase['ro_phrase']}'")
    
    print(f"\n--- Phrases from {ro_file} (Direction 2) ---")
    phrases2 = extractor.extract_consistent_phrases(eng_words, ro_words, matrix2)
    print(f"Found {len(phrases2)} consistent phrases:")
    for i, phrase in enumerate(phrases2[:8]):  # Show first 8
        print(f"{i+1:2}. '{phrase['eng_phrase']}' <-> '{phrase['ro_phrase']}'")
    
    # Compare the two directions
    print(f"\n--- Comparison of Original Directions ---")
    unique_to_dir1 = set([p['eng_phrase'] + " ||| " + p['ro_phrase'] for p in phrases1])
    unique_to_dir2 = set([p['eng_phrase'] + " ||| " + p['ro_phrase'] for p in phrases2])
    
    common_phrases = unique_to_dir1 & unique_to_dir2
    only_in_dir1 = unique_to_dir1 - unique_to_dir2
    only_in_dir2 = unique_to_dir2 - unique_to_dir1
    
    print(f"Phrases common to both directions: {len(common_phrases)}")
    print(f"Phrases only in Direction 1: {len(only_in_dir1)}")
    print(f"Phrases only in Direction 2: {len(only_in_dir2)}")
    
    if only_in_dir1:
        print(f"\nUnique to Direction 1:")
        for i, phrase in enumerate(list(only_in_dir1)[:3]):
            print(f"  {i+1}. {phrase}")
    
    if only_in_dir2:
        print(f"\nUnique to Direction 2:")
        for i, phrase in enumerate(list(only_in_dir2)[:3]):
            print(f"  {i+1}. {phrase}")
    
    # 2. Perform symmetrization
    print(f"\n--- Symmetrization Process ---")
    symmetrized_matrix, symmetrized_set = extractor.symmetrize_alignments(matrix1, matrix2)
    
    # 3. Extract phrases from symmetrized alignments
    print(f"\n--- Phrases from Symmetrized Alignments ---")
    symmetrized_phrases = extractor.extract_consistent_phrases(eng_words, ro_words, symmetrized_matrix)
    print(f"Found {len(symmetrized_phrases)} consistent phrases:")
    for i, phrase in enumerate(symmetrized_phrases[:10]):
        print(f"{i+1:2}. '{phrase['eng_phrase']}' <-> '{phrase['ro_phrase']}'")
    
    # 4. Show how symmetrization combines both directions
    print(f"\n--- Symmetrization Benefits ---")
    symmetrized_phrase_set = set([p['eng_phrase'] + " ||| " + p['ro_phrase'] for p in symmetrized_phrases])
    
    recovered_from_dir1 = symmetrized_phrase_set & only_in_dir1
    recovered_from_dir2 = symmetrized_phrase_set & only_in_dir2
    new_phrases = symmetrized_phrase_set - (unique_to_dir1 | unique_to_dir2)
    
    print(f"Recovered phrases from Direction 1: {len(recovered_from_dir1)}")
    print(f"Recovered phrases from Direction 2: {len(recovered_from_dir2)}")
    print(f"New phrases created by symmetrization: {len(new_phrases)}")
    
    return {
        'title': title,
        'phrases_dir1': len(phrases1),
        'phrases_dir2': len(phrases2),
        'phrases_symmetrized': len(symmetrized_phrases),
        'common_phrases': len(common_phrases),
        'unique_dir1': len(only_in_dir1),
        'unique_dir2': len(only_in_dir2),
        'improvement_over_dir1': len(symmetrized_phrases) - len(phrases1),
        'improvement_over_dir2': len(symmetrized_phrases) - len(phrases2)
    }

def main():
    extractor = PhraseExtractor()
    
    # Process each sentence pair
    results = []
    
    # Mermaid example
    results.append(analyze_sentence_pair(
        extractor, 
        'alignments/mermaid_ro_eng.txt', 
        'alignments/mermaid_eng_ro.txt',  
        'Mermaid: "the mermaid sings majestically over the golden caves"'
    ))
    
    # Cat example
    results.append(analyze_sentence_pair(
        extractor,
        'alignments/cat_ro_eng.txt',
        'alignments/cat_eng_ro.txt',
        'Cat: "the cat assumes it will go to the beach with other cats"'
    ))
    
    # Michael example  
    results.append(analyze_sentence_pair(
        extractor,
        'alignments/michael_ro_eng.txt',
        'alignments/michael_eng_ro.txt',
        'Michael: "michael assumes that he will stay in the house"'
    ))


if __name__ == "__main__":
    main()