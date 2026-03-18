from negmas import make_issue
from negmas.preferences import LinearAdditiveUtilityFunction as LUFun


def get_all_domains():
    return [
        job_offer(),
        car_purchase(),
        software_license(),
        apartment_rental(),
        freelance_contract(),
    ]


def job_offer():
    issues = [
        make_issue(name="salary",      values=10),  # 0=40k, 9=85k
        make_issue(name="remote_days", values=6),   # 0–5 days/week
        make_issue(name="vacation",    values=5),   # 0=15 days, 4=30 days
    ]
    # Employee: high salary, more remote, more vacation
    buyer = LUFun(
        values={
            "salary":      lambda v: v / 9.0,
            "remote_days": lambda v: v / 5.0,
            "vacation":    lambda v: v / 4.0,
        },
        weights={"salary": 0.6, "remote_days": 0.25, "vacation": 0.15},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    # Employer: low salary, less remote, less vacation
    seller = LUFun(
        values={
            "salary":      lambda v: 1.0 - v / 9.0,
            "remote_days": lambda v: 1.0 - v / 5.0,
            "vacation":    lambda v: 1.0 - v / 4.0,
        },
        weights={"salary": 0.6, "remote_days": 0.25, "vacation": 0.15},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    return {"name": "Job Offer", "issues": issues, "ufun_buyer": buyer, "ufun_seller": seller}


def car_purchase():
    issues = [
        make_issue(name="price",        values=10),  # 0=cheap, 9=expensive
        make_issue(name="warranty",     values=5),   # 0=1yr, 4=5yr
        make_issue(name="delivery",     values=4),   # 0=1wk, 3=4wks
    ]
    # Buyer: low price, long warranty, fast delivery
    buyer = LUFun(
        values={
            "price":    lambda v: 1.0 - v / 9.0,
            "warranty": lambda v: v / 4.0,
            "delivery": lambda v: 1.0 - v / 3.0,
        },
        weights={"price": 0.6, "warranty": 0.25, "delivery": 0.15},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    # Seller: high price, short warranty, slow delivery
    seller = LUFun(
        values={
            "price":    lambda v: v / 9.0,
            "warranty": lambda v: 1.0 - v / 4.0,
            "delivery": lambda v: v / 3.0,
        },
        weights={"price": 0.6, "warranty": 0.25, "delivery": 0.15},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    return {"name": "Car Purchase", "issues": issues, "ufun_buyer": buyer, "ufun_seller": seller}


def software_license():
    issues = [
        make_issue(name="price",         values=10),  # license cost
        make_issue(name="seats",         values=6),   # 0=5 seats, 5=30 seats
        make_issue(name="support_level", values=4),   # 0=basic, 3=premium
    ]
    # Buyer: low price, many seats, high support
    buyer = LUFun(
        values={
            "price":         lambda v: 1.0 - v / 9.0,
            "seats":         lambda v: v / 5.0,
            "support_level": lambda v: v / 3.0,
        },
        weights={"price": 0.5, "seats": 0.3, "support_level": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    # Seller: high price, few seats, low support (cheaper to provide)
    seller = LUFun(
        values={
            "price":         lambda v: v / 9.0,
            "seats":         lambda v: 1.0 - v / 5.0,
            "support_level": lambda v: 1.0 - v / 3.0,
        },
        weights={"price": 0.5, "seats": 0.3, "support_level": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    return {"name": "Software License", "issues": issues, "ufun_buyer": buyer, "ufun_seller": seller}


def apartment_rental():
    issues = [
        make_issue(name="rent",       values=10),  # 0=low, 9=high
        make_issue(name="lease",      values=5),   # 0=6mo, 4=24mo
        make_issue(name="renovation", values=4),   # 0=none, 3=full
    ]
    # Tenant: low rent, short lease, high renovation
    buyer = LUFun(
        values={
            "rent":       lambda v: 1.0 - v / 9.0,
            "lease":      lambda v: 1.0 - v / 4.0,
            "renovation": lambda v: v / 3.0,
        },
        weights={"rent": 0.6, "lease": 0.2, "renovation": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    # Landlord: high rent, long lease, no renovation
    seller = LUFun(
        values={
            "rent":       lambda v: v / 9.0,
            "lease":      lambda v: v / 4.0,
            "renovation": lambda v: 1.0 - v / 3.0,
        },
        weights={"rent": 0.6, "lease": 0.2, "renovation": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    return {"name": "Apartment Rental", "issues": issues, "ufun_buyer": buyer, "ufun_seller": seller}


def freelance_contract():
    issues = [
        make_issue(name="hourly_rate", values=10),  # 0=low, 9=high
        make_issue(name="deadline",    values=6),   # 0=1wk, 5=6wks
        make_issue(name="revisions",   values=4),   # 0=1, 3=4 rounds
    ]
    # Client: low rate, tight deadline, many revisions
    buyer = LUFun(
        values={
            "hourly_rate": lambda v: 1.0 - v / 9.0,
            "deadline":    lambda v: 1.0 - v / 5.0,
            "revisions":   lambda v: v / 3.0,
        },
        weights={"hourly_rate": 0.5, "deadline": 0.3, "revisions": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    # Freelancer: high rate, long deadline, few revisions
    seller = LUFun(
        values={
            "hourly_rate": lambda v: v / 9.0,
            "deadline":    lambda v: v / 5.0,
            "revisions":   lambda v: 1.0 - v / 3.0,
        },
        weights={"hourly_rate": 0.5, "deadline": 0.3, "revisions": 0.2},
        issues=issues, reserved_value=0.0,
    ).scale_max(1.0)
    return {"name": "Freelance Contract", "issues": issues, "ufun_buyer": buyer, "ufun_seller": seller}