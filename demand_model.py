from datetime import date, datetime, timedelta

import numpy as np

BASE_ORDERS_PER_DAY = 28.0
TREND_GROWTH = 0.45         
DAY_NOISE_SIGMA = 0.10      
BLACK_FRIDAY_BOOST = 2.0


WEEKDAY_FACTORS = [0.85, 0.85, 0.90, 0.95, 1.15, 1.35, 0.95]

MONTH_FACTORS = {
    1: 0.85, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.00,
    7: 0.90, 8: 0.90, 9: 1.00, 10: 1.05, 11: 1.25, 12: 1.45,
}

OPEN_HOURS = list(range(9, 21))
HOUR_WEIGHTS = np.array([0.5, 0.8, 1.0, 1.1, 1.0, 1.0, 1.1, 1.3, 1.5, 1.4, 1.0, 0.6])
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()

CATEGORY_MONTH_FACTORS = {
    "Toys": {11: 1.5, 12: 2.5},
    "Electronics": {11: 1.6, 12: 1.3},
    "Cosmetics": {3: 1.5, 12: 1.3},
    "Sports Equipment": {1: 1.6, 5: 1.3, 6: 1.3},
    "Clothing": {3: 1.2, 4: 1.2, 9: 1.2, 10: 1.2},
}


def black_friday(year):
    first_day = date(year, 11, 1)
    first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
    return first_friday + timedelta(days=21)


def daily_intensity(days):
    n = len(days)
    intensity = np.empty(n)
    for i, day in enumerate(days):
        trend = 1.0 + TREND_GROWTH * (i / max(n - 1, 1))
        value = (BASE_ORDERS_PER_DAY * trend
                 * MONTH_FACTORS[day.month]
                 * WEEKDAY_FACTORS[day.weekday()])
        if day == black_friday(day.year):
            value *= BLACK_FRIDAY_BOOST
        intensity[i] = value
    return intensity


def draw_order_counts(rng, days):
    noise = rng.lognormal(mean=0.0, sigma=DAY_NOISE_SIGMA, size=len(days))
    return rng.poisson(daily_intensity(days) * noise)


def random_order_time(rng, day):
    hour = int(rng.choice(OPEN_HOURS, p=HOUR_WEIGHTS))
    return datetime(day.year, day.month, day.day, hour,
                    int(rng.integers(0, 60)), int(rng.integers(0, 60)))


def category_factor(category_name, month):
    return CATEGORY_MONTH_FACTORS.get(category_name, {}).get(month, 1.0)