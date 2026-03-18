from negmas import SAONegotiator, ResponseType

from bidding.bidding_strategy import TimeBasedBidding
from bidding.adaptive_bidding import AdaptiveBidding
from bidding.tit_for_tat import TitForTatBidding
from bidding.predictive_tit_for_tat import PredictiveTitForTatBidding
from bidding.micro import MiCROBidding
from bidding.hybrid_bidding import HybridBidding

from acceptance.acceptance_strategies import ACnext, ACasp, AClow, ACnew

from opponent_modeling.frequency_opponent_model import FrequencyOpponentModel
from opponent_modeling.bayesian_opponent_model import BayesianOpponentModel
from opponent_modeling.startegy_learning import LinearExtrapolationModel, GaussianProcessModel


class BOANegotiator(SAONegotiator):

    def __init__(self, bidding_strategy="timebased", acceptance_strategy="acasp",
                 opponent_model="frequency", name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self._bidding_name = bidding_strategy
        self._acceptance_name = acceptance_strategy
        self._opponent_model_name = opponent_model
        self._last_bid = None

    def on_negotiation_start(self, state):
        issues = self.nmi.issues

        # Opponent Model
        if self._opponent_model_name == "frequency":
            self.opp_model = FrequencyOpponentModel(issues)
        elif self._opponent_model_name == "bayesian":
            self.opp_model = BayesianOpponentModel(issues)
        elif self._opponent_model_name == "linear":
            self.opp_model = LinearExtrapolationModel(self.ufun)
        elif self._opponent_model_name == "gp":
            self.opp_model = GaussianProcessModel(self.ufun)
        else:
            raise ValueError(f"Unknown opponent model: {self._opponent_model_name}")

        # Bidding Strategy
        if self._bidding_name == "timebased":
            self.bidding = TimeBasedBidding(self.ufun)
        elif self._bidding_name == "adaptive":
            self.bidding = AdaptiveBidding(self.ufun, self.opp_model)
        elif self._bidding_name == "titfortat":
            self.bidding = TitForTatBidding(self.ufun)
        elif self._bidding_name == "predictive_titfortat": 
            self.bidding = PredictiveTitForTatBidding(self.ufun, self.opp_model)
        elif self._bidding_name == "micro":
            self.bidding = MiCROBidding(self.ufun, self.opp_model)
        elif self._bidding_name == "hybrid":
            self.bidding = HybridBidding(self.ufun, self.opp_model)
        else:
            raise ValueError(f"Unknown bidding strategy: {self._bidding_name}")

        # Acceptance Strategy
        if self._acceptance_name == "acnext":
            self.acceptance = ACnext(self.ufun, self.bidding)
        elif self._acceptance_name == "acasp":
            self.acceptance = ACasp(self.ufun, self.bidding)
        elif self._acceptance_name == "aclow":
            self.acceptance = AClow(self.ufun, self.bidding)
        elif self._acceptance_name == "acnew":
            self.acceptance = ACnew(self.ufun, self.bidding)
        else:
            raise ValueError(f"Unknown acceptance strategy: {self._acceptance_name}")

    def respond(self, state):
        offer = state.current_offer
        if offer is None:
            return ResponseType.REJECT_OFFER

        # Update opponent model
        if self._opponent_model_name in ("frequency", "bayesian", "linear"):
            self.opp_model.update(offer)
        elif self._opponent_model_name == "gp":
            self.opp_model.update(offer, state.time)

        # Update bidding strategies that track opponent
        if self._bidding_name == "adaptive":
            self.bidding.update_opponent_history(offer)
        elif self._bidding_name == "titfortat":
            self.bidding.update_opponent_history(offer)
        elif self._bidding_name == "predictive_titfortat":         
            self.bidding.update_opponent_history(offer, state.time)
        elif self._bidding_name == "micro":
            self.bidding.update_opponent_offer(offer)
        elif self._bidding_name == "hybrid":
            self.bidding.update_opponent_history(offer)

        # Acceptance check — pass time and outcome_space, NOT state
        outcome_space = self.nmi.outcome_space
        time = state.time
        if self.acceptance.should_accept(offer, time, outcome_space):
            return ResponseType.ACCEPT_OFFER
        return ResponseType.REJECT_OFFER

    def propose(self, state):
        bid = self.bidding.generate_bid(self.nmi.outcome_space, state.time)
        self._last_bid = bid
        if self._acceptance_name in ("aclow", "acnew"):
            self.acceptance.record_my_bid(bid)
        return bid