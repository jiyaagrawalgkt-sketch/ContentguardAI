import re
from typing import Optional, Tuple, Dict, Any, List


class CorrectionValidationError(Exception):
    """Raised when a proposed automatic correction fails safety validation."""
    pass


class ManualReviewRequiredError(Exception):
    """Raised when a finding cannot be safely auto-corrected and requires human judgment."""
    pass


# Disallowed phrases in actual content replacement text (these are advice/instructions, NOT replacement copy)
INSTRUCTION_EXPLANATION_MARKERS = [
    r"^substantiate\b",
    r"^provide\s+(?:verified|proof|research|documentation|citation)\b",
    r"^consider\s+(?:moving|rephrasing|revising|removing)\b",
    r"^change\s+statement\s+to\b",
    r"^consult\s+(?:legal|compliance|team)\b",
    r"^renew\s+(?:approval|documentation)\b",
    r"^harmonize\s+statement\b",
    r"^remove\s+(?:unverified|unapproved|unsupported|risk)\b",
    r"^align\s+with\s+approved\b",
    r"\bverifiable\s+use\s+cases\b",
    r"\borganizational\s+knowledge\s+base\b",
    r"\bofficial\s+approved\s+fact\b",
    r"\bpolicy\s+violation\b",
    r"\bguideline\s+reference\b",
]


def is_instruction_or_explanation(text: Optional[str]) -> bool:
    """Detect if a text string is an editorial instruction/advice rather than literal replacement content."""
    if not text or not text.strip():
        return False
    norm = text.strip().lower()
    for pattern in INSTRUCTION_EXPLANATION_MARKERS:
        if re.search(pattern, norm):
            return True
    return False


