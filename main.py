from negmas import SAOMechanism, TimeBasedConcedingNegotiator, make_issue
from negmas.preferences import LinearAdditiveUtilityFunction as LUFun 
from negotiators.negotiator import Basic_Negotiator

# Define what we're negotiating about
issues = [
    make_issue(name="price", values=100),
    make_issue(name="delivery", values=5),
    make_issue(name="quality", values=3)
]

# Create negotiation session (Stacked Alternating Offers)
session = SAOMechanism(issues=issues, n_steps=100)

# Add buyer (prefers low price) and seller (prefers high price)
session.add(
    TimeBasedConcedingNegotiator(name="time_based_negotiator"),
    ufun=LUFun.random(issues=issues, reserved_value=0.0).scale_max(1.0),
)
session.add(
    Basic_Negotiator(name="basic_negotiator"),
    ufun=LUFun.random(issues=issues, reserved_value=0.0).scale_max(1.0),
)

# Run and get result
result = session.run()
print(f"Agreement: {result.agreement}, Rounds: {result.step}")
session.plot()