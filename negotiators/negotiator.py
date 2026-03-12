from negmas import SAONegotiator, ResponseType

from bidding.bidding_strategy import BiddingStrategy
from acceptance.acceptance_strategy import AcceptanceStrategy
from opponent_modeling.frequency_opponent_model import OpponentModel


class Basic_Negotiator(SAONegotiator):

    def on_negotiation_start(self, state):
        self.opponent_model = OpponentModel(self.nmi.issues)
        self.bidding = BiddingStrategy(self.ufun)
        self.acceptance = AcceptanceStrategy(self.ufun, self.bidding)

    def respond(self, state):
        offer = state.current_offer
        time = state.time

        if offer:
            self.opponent_model.update(offer)

        if self.acceptance.should_accept(offer, time):
            return ResponseType.ACCEPT_OFFER

        bid = self.bidding.generate_bid(self.nmi.outcome_space, time)
        return ResponseType.REJECT_OFFER, bid