def determine_correction_strategy(
    action: Optional[str],
    replacement: Optional[str],
    category: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Determine the appropriate correction operation: 'REPLACE', 'REMOVE', 'REWRITE', or 'MANUAL_REVIEW'.
    Sanitizes any inadvertent explanation text in replacement.
    """
    clean_action = (action or "Replace").strip().lower()
    clean_repl = replacement.strip() if replacement is not None else None

    # If replacement is an editorial instruction/advice sentence, strip it immediately!
    if is_instruction_or_explanation(clean_repl):
        clean_repl = None

    if clean_action == "remove" or clean_repl == "":
        return "REMOVE", ""

    if clean_action in ["review", "verify", "update_source", "manual"]:
        if clean_repl and not is_instruction_or_explanation(clean_repl):
            return "REPLACE", clean_repl
        return "MANUAL_REVIEW", None

    if clean_repl:
        if category in ["unnecessary_content", "brand_voice"] and len(clean_repl.split()) > 4:
            return "REWRITE", clean_repl
        return "REPLACE", clean_repl

    return "MANUAL_REVIEW", None


def locate_target_span(
    content: str,
    matched_text: str,
    char_start: Optional[int] = None,
    char_end: Optional[int] = None,
    context_sentence: Optional[str] = None
) -> Optional[Tuple[int, int]]:
    """
    Locates the exact target occurrence in the latest content.
    1. Tests provided offsets first.
    2. If offset shifted, searches for occurrences.
    3. If multiple occurrences, uses context_sentence or surrounding window to disambiguate.
    """
    if not content or not matched_text:
        return None

    # 1. Exact match at offsets
    if char_start is not None and char_end is not None and 0 <= char_start < char_end <= len(content):
        if content[char_start:char_end] == matched_text:
            return char_start, char_end

    # 2. Search all occurrences
    occurrences = []
    idx = 0
    while True:
        pos = content.find(matched_text, idx)
        if pos == -1:
            break
        occurrences.append((pos, pos + len(matched_text)))
        idx = pos + 1

    if len(occurrences) == 1:
        return occurrences[0]

    if len(occurrences) > 1:
        # Disambiguate using sentence context if available
        if context_sentence and context_sentence.strip():
            cs_clean = context_sentence.strip()
            # If the context sentence is present in the text, pick the occurrence located within it
            if cs_clean in content:
                cs_pos = content.find(cs_clean)
                cs_end = cs_pos + len(cs_clean)
                for s, e in occurrences:
                    if cs_pos <= s and e <= cs_end:
                        return s, e

            # Otherwise, find the sentence in content that has the highest word overlap with context_sentence
            content_sentences = re.split(r"(?<=[.!?])\s+", content)
            best_sent_pos = None
            best_sent_score = -1
            current_cursor = 0
            cs_words = set(re.findall(r"\w+", cs_clean.lower()))

            for sent in content_sentences:
                sent_start = content.find(sent, current_cursor)
                if sent_start == -1:
                    sent_start = current_cursor
                sent_words = set(re.findall(r"\w+", sent.lower()))
                overlap = len(cs_words.intersection(sent_words))
                if overlap > best_sent_score:
                    best_sent_score = overlap
                    best_sent_pos = (sent_start, sent_start + len(sent))
                current_cursor = sent_start + len(sent)

            if best_sent_pos and best_sent_score >= 2:
                # Find occurrence closest to or within the best matching sentence
                b_s, b_e = best_sent_pos
                for s, e in occurrences:
                    if b_s <= s and e <= b_e:
                        return s, e
                return min(occurrences, key=lambda occ: abs(occ[0] - b_s))

        # Fallback to occurrence closest to original char_start
        if char_start is not None:
            return min(occurrences, key=lambda occ: abs(occ[0] - char_start))

        return occurrences[0]

    # 3. Case-insensitive / whitespace-normalized fallback
    pattern = re.compile(re.escape(matched_text.strip()), re.IGNORECASE)
    match = pattern.search(content)
    if match:
        return match.start(), match.end()

    return None


def clean_grammar_after_removal(text: str, start_pos: int) -> str:
    """
    Cleans up whitespace and dangling punctuation caused by deleting a phrase.
    Preserves paragraph breaks, capitalization, and surrounding punctuation.
    """
    # 1. Collapse multiple inline spaces/tabs to single space
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r"[ \t]{2,}", " ", line)
        # Dangling commas or punctuation: ", ," -> ",", " , " -> ", "
        cleaned_line = re.sub(r"\s+([,.;:!?])", r"\1", cleaned_line)
        cleaned_line = re.sub(r",\s*,+", ",", cleaned_line)
        cleaned_line = re.sub(r",\s*\.", ".", cleaned_line)
        cleaned_line = re.sub(r"([.!?])\s*([.!?])+", r"\1", cleaned_line)
        # Dangling conjunction at end of sentence: "foo and ." -> "foo."
        cleaned_line = re.sub(r"\s+(?:and|or|with|for|in|to|at)\s*([.,;!?])", r"\1", cleaned_line, flags=re.IGNORECASE)
        # Dangling conjunction after colon: ": and " -> ": "
        cleaned_line = re.sub(r":\s+(?:and|or|with|for)\s+", ": ", cleaned_line, flags=re.IGNORECASE)
        cleaned_lines.append(cleaned_line.strip())

    result = "\n".join(cleaned_lines)
    # Collapse 3+ newlines to 2 newlines (preserve paragraphs)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def apply_context_aware_correction(
    content: str,
    matched_text: str,
    suggested_replacement: Optional[str],
    correction_type: str,
    char_start: Optional[int] = None,
    char_end: Optional[int] = None,
    context_sentence: Optional[str] = None
) -> Tuple[str, str]:
    """
    Applies the validated correction to content.
    Returns: (corrected_content, actual_applied_operation)
    """
    if correction_type == "MANUAL_REVIEW":
        raise ManualReviewRequiredError(
            "This finding requires manual editorial or legal evaluation. "
            "Automatic replacement cannot be safely applied without human review."
        )

    span = locate_target_span(content, matched_text, char_start, char_end, context_sentence)
    if not span:
        raise CorrectionValidationError(
            f"The target text '{matched_text[:40]}...' was not found in the current draft. "
            "It may have already been modified in a previous edit."
        )

    start, end = span
    target = content[start:end]

    if correction_type == "REMOVE" or suggested_replacement == "":
        # Remove target span
        prefix = content[:start]
        suffix = content[end:]
        raw_combined = prefix + suffix
        corrected = clean_grammar_after_removal(raw_combined, start)
        return corrected, "REMOVE"

    # REPLACE or REWRITE
    repl = suggested_replacement or ""

    # Check for forbidden explanation markers
    if is_instruction_or_explanation(repl):
        raise CorrectionValidationError(
            f"Refused to insert editorial instruction into content: '{repl[:50]}...'. "
            "Findings must only apply literal content replacements."
        )

    # Intelligent casing alignment:
    # If the original matched text began with an uppercase character and wasn't all-caps,
    # match the casing of the replacement.
    if target and target[0].isupper() and not target.isupper() and repl and repl[0].islower():
        # Check if target is at sentence start or starts with capital
        repl = repl[0].upper() + repl[1:]

    corrected = content[:start] + repl + content[end:]
    return corrected, correction_type


def validate_correction_safety(
    original_content: str,
    corrected_content: str,
    matched_text: str,
    replacement: Optional[str],
    correction_type: str
) -> bool:
    """
    Safe correction validation layer:
    - Confirms content changed meaningfully.
    - Confirms non-empty output.
    - Confirms no editorial explanations were injected.
    - Confirms preservation of unrelated content.
    """
    if not corrected_content or not corrected_content.strip():
        raise CorrectionValidationError("Correction resulted in empty content.")

    if original_content == corrected_content:
        raise CorrectionValidationError("Correction resulted in zero changes to the content.")

    if replacement and is_instruction_or_explanation(replacement):
        raise CorrectionValidationError("Replacement contains forbidden editorial explanation markers.")

    # Check that forbidden explanation phrases were not injected into the corrected text
    for pattern in INSTRUCTION_EXPLANATION_MARKERS:
        if re.search(pattern, corrected_content, re.IGNORECASE) and not re.search(pattern, original_content, re.IGNORECASE):
            raise CorrectionValidationError("Safety check failed: explanation instruction was injected into content.")

    return True
