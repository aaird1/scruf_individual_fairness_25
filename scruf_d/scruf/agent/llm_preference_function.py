# in preference_function.py

from scruf.agent.llm_client import LLMClient
from .preference_function import PreferenceFunctionFactory, PreferenceFunction
from scruf.util import ResultList
import copy

class LLMPreferenceFunction(PreferenceFunction):
    """
    Uses an LLM to rescore a recommendation list according to a natural-language
    description of what should be prioritized.
    """

    _PROPERTY_NAMES = ['prompt', 'model']

    def __init__(self):
        super().__init__()
        self.client = None

    def setup(self, input_props, names=None):
        super().setup(input_props, names=self.configure_names(
            LLMPreferenceFunction._PROPERTY_NAMES, names))
        self.client = LLMClient(model=self.get_property('model'))

    def __str__(self):
        return f"LLMPreferenceFunction: prompt = {self.get_property('prompt')}"

    def compute_preferences(self, recommendations: ResultList) -> ResultList:
        rec_list = copy.deepcopy(recommendations)
        goal = self.get_property('prompt')

        item_ids = [entry.item for entry in rec_list.get_results()]
        system = (
            "You assign preference boost scores to items for a recommender system, "
            "based on a stated prioritization goal. "
            "Return ONLY a JSON object mapping each item id (as a string) to a float boost value "
            "(can be negative, zero, or positive)."
        )
        prompt = f"Prioritization goal:\n{goal}\n\nItem ids:\n{item_ids}"

        raw = self.client.generate(prompt, system=system)
        try:
            scores = self.client.extract_json(raw)
            rec_list.rescore(lambda entry: float(scores.get(str(entry.item), 0.0)))
        except (ValueError, KeyError, TypeError):
            rec_list.rescore(lambda entry: 0.0)  # fail safe: no-op boost

        return rec_list


PreferenceFunctionFactory.register_preference_function("llm_preference", LLMPreferenceFunction)