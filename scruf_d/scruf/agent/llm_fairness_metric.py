# in fairness_metric.py, alongside your existing classes

from scruf.agent.llm_client import LLMClient
from . import FairnessMetric, FairnessMetricFactory, ItemFeatureFairnessMetric

class LLMFairnessMetric(FairnessMetric):
    """
    Uses an LLM to score fairness in [0,1] based on a natural-language description
    of the fairness goal and the observed history.
    """

    _PROPERTY_NAMES = ['prompt', 'model']

    def __init__(self):
        super().__init__()
        self.client = None

    def setup(self, input_props, names=None):
        super().setup(input_props, names=self.configure_names(
            LLMFairnessMetric._PROPERTY_NAMES, names))
        self.client = LLMClient(model=self.get_property('model'))

    def compute_fairness(self, history):
        fairness_goal = self.get_property('prompt')
        history_summary = self._summarize_history(history)

        system = (
            "You are a fairness evaluator for a recommender system. "
            "Given a fairness goal and a summary of recent recommendation history, "
            "return ONLY a JSON object: {\"score\": <float between 0 and 1>, \"reason\": <short string>}. "
            "1.0 means fully fair relative to the stated goal, 0.0 means fully unfair."
        )
        prompt = f"Fairness goal:\n{fairness_goal}\n\nHistory:\n{history_summary}"

        raw = self.client.generate(prompt, system=system)
        try:
            result = self.client.extract_json(raw)
            score = float(result["score"])
            return max(0.0, min(1.0, score))  # clamp defensively
        except (ValueError, KeyError, TypeError):
            # fail safe rather than crash the pipeline
            return 0.5

    def _summarize_history(self, history):
        # You'll want to tailor this to what `history` actually contains in scruf —
        # e.g. counts of protected vs non-protected items shown, positions, etc.
        return str(history)


#metric_specs = [("llm_fairness", LLMFairnessMetric)]
FairnessMetricFactory.register_fairness_metric("llm_fairness", LLMFairnessMetric)