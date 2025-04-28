from langchain_core.output_parsers import StrOutputParser

filter_codes = {
    "S1": "S1: Violent Crimes",
    "S2": "S2: Non-Violent Crimes",
    "S3": "S3: Sex-Related Crimes",
    "S4": "S4: Child Sexual Exploitation",
    "S5": "S5: Defamation",
    "S6": "S6: Specialized Advice",
    "S7": "S7: Privacy",
    "S8": "S8: Intellectual Property",
    "S9": "S9: Indiscriminate Weapons",
    "S10": "S10: Hate",
    "S11": "S11: Suicide & Self-Harm",
    "S12": "S12: Sexual Content",
    "S13": "S13: Elections",
}


def parse_guard_output(output: str) -> bool:
    if output == "safe":
        return {
            "safe": True,
            "reason": "The output is safe.",
        }
    else:
        return {
            "safe": False,
            "reason": filter_codes[output.strip().split("\n")[1].upper()],
        }


class FilterChain:
    def __init__(self, model_guard):
        self.filter_chain = model_guard | StrOutputParser() | (lambda output: parse_guard_output(output))
