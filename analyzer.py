# <Imports>
import diagnoser
from konlpy.tag import Hannanum, Kkma, Komoran, Okt
from typing import List, Dict, Tuple

# <Constants – ALL_CAPS>
ANALYZER_CLASSES = {
    "hannanum": Hannanum,
    "kkma": Kkma,
    "komoran": Komoran,
    "okt": Okt
}

# <Functions – camelCasingAllNames>
def analyzeWithTagger(analyzerType: str, text: str) -> List[Tuple[str, str]]:
    """
    Performs POS tagging using the specified analyzer type.

    :param analyzerType: One of 'hannanum', 'kkma', 'komoran', 'okt' (case-insensitive)
    :param text: Text to analyze
    :return: List of (morpheme, tag) tuples
    """
    analyzerType = analyzerType.lower()
    if analyzerType == 'komoran':
        # weird case
        text = text.replace('\n', '')
    if analyzerType not in ANALYZER_CLASSES:
        raise ValueError(f"Unsupported analyzer type: {analyzerType}")
    
    analyzer = ANALYZER_CLASSES[analyzerType]()
    return analyzer.pos(text)


def analyzeWithAllTaggers(text: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Performs POS tagging using all supported analyzers.

    :param text: Text to analyze
    :return: Dictionary mapping analyzer name to list of (morpheme, tag) tuples
    """
    results = {}
    for name in ANALYZER_CLASSES:
        try:
            results[name] = analyzeWithTagger(name, text)
        except Exception as e:
            diagnoser.log(f"[ERROR] {name} failed: {e}")
            results[name] = [("Error", str(e))]
    return results

# <main function>
def main():
    sampleText = """안녕하세요, PAL파트너스입니다 :)
운영자님 스타일과 잘 맞을 것 같아 제안드리고 싶었습니다.

미리 정산되는 구조로 최대 500만 원 지급 가능합니다.
블로그 운영에는 어떠한 간섭도 없습니다.

혹시 지금 구조만 간단히 들어보셔도 괜찮으실까요?"""
    diagnoser.log("Running MMAT on sample text...\n")

    allResults = analyzeWithAllTaggers(sampleText)
    for analyzer, tags in allResults.items():
        diagnoser.log(f"{analyzer.upper()} → {tags}")

if __name__ == "__main__":
    main()