# arvis/conversation/response_plan_builder.py

from arvis.conversation.response_strategy_decision import ResponseStrategyDecision
from arvis.conversation.response_plan import ResponsePlan
from arvis.conversation.response_realization_mode import ResponseRealizationMode
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.generation.frame_builder import build_generation_frame
from arvis.linguistic.generation.prompt_builder import build_llm_prompt


class ResponsePlanBuilder:
    """
    Builds a ResponsePlan from a ResponseStrategyDecision.

    This component determines:
    - linguistic act
    - realization mode
    - template fast-path
    """

    @staticmethod
    def build(decision: ResponseStrategyDecision) -> ResponsePlan:

        # NOTE: lexicon should come from context in future (injection)
        lexicon = decision.signals.get("lexicon_snapshot")
        state = decision.signals.get("state")

        strategy = decision.strategy

        # --- Act mapping (strategy → linguistic act) ---
        if strategy == ResponseStrategyType.ABSTENTION:
            act = LinguisticAct(LinguisticActType.ABSTENTION)
        elif strategy == ResponseStrategyType.CONFIRMATION:
            act = LinguisticAct(LinguisticActType.REQUEST_CONFIRMATION)
        elif strategy == ResponseStrategyType.ACTION:
            act = LinguisticAct(LinguisticActType.DECISION)
        elif strategy == ResponseStrategyType.INFORMATIONAL:
            act = LinguisticAct(LinguisticActType.INFORMATION)
        elif strategy == ResponseStrategyType.SOCIAL:
            act = LinguisticAct(LinguisticActType.INFORMATION)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
        
        frame = None
        prompt = None

        if lexicon is not None:
            frame_obj = build_generation_frame(
                act=act,
                lexicon=lexicon,
                state=state,
            )
            frame = {
                "act": frame_obj.act.value,
                "tone": frame_obj.tone,
                "verbosity": frame_obj.verbosity,
                "allowed_entries": frame_obj.allowed_entries,
            }

            prompt = build_llm_prompt(
                frame=frame_obj,
                context=decision.signals.get("context", ""),
                query=decision.signals.get("query", ""),
            )

        # --- ABSTENTION ---
        if strategy == ResponseStrategyType.ABSTENTION:
            return ResponsePlan(
                strategy=strategy,
                realization_mode=ResponseRealizationMode.TEMPLATE,
                act_type=LinguisticActType.ABSTENTION,
                template_key="abstention",
                short_circuit=True,
                context_hints=decision.signals,
            )

        # --- CONFIRMATION ---
        if strategy == ResponseStrategyType.CONFIRMATION:
            return ResponsePlan(
                strategy=strategy,
                realization_mode=ResponseRealizationMode.TEMPLATE,
                act_type=LinguisticActType.REQUEST_CONFIRMATION,
                template_key="request_confirmation",
                short_circuit=True,
                context_hints=decision.signals,
            )

        # --- ACTION ---
        if strategy == ResponseStrategyType.ACTION:
            act_type = LinguisticActType.DECISION

            return ResponsePlan(
                strategy=strategy,
                realization_mode=ResponseRealizationMode.LLM,
                act_type=act_type,
                short_circuit=False,
                context_hints=decision.signals,
                generation_frame=frame,
                prompt=prompt,
            )

        # --- INFORMATIONAL ---
        if strategy == ResponseStrategyType.INFORMATIONAL:
            act_type = LinguisticActType.INFORMATION

            return ResponsePlan(
                strategy=strategy,
                realization_mode=ResponseRealizationMode.LLM,
                act_type=act_type,
                short_circuit=False,
                context_hints=decision.signals,
                generation_frame=frame,
                prompt=prompt,
            )

        # --- SOCIAL (future extension) ---
        if strategy == ResponseStrategyType.SOCIAL:
            return ResponsePlan(
                strategy=strategy,
                realization_mode=ResponseRealizationMode.TEMPLATE,
                act_type=LinguisticActType.INFORMATION,
                template_key="social_response",
                short_circuit=True,
                context_hints=decision.signals,
            )

        raise ValueError(f"Unsupported strategy: {strategy}